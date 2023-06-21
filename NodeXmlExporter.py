#!/bin/bash/python3
import asyncio
import argparse
import logging
import sys
import progressbar

from asyncua import Client

from XmlExporter import XmlExporter


class NodeXMLExporter:
    def __init__(self):
        self.nodes = []
        self.namespaces = {}
        self.visited = []
        self.client = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    async def start_node_browse(self, rootnode):
        bar = progressbar.ProgressBar(max_value=progressbar.UnknownLength)
        await self.iterater_over_child_nodes(rootnode, bar)

    async def iterater_over_child_nodes(self, node, browse_progressbar):
        self.nodes.append(node)
        self.logger.debug("Add %s" % node)
        browse_progressbar.update(len(self.nodes))
        # iterate over all referenced nodes (31), only hierarchical references (33)
        for child in await node.get_children(refs=33):
            if child not in self.nodes:
                await self.iterater_over_child_nodes(child, browse_progressbar)

    async def export_xml(self, namespaces=None, output_file="export.xml", export_values=False):
        if namespaces:
            self.logger.info("Export only NS %s" % namespaces)
            nodes = [node for node in self.nodes if node.nodeid.NamespaceIndex in namespaces]
        else:
            nodes = self.nodes

        self.logger.info("Export nodes to %s" % output_file)
        self.logger.info("Export node values: %s" % export_values)
        bar = progressbar.ProgressBar(max_value=len(nodes))
        exp = XmlExporter(self.client, export_values, bar.update)
        await exp.build_etree(nodes)
        await exp.write_xml(output_file)
        self.logger.info("Export finished")

    async def import_nodes(self, server_url="opc.tcp://localhost:16664", username="", password=""):
        from asyncua.crypto import security_policies
        import types
        from asyncua.ua.uaprotocol_hand import CryptographyNone

        self.client = Client(server_url)
        if username is not None:
            self.client.set_user(username)

        if password is not None:
            self.client.set_password(password)

        # Fix symmetric_key_size (not 0) of securityPolicy
        # sec_policy = security_policies.SecurityPolicy()
        # sec_policy.symmetric_key_size = 8
        # self.client.security_policy = sec_policy

        # Fix signature method of CryptographyNone
        # def signature(self, data):
        #    return None
        # fixed_signature = types.MethodType(signature, CryptographyNone)
        # self.client.security_policy.asymmetric_cryptography.signature = fixed_signature

        try:
            await self.client.connect()
        except Exception as e:
            self.logger.error("No connection established", e)
            self.logger.error(e)
            self.logger.error("Exiting ...")
            sys.exit()

        self.logger.info("Client connected to %s" % server_url)

        for ns in await self.client.get_namespace_array():
            self.namespaces[await self.client.get_namespace_index(ns)] = ns

        root = self.client.get_root_node()
        self.logger.info("Starting to collect nodes. This may take some time ...")
        await self.start_node_browse(root)
        self.logger.info("All nodes collected")

    async def statistics(self):
        self.logger.info("Calculating statistics")
        typecounts_per_namespace = {}
        nodecount = len(self.nodes)
        bar = progressbar.ProgressBar()
        for idx in bar(range(nodecount)):
            node = self.nodes[idx]
            try:
                node_class = str(await node.read_node_class())
                ns = node.nodeid.NamespaceIndex
                if ns not in typecounts_per_namespace:
                    typecounts_per_namespace[ns] = {}
                if node_class not in typecounts_per_namespace[ns]:
                    typecounts_per_namespace[ns][node_class] = 1
                else:
                    typecounts_per_namespace[ns][node_class] += 1
            except Exception as e:
                self.logger.error("some error with %s: %s" % (node, e))

        for ns in typecounts_per_namespace:
            self.logger.info("NS%d (%s)" % (ns, self.namespaces[ns]))
            for type_info in typecounts_per_namespace[ns]:
                self.logger.info("\t%s:\t%d" % (type_info, typecounts_per_namespace[ns][type_info]))
        self.logger.info("\tTOTAL in namespace: %d" % len(self.nodes))


async def main():
    parser = argparse.ArgumentParser(
        description="Export Node XML from OPC UA server")
    parser.add_argument('serverUrl', help='Complete URL of the OPC UA server', default="opc.tcp://localhost:16664")
    parser.add_argument('-n', '--namespace',
                        metavar='<namespace>',
                        dest="namespaces",
                        action="append",
                        type=int,
                        help='Export only the given namespace indexes. Multiple NS indexes can be specified. If not specified, export all nodes.')
    parser.add_argument('outputFile',  default="nodes_output.xml",
                        help='Save exported nodes in specified XML file')
    parser.add_argument('-u', '--username', default="", metavar='<username>', dest="username", help="Username to login on server")
    parser.add_argument('-p', '--password', default="", metavar='<password>', dest="password", help="Password to login on server")
    parser.add_argument('-v', '--values', default=False, metavar='<values>', dest="export_values", help="Export node values to nodeset")
    args = parser.parse_args()

    exporter = NodeXMLExporter()
    await exporter.import_nodes(server_url=args.serverUrl, username=args.username, password=args.password)
    await exporter.statistics()
    await exporter.export_xml(args.namespaces, args.outputFile, args.export_values)

    await exporter.client.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    asyncio.run(main())
