OPC UA XML Export client
=========================

This client exports all nodes from a running OPC UA server into a nodeset XML file.
Forked from https://github.com/plt-tud/opc_ua_xml_export_client to support the newer _asyncua_ library.

Dependencies
------------
* Python3 (requires  Python 3.7+)
* opcua-asyncio (https://github.com/FreeOpcUa/opcua-asyncio)


Install
-------
```bash
pip3 install asyncua
```


Run
---
Export nodes from server `opc.tcp://localhost:16664` into XML file `export.xml`

```shell
python3 NodeXmlExporter.py --serverUrl opc.tcp://localhost:16664  --outputFile export.xml
```

Export only namespace 2
```shell
python3 NodeXmlExporter.py -s opc.tcp://localhost:16664 -n 2 -o export-ns2.xml
```
