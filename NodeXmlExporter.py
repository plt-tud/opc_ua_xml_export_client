import argparse
import logging
import sys
import asyncio

from asyncua.crypto import uacrypto
from asyncua.client import Client

from XmlExporter import XmlExporter


class NodeXMLExporter:
    def __init__(self):
        self.nodes = []
        self.namespaces = {}
        self.visited = []
        self.client = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    async def iterater_over_child_nodes(self, node):
        self.nodes.append(node)
        self.logger.debug("Add %s" % node)
        # iterate over all referenced nodes (31), only hierarchical references (33)
        children = await node.get_children(refs=33)
        for child in children:
            if child not in self.nodes:
                await self.iterater_over_child_nodes(child)

    async def export_xml(self, namespaces=None, output_file="export.Nodeset2.xml"):
        if namespaces:
            self.logger.info("Export only NS %s" % namespaces)
            nodes = [node for node in  self.nodes if node.nodeid.NamespaceIndex in namespaces]
        else:
            nodes = self.nodes
        
        self.logger.info("Export nodes to %s" % output_file)
        exp = XmlExporter(self.client)
        await exp.build_etree(nodes)
        await exp.write_xml(output_file)
        self.logger.info("Export finished")

    async def import_nodes(self, server_url):
        from   asyncua.crypto import security_policies
        import types
        from  asyncua.ua.uaprotocol_hand import CryptographyNone
        
        self.client = Client(url=server_url)
        
         # Fix symmetric_key_size (not 0) of securityPolicy
        sec_policy = security_policies.SecurityPolicy()
        sec_policy.symmetric_key_size = 8
        self.client.security_policy = sec_policy
        # Fix signature method of CryptographyNone
        def signature(self, data):
            return None
        fixed_signature = types.MethodType(signature, CryptographyNone)
        self.client.security_policy.asymmetric_cryptography.signature = fixed_signature
        
        try:
            await self.client.connect()
        except Exception as e:
            self.logger.error("No connection established", e)
            self.logger.error(e)
            self.logger.error("Exiting ...")
            sys.exit()
        self.logger.info("Client connected to %s" % server_url)
    
        nsArray = await self.client.get_namespace_array()
        for ns in nsArray:
            ix = await self.client.get_namespace_index(ns)
            self.namespaces[ix] = ns
        root = self.client.get_root_node()
        self.logger.info("Starting to collect nodes. This may take some time ...")
        await self.iterater_over_child_nodes(root)
        self.logger.info("All nodes collected")

    def statistics(self):
        types = {}
        for node in self.nodes:
            try:
                node_class = str(node.get_node_class())
                ns = node.nodeid.NamespaceIndex
                if ns not in types:
                    types[ns] = {}
                if node_class not in types[ns]:
                    types[ns][node_class] = 1
                else:
                    types[ns][node_class] += 1
            except Exception as e:
                self.logger.info("some error with %s: %s" % (node,e))

        for ns in types:
            self.logger.info("NS%d (%s)" % (ns, self.namespaces[ns]))
            for type in types[ns]:
                self.logger.info("\t%s:\t%d" % (type, types[ns][type]))
        self.logger.info("\tTOTAL in namespace: %d" % len(self.nodes))


async def main():   

    parser = argparse.ArgumentParser(
        description="Export Node XML from OPC UA server")
    
    parser.add_argument('-s', '--serverUrl',
                        metavar='<serverUrl>',
                        dest="serverUrl",
                        help='Complete URL of the OPC UA server',
                        nargs='?',
                        default="opc.tcp://localhost:4840",
                        type=str)
    parser.add_argument('-n', '--namespace',
                        metavar='<namespace>',
                        dest="namespaces",
                        action="append",
                        type=int,
                        help='Export only the given namespace indices. Multiple NS indizes can be specified. If not specified, export all nodes.')
    parser.add_argument('-o', '--outputFile',
                        metavar='<outputFile>',
                        dest="outputFile",
                        help='Save exported nodes in specified XML file',
                        nargs='?',
                        default="export.Nodeset2.xml",
                        type=str)     
    args = parser.parse_args()

    exporter = NodeXMLExporter()
    await exporter.import_nodes(server_url=args.serverUrl)
    # exporter.statistics()
    await exporter.export_xml(args.namespaces, args.outputFile)

    await exporter.client.disconnect()
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)
    asyncio.run(main())