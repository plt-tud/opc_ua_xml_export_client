import sys

from opcua import Client

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


    for (index, ns) in types.items():
        count = 0
        print("Namespace %d (%s)" % (index, ns['url']))
        for (c,val) in ns['classes'].items():
            count += val
            print("\t%s:\t%d" % (c,val))
        print("\tTOTAL in namespace: %d" % count)
    print("TOTAL in server: %d" % len(nodes))
    client.disconnect()
