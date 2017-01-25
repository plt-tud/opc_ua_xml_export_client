OPC UA XML Export client
=========================

This client exports all nodes from a running OPC UA server into a node XML file

Dependencies
------------
* Python3
* freeopcua (https://github.com/FreeOpcUa/python-opcua)


Install
-------
```bash
pip3 install freeopcua
```


Run
---
Export nodes from server `opc.tcp://localhost:16664` into XML file `export.xml`
```
python3 NodeXmlExporter.py opc.tcp://localhost:16664 export.xml

# Export only namespace 2
python3 NodeXmlExporter.py opc.tcp://localhost:16664 --namespace 2 export-ns2.xml
```
