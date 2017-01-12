OPC UA XML Export client
=========================

This client exports all nodes from a running OPC UA server into a node XML file

Dependencies
------------
* Python3



Install
-------
```bash
pip3 install freeopcua
```


Run
---
Export nodes from server `opc.tcp://localhost:16664` into XML file `export.xml`
```
python3 client.py opc.tcp://localhost:16664 export.xml
```
