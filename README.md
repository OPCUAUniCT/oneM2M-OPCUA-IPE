# oneM2M-OPCUA-IPE
The oneM2M-OPCUA-IPE is an implementation based on Phyton language to realize the full OPCUA-IPE architecture shown in the following Figure.
![Alt text](https://github.com/OPCUAUniCT/oneM2M-OPCUA-IPE/blob/master/docs/OPCUA-IPE%20architecture..PNG)

oneM2M-OPCUA-IPE realizes an interworking solution to make interoperable oneM2M and OPC UA. It is based on the ad-hoc definition of an oneM2M IPE, called OPCUA-IPE. The aim of this solution is the integration of oneM2M–based IoT devices with OPC UA–compliant industrial applications; this integration requires that information produced by oneM2M–based IoT devices must be published by an OPC UA Server allowing the OPC UA-based client applications the access to this information. For this reason, the design of the OPCUA-IPE is based on the assumption to use an OPC UA Server to expose the resources belonging to the oneM2M system towards the OPC UA domain. OPC UA Clients may connect to the OPC UA Server offered by the OPCUA-IPE through OPC UA interfaces; in this way, accessing the information maintained by the OPC UA Server, means accessing the information relevant to resources present in the oneM2M system.
As shown by Figure, two main entities are present in the OPCUA -IPE: an OPC UA Server and the Interworking Manager.
The OPC UA Server contains the AddressSpace maintaining OPC UA Nodes mapping the oneM2M resources to be exposed towards the OPC UA domain. A mapping strategy has been defined by the authors to represent each oneM2M resource by a suitable set of standard or ad-hoc defined OPC UA Nodes inside the AddressSpace. The mapping procedure allows to set the attributes of each OPC UA Node according to the current value of the relevant oneM2M resource, represented by the Node. Each time a change occurs in an exposed oneM2M resource (e.g. updating of values of attributes), the change is reflected into the relevant set of OPC UA Nodes representing the oneM2M resource. In the opposite direction, each change inside the AddressSpace must be reflected in the correspondent oneM2M resource; for example if an OPC UA Client updates the attribute values of one or more OPC UA Nodes representing oneM2M resources, the relevant changes must be updated in these resources. 
The Interworking Manager is the core of the OPCUA-IPE. It communicates with the OPC UA Server and it is made up by an AE able to communicate with the CSE exposing oneM2M resources. The Interworking Manager performs several activities. Among them, it is in charge of triggering changes in the state of the oneM2M resources exposed and reflecting each change occurred into OPC UA AddressSpace of the OPC UA Server. Similarly, changes in the AddressSpace must be applied on oneM2M side, as said before. Managing the dynamic adding/deletion of oneM2M exposed resources must be also realized by the Interworking Manager; this means that if a oneM2M resource is no more available, the relevant OPC UA Nodes must be removed from the AddressSpace. Moreover, if a novel oneM2M resource is available the relevant OPC UA Nodes may be added into the AddressSpace. 




## Overview

  - OpenMTC SDK is a python-based reference implementation of the oneM2M standard. 
  - FreeOpcUaA is a python based open-source OPC UA communication stack. Furthermore, 
  - UaExpert OPC UA Client 

## Getting started
### Requirements
Installation of openMTC is required. See documentation [here](https://github.com/OpenMTC/OpenMTC).

Installation of FreeOpcUa is required. See documentation [here](https://github.com/FreeOpcUa/python-opcua).
#### Example
1. Go to openMTC and run gateway:
```sh
$./run-gateway -vv
```
In this way a gateway instance is running in the background of the localhost.

2. Now gateway must be initialized. It can be initialized with script provided by oneM2M official site [here](https://www.onem2m.org/application-developer-guide/other-resources-curl-scripts) or script provided from this repository (mn-cse_init.sh)
```sh
$./mn-cse_init.sh  0.0.0.0 8000 onem2m
```
- 0.0.0.0 is localhost
- 8000 port
- onem2m is name of cseBase root of Resource Tree

3. Run InterworkingManager :
```sh
$python3 InterworkingManager.py 
```
4. Run UAExpert and add opc.tcp://127.0.0.1:4840/freeopcua/server/ as Endpoint URL




