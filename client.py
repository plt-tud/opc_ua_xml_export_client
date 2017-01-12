#!/bin/bash/python3

import argparse
import logging
import sys

from opcua import Client

from XmlExporter import XmlExporter


class NodeXMLExporter:
    def __init__(self):
        self.nodes = []
        self.namespaces = {}
        self.visited = []
        self.client = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def iterater_over_child_nodes(self, node):
        self.nodes.append(node)
        self.logger.debug("Add %s" % node)
        # iterate over all referenced nodes (31), only hierarchical references (33)
        for child in node.get_children(refs=33):
            if child not in self.nodes:
                self.iterater_over_child_nodes(child)

    def export_xml(self, output_file="export.xml"):
        self.logger.info("Export nodes to %s" % output_file)
        exp = XmlExporter(self.client)
        exp.build_etree(self.nodes)
        exp.write_xml(output_file)
        self.logger.info("Export finished")

    def import_nodes(self, server_url="opc.tcp://localhost:16664"):
        self.client = Client(server_url)
        try:
            self.client.connect()
        except Exception:
            self.logger.error("No connection established. Exiting ...")
            sys.exit()

        self.logger.info("Client connected to %s" % server_url)

        for ns in self.client.get_namespace_array():
            self.namespaces[self.client.get_namespace_index(ns)] = ns

        root = self.client.get_root_node()
        self.iterater_over_child_nodes(root)

    def statistics(self):
        types = {}
        for node in self.nodes:
            node_class = str(node.get_node_class())
            ns = node.nodeid.NamespaceIndex
            if ns not in types:
                types[ns] = {}
            if node_class not in types[ns]:
                types[ns][node_class] = 1
            else:
                types[ns][node_class] += 1

        for ns in types:
            self.logger.info("NS%d (%s)" % (ns, self.namespaces[ns]))
            for type in types[ns]:
                self.logger.info("\t%s:\t%d" % (type, types[ns][type]))
        self.logger.info("\tTOTAL in namespace: %d" % len(self.nodes))


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)

    parser = argparse.ArgumentParser(
        description="Export Node XML from OPC UA server")
    parser.add_argument('serverUrl', help='Complete URL of the OPC UA server', default="opc.tcp://localhost:16664")
    parser.add_argument('-n', '--namespace',
                        metavar='<namespace>',
                        dest="namespaces",
                        action="append",
                        type=int,
                        help='Export only the given namespace index')
    parser.add_argument('outputFile',
                        help='Save exported nodes in specified XML file')
    args = parser.parse_args()

    exporter = NodeXMLExporter()
    exporter.import_nodes(server_url=args.serverUrl)
    exporter.statistics()
    exporter.export_xml(args.outputFile)

    exporter.client.disconnect()
