from opcua.common import xmlexporter

"""
Modified version of XmlExporter from FreeOPCUA

Add Try-Except
"""

class XmlExporter(xmlexporter.XmlExporter):

    def build_etree(self, node_list, uris=None):
        """
        Create an XML etree object from a list of nodes; custom namespace uris are optional
        Namespaces used by nodes are always exported for consistency.
        Args:
            node_list: list of Node objects for export
            uris: list of namespace uri strings

        Returns:
        """
        self.logger.info('Building XML etree')

        self._add_namespaces(node_list, uris)

        # add all nodes in the list to the XML etree
        for node in node_list:
            try:
                self.node_to_etree(node)
            except Exception as e:
                self.logger.warn("Error building etree for node %s: %s" % (node, e))

        # add aliases to the XML etree
        self._add_alias_els()
        
    def _get_ns_idxs_of_nodes(self, nodes):
        """
        get a list of all indexes used or references by nodes
        """
        idxs = []
        for node in nodes:
            node_idxs = [node.nodeid.NamespaceIndex]
            try:
                node_idxs.append(node.get_browse_name().NamespaceIndex)
            except Exception:
                pass
            try:
                node_idxs.extend(ref.NodeId.NamespaceIndex for ref in node.get_references())
            except Exception:
                pass
            node_idxs = list(set(node_idxs))  # remove duplicates
            for i in node_idxs:
                if i != 0 and i not in idxs:
                    idxs.append(i)
        return idxs