import sys

from opcua import Client
from xml.dom import minidom
import datetime

nodes = []
types = {}

def iterater_over_child_nodes(parent):
    for child in parent.get_children(refs=31):
        if child not in nodes:
            nodes.append(child)
            ns = child.nodeid.NamespaceIndex
            try:
                types[ns]['classes'][str(child.get_node_class())] += 1
            except KeyError:
                types[ns]['classes'][str(child.get_node_class())] =1
            iterater_over_child_nodes(child)

if __name__ == "__main__":

    client_url = "opc.tcp://localhost:16664"
    client = Client(client_url)
    
    namespace = 2

    try:
        client.connect()
    except Exception:
        print("No connection established. Exiting ...")
        sys.exit()

    print("Client connected to %s" % client_url)

    for ns in client.get_namespace_array():
        types[client.get_namespace_index(ns)] = {'url': ns, 'classes': {}}
    root = client.get_root_node()

    iterater_over_child_nodes(root)

    doc = minidom.Document()
    
    doc.appendChild(doc.createComment("Exported node xml from %s - ns: %d - %s" % (client_url, namespace, datetime.datetime.now())))
    xml_uanodeset = doc.createElement("UANodeSet")
    doc.appendChild(xml_uanodeset)

    xml_uanodeset.setAttributeNS("xsi", "xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    xml_uanodeset.setAttributeNS("xsd", "xmlns:xsd", "http://www.w3.org/2001/XMLSchema")
    xml_uanodeset.setAttributeNS("", "xmlns", "http://opcfoundation.org/UA/2011/03/UANodeSet.xsd")
    xml_uanodeset.setAttribute("LastModified", str(datetime.datetime.now()))
    
    
    xml_namespace_uris = xml_uanodeset.appendChild(doc.createElement("NamespaceUris"))
    for ns in client.get_namespace_array():
        xml_namespace_uris.appendChild(doc.createElement("Uri")).appendChild(doc.createTextNode(ns))
        

    for node in nodes:
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
            xml_ref.setAttribute("IsAbstract", str(node.is_abstract))
        except:
            pass
        try:
            # not tested (Variable)
            xml_ref.setAttribute("DataType", node.get_data_type.to_str())
        except:
            pass
        try:
            # not tested (Variable)
            xml_ref.setAttribute("ParentNodeId", node.get_parent.nodeid.to_str())
        except:
            pass


    print(doc.toprettyxml())

    for (index, ns) in types.items():
        count = 0
        print("Namespace %d (%s)" % (index, ns['url']))
        for (c,val) in ns['classes'].items():
            count += val
            print("\t%s:\t%d" % (c,val))
        print("\tTOTAL in namespace: %d" % count)
    print("TOTAL in server: %d" % len(nodes))

    client.disconnect()
