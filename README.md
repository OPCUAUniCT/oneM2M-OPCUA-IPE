# oneM2M-OPCUA-IPE
oneM2M-OPCUA-IPE is a simple implementation based on Phyton language to allow an easier integration with libraries and SDK used to realize some elements of the OPCUA-IPE architecture as shown in [1] and [2]. oneM2M-OPCUA-IPE realise an automatic exposition and management of oneM2M CSE resource tree towards OPCUA Server Address Space.


## Overview

  - OpenMTC SDK is a python-based reference implementation of the oneM2M standard. 
  - FreeOpcUaA is a python based open-source OPC UA communication stack. Furthermore, 
  - UaExpert OPC UA Client 

## Getting started
### Requirements
Installation of openMTC is required. See documentation [here](https://github.com/OpenMTC/OpenMTC).

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



## References
[#1 Enabling OPC UA and oneM2M Interworking](https://ieeexplore.ieee.org/document/9067161)

[#2 Towards Interoperability of oneM2M and OPC UA](https://www.scitepress.org/PublicationsDetail.aspx?ID=ppV040kquCA=&t=1)
