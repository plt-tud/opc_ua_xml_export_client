import traceback
import logging
import asyncio
import functools

from collections import OrderedDict
import xml.etree.ElementTree as Et
import base64
from dataclasses import fields, is_dataclass
from enum import Enum

from asyncua import ua
from asyncua.ua.uatypes import type_string_from_type
from asyncua.common import xmlexporter
from asyncua.ua import object_ids as o_ids
from asyncua.common.ua_utils import get_base_data_type

_logger = logging.getLogger(__name__)

"""
Modified version of XmlExporter from FreeOPCUA

Add Try-Except
"""

class XmlExporter(xmlexporter.XmlExporter):

    async def build_etree(self, node_list):
        """
        Create an XML etree object from a list of nodes; custom namespace uris are optional
        Namespaces used by nodes are always exported for consistency.
        Args:
            node_list: list of Node objects for export
            uris: list of namespace uri strings

        Returns:
        """
        self.logger.info('Building XML etree')

        await self._add_namespaces(node_list)

        # add all nodes in the list to the XML etree
        for node in node_list:
            try:
                await self.node_to_etree(node)
            except Exception as e:
                self.logger.warn("Error building etree for node %s: %s" % (node, e))
                traceback.print_exc()

        # add aliases to the XML etree
        self._add_alias_els()
        
    async def _get_ns_idxs_of_nodes(self, nodes):
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
                node_idxs.extend(ref.NodeId.NamespaceIndex for ref in await node.get_references())
            except Exception:
                pass
            node_idxs = list(set(node_idxs))  # remove duplicates
            for i in node_idxs:
                if i != 0 and i not in idxs:
                    idxs.append(i)
        return idxs
        
        
    async def add_variable_common(self, node, el):
        dtype = await node.read_data_type()
        if dtype.NamespaceIndex == 0 and dtype.Identifier in o_ids.ObjectIdNames:
            dtype_name = o_ids.ObjectIdNames[dtype.Identifier]
            self.aliases[dtype] = dtype_name
        else:
            dtype_name = self._node_to_string(dtype)
        rank = await node.read_value_rank()
        if rank != -1:
            el.attrib["ValueRank"] = str(int(rank))
        try:
            dim = await node.read_attribute(ua.AttributeIds.ArrayDimensions)
            if dim.Value.Value:
                el.attrib["ArrayDimensions"] = ",".join([str(i) for i in dim.Value.Value])
        except:
            pass
        el.attrib["DataType"] = dtype_name
        await self.value_to_etree(el, dtype_name, dtype, node)
       
    async def _add_node_common(self, nodetype, node):
        browsename = await node.read_browse_name()
        nodeid = node.nodeid
        parent = await node.get_parent()
        displayname = (await node.read_display_name()).Text
        desc = None
        try:
            desc = await node.read_description()
            if desc:
                desc = desc.Text
        except:
            pass
        node_el = Et.SubElement(self.etree.getroot(), nodetype)
        node_el.attrib["NodeId"] = self._node_to_string(nodeid)
        node_el.attrib["BrowseName"] = self._bname_to_string(browsename)
        if parent is not None:
            node_class = await node.read_node_class()
            if node_class in (ua.NodeClass.Object, ua.NodeClass.Variable, ua.NodeClass.Method):
                node_el.attrib["ParentNodeId"] = self._node_to_string(parent)
        self._add_sub_el(node_el, 'DisplayName', displayname)
        if desc not in (None, ""):
            self._add_sub_el(node_el, 'Description', desc)
        # FIXME: add WriteMask and UserWriteMask
        await self._add_ref_els(node_el, node)
        return node_el  
        
    async def _all_fields_to_etree(self, struct_el, val):
        for field in fields(val):
            # FIXME; what happend if we have a custom type which is not part of ObjectIds???
            _logger.info(f"field name = '{field.name}'")
            if field.name == "Encoding":
                continue
            type_name = type_string_from_type(field.type)
            await self.member_to_etree(struct_el, field.name, ua.NodeId(getattr(ua.ObjectIds, type_name)), getattr(val, field.name))       
   