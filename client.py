import sys

from opcua import Client
from xml.dom import minidom
import argparse
import datetime

def iterater_over_child_nodes(parent, namespace, nodes, visited):
    # iterate over all referenced nodes (31)
    for child in parent.get_children(refs=31):
        if child not in visited:
            visited.append(child)
            ns = child.nodeid.NamespaceIndex
            if ns in namespace:
                nodes[ns].append(child)
            iterater_over_child_nodes(child, namespace, nodes, visited)


def create_node_xml(nodes, namespace, namespace_array, server_url, outputFile):
    doc = minidom.Document()

    doc.appendChild(doc.createComment("Exported node xml from %s - ns: %d - %s" % (server_url, namespace, datetime.datetime.now())))
    xml_uanodeset = doc.createElement("UANodeSet")
    doc.appendChild(xml_uanodeset)

    xml_uanodeset.setAttributeNS("xsi", "xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    xml_uanodeset.setAttributeNS("xsd", "xmlns:xsd", "http://www.w3.org/2001/XMLSchema")
    xml_uanodeset.setAttributeNS("", "xmlns", "http://opcfoundation.org/UA/2011/03/UANodeSet.xsd")
    xml_uanodeset.setAttribute("LastModified", str(datetime.datetime.now()))


    xml_namespace_uris = xml_uanodeset.appendChild(doc.createElement("NamespaceUris"))
    for ns in namespace_array:
        xml_namespace_uris.appendChild(doc.createElement("Uri")).appendChild(doc.createTextNode(ns))

    for node in nodes[namespace]:
        xml_node = xml_uanodeset.appendChild(doc.createElement("UA" + node.get_node_class()._name_))
        xml_node.setAttribute("NodeId", node.nodeid.to_string())
        xml_node.setAttribute("BrowseName", node.get_browse_name().to_string())
        xml_node.appendChild(doc.createElement("DisplayName"))\
            .appendChild(doc.createTextNode(node.get_display_name().to_string()))
        try:
            xml_node.appendChild(doc.createElement("Description"))\
                .appendChild(doc.createTextNode(node.get_description().to_string()))
        except:
            pass
        xml_references = xml_node.appendChild(doc.createElement("References"))
        for ref in node.get_references():
            xml_ref = xml_references.appendChild(doc.createElement("Reference"))
            xml_ref.setAttribute("ReferenceType", ref.ReferenceTypeId.to_string())
            xml_ref.setAttribute("IsForward", str(ref.IsForward))
            xml_ref.appendChild(doc.createTextNode(ref.NodeId.to_string()))
        try:
            if node.get_inverse_name().to_string():
                xml_ref.appendChild(doc.createElement("InverseName"))\
                    .appendChild(doc.createTextNode(node.get_inverse_name().to_string()))
        except:
            pass
        try:
            # not tested
            xml_ref.setAttribute("IsAbstract", str(node.IsAbstract))
        except:
            pass
        try:
            # not tested (Variable)
            xml_ref.setAttribute("DataType", node.get_data_type.to_str())
        except:
            pass
        try:
            # not tested (Variable)
            xml_ref.setAttribute("Symmetric", str(node.isSymmetric))
        except:
            pass
        try:
            # not tested (Variable)
            xml_ref.setAttribute("ParentNodeId", node.get_parent.nodeid.to_str())
        except:
            pass

    f = open(outputFile, 'w')
    doc.writexml(f, indent='\t', newl='\r\n',)
    f.close()


def export_node_xml(server_url="opc.tcp://localhost:16664", namespace=None):
    client = Client(server_url)
    try:
        client.connect()
    except Exception:
        print("No connection established. Exiting ...")
        sys.exit()

    print("Client connected to %s" % server_url)

    if not namespace:
        namespace = []
        for ns in client.get_namespace_array():
            namespace.append(client.get_namespace_index(ns))

    root = client.get_root_node()

    nodes = {}
    visited = []
    for ns in namespace:
        nodes[ns] = []

    namespace_array = client.get_namespace_array()
    iterater_over_child_nodes(root, namespace, nodes, visited)


    for ns in namespace:
        create_node_xml(nodes, ns, namespace_array, server_url, "ns%d.xml" % ns)

    types = {}
    for ns in namespace:
        types[ns]={}
        print("NS%d (%s)" % (ns, namespace_array[ns]))
        for node in nodes[ns]:
            try:
                types[ns][str(node.get_node_class())] += 1
            except KeyError:
                types[ns][str(node.get_node_class())] =1

        for typ in types[ns]:
            print("\t%s:\t%d" % (typ,types[ns][typ]))
        print("\tTOTAL in namespace: %d" % len(nodes[ns]))
    client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export Node XML from OPC UA server")
    parser.add_argument('serverUrl', help='Complete URL of the OPC UA server', default="opc.tcp://localhost:16664")
    parser.add_argument('-n','--namespace',
                        metavar='<namespace>',
                        dest="namespaces",
                        action="append",
                        type=int,
                        help='Export only the given namespace index')
    args = parser.parse_args()

    export_node_xml(server_url=args.serverUrl, namespace=args.namespaces)
