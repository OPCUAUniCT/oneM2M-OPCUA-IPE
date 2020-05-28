import sys
sys.path.insert(0, "..")
import json
from openmtc_onem2m.model import CSEBase, AE, Container, ContentInstance
from openmtc_onem2m.transport import OneM2MRequest
import os.path
from threading import Thread

import opcua

from src.IpeAe import  IpeAe
from src.NodeBuilder import NodeBuilder
from src.CustomSession import CustomInternalServer



class InterworkingManager(Thread):

    
    def __init__(self, xae, data_cache_state=None):
        self.xae = xae
        self.aeNodes = []
        self.cseBaseNodes= []
        self.containerNodes = []
        self.nodeid_uri_dict = {}
        self.nodeid_attr_dict = {}
        self.all_nodeid_mapped = []
        self.opc_openmtc_attrname_dict = self.parse_json()
        self.node_builder = None
        self.server = None
        #data cache state
        if data_cache_state is not None:
            self.data_cache_state = data_cache_state
        else:
            self.data_cache_state = False
        
    def init_server(self):
        custom_iserver = CustomInternalServer(self)
        server = opcua.Server(iserver=custom_iserver)
        server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
        os.chdir("..")
        server.import_xml(os.path.abspath(os.curdir)+ '/nodeset/onem2m-opcua.xml')       # server.iserver.dump_address_space(os.path.dirname(__file__) + 'dump')

        self.server = server
    
    def map_discovered_resources_to_node(self):
        #need for startup
        if self.data_cache_state== True:
            self.server.iserver.isession.initialization_cache = True
        self.node_builder = NodeBuilder(self.xae.resourceDiscovered, self.server, self.xae)
        self.node_builder.node_builder()
        self.aeNodes = self.node_builder.aeNodes
        self.cseBaseNodes = self.node_builder.cseBaseNodes
        self.containerNodes = self.node_builder.containerNodes
        self.nodeid_uri_dict = self.node_builder.nodeid_uri_dict
        self.nodeid_attr_dict = self.node_builder.nodeid_attr_dict
        self.all_nodeid_mapped = self.node_builder.all_nodeid_builded
        self.server.iserver.isession.initialization_cache = False

    def translate_read_request(self,node_to_read, old_value):
            if self.nodeid_uri_dict.get(node_to_read, None) is not None:
                onem2m_request = OneM2MRequest("retrieve", to=self.nodeid_uri_dict.get(node_to_read))
                promise = self.xae.client.send_onem2m_request(onem2m_request)
                onem2m_response = promise.get()
                response = onem2m_response.content
                attr_to_read = self.opc_openmtc_attrname_dict[self.nodeid_attr_dict[node_to_read]]
                
                new_value =self.decode_response(attr_to_read, getattr(response,attr_to_read))
                print(" HTTP-Read_Value: "+ str(new_value))
                if old_value != new_value:
                    #this type of write not support uncertain response
                    self.server.iserver.isession.initialization_cache =True
                    self.server.get_node(node_to_read).set_value(new_value)
                    self.server.iserver.isession.initialization_cache =False

    def translate_write_request(self,node_to_write,value_to_write):
            if self.nodeid_uri_dict.get(node_to_write, None) is not None:
                #take uri from nodeid
                resource_uri = self.nodeid_uri_dict.get(node_to_write)
                #take resource from uri
                res = self.xae.uri_resource_dict.get(resource_uri)
                #take attr from node id
                attr_to_write = self.nodeid_attr_dict.get(node_to_write)
                
                update_instance = self.decode_request(res, 
                                                      attr_to_write, value_to_write)
                onem2m_request = OneM2MRequest("update",
                                                to=self.nodeid_uri_dict.get(node_to_write),
                                                pc=update_instance)
                self.xae.client.send_onem2m_request(onem2m_request)
                
        
       
    def parse_json(self):
        f = open('utils/opc_openmtc_name_map.json')
        data = json.load(f)
        f.close()
        return data
    
    def decode_response(self, attr_to_read, datavalue):
        if attr_to_read == "content":
            return datavalue.decode("utf-8")
        if attr_to_read == "cseType":
            return datavalue-1
        return datavalue
    
    def decode_request(self, resource,attr_to_write , value_to_write):
        if isinstance(resource, CSEBase):
            cse = CSEBase()
            setattr(cse, attr_to_write, value_to_write)
            return cse
        elif isinstance(resource, AE):
            ae = AE()
            setattr(ae, attr_to_write, value_to_write)
            return ae
        elif isinstance(resource, Container):
            cnt = Container()
            setattr(cnt, attr_to_write, value_to_write)
            return cnt
        elif isinstance(resource, ContentInstance):
            cin = ContentInstance()
            setattr(cin, attr_to_write, value_to_write)
            return cin
        return resource
    
    
    #Observer set
    def update_cin(self,res):
        print("--- Update Received from AE ---")
        self.node_builder.add_new_node(res)
        self.refresh_dict()
        
    def update_nodes(self):
        print("--- Update resources value from AE ---")
        self.refresh_dict()
        self.server.iserver.isession.read_for_data_cache(self.all_nodeid_mapped)
        
    def refresh_dict(self):
            self.aeNodes = self.node_builder.aeNodes
            self.cseBaseNodes = self.node_builder.cseBaseNodes
            self.containerNodes = self.node_builder.containerNodes
            self.nodeid_uri_dict = self.node_builder.nodeid_uri_dict
            self.nodeid_attr_dict = self.node_builder.nodeid_attr_dict
            self.all_nodeid_mapped = self.node_builder.all_nodeid_builded


    
    
    
if __name__ == "__main__":    
   
    ipe = IpeAe("ipe_ae", ['http://0.0.0.0:21346'])
    ipe.start_activity()
    ipe.retrieve_request()
    
    in_manager = InterworkingManager(ipe,data_cache_state=True)
    print("DATA CACHE STATUS: %s ", in_manager.data_cache_state)
    ipe.add(in_manager)
    in_manager.init_server()
    in_manager.map_discovered_resources_to_node()
    in_manager.server.start()

#generate event
# curl -X POST {PATH} -H {HEADER} -d {DATA.json}
# curl -X POST localhost:8000/onem2m/light_ae1/light/ -H 'Content-Type: application/vnd.onem2m-res+json' -d '{"m2m:cin": {"con": "eyAic3dpdGNoX3N0YXRlIjogIm9uIiB9", "cnf":"application/json:1"}}'
