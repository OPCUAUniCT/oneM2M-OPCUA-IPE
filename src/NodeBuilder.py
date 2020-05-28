from openmtc_onem2m.model import CSEBase, AE, Container, ContentInstance

from opcua import ua

#This class build all resource tree starting from a cseBase, single mapped resource not yet implementend, e.g. aeNode without csebase, container without ae
class NodeBuilder():
     
    def __init__(self, resourceDiscovered, server, xae):
        self.resourceDiscovered = resourceDiscovered 
        self.server = server 
        self.aeNodes = []
        self.cseBaseNodes= []
        self.containerNodes = []
        self.nodeid_uri_dict = {}
        self.nodeid_attr_dict = {}
        self.all_nodeid_builded = []
        self.xae = xae
    
    
    
    
    def node_builder(self):
        for resource in self.resourceDiscovered:
            if isinstance(resource, CSEBase):
                cseNode = self.cse_node_builder(resource)
            elif isinstance(resource, AE):
                self.aeNodes.append((self.ae_node_builder(cseNode, resource)))
            elif isinstance(resource, Container):
                self.containerNodes.append(self.container_node_builder(self.aeNodes,self.containerNodes, resource))
            elif isinstance(resource, ContentInstance):
                self.content_instance_node_builder(self.containerNodes,resource)
                
        

                
        
    def resource_node_builder(self, myobj,resource):
        listChildren = myobj.get_children()
        for child in listChildren:           
            if child.get_browse_name().to_string() == "2:resourceName":
                child.set_value(resource.resourceName)
            elif child.get_browse_name().to_string() == "2:resourceType":
                child.set_value(resource.resourceType)
            elif child.get_browse_name().to_string() == "2:resourceID":
                child.set_value(resource.resourceID)
            elif child.get_browse_name().to_string() == "2:parentID":
                child.set_value(resource.parentID)
            elif child.get_browse_name().to_string() == "2:creationTime":
                child.set_value(resource.creationTime)
            elif child.get_browse_name().to_string() == "2:lastModifiedTime":
                child.set_value(resource.lastModifiedTime)
          
    def cse_node_builder(self, resource):
        idx = self.server.get_namespace_index("http://dieei.unict.it/oneM2M-OPCUA/")
        cseBaseObjectType = ua.NodeId.from_string('ns=%d;i=1003' % idx)
        myobj = self.server.nodes.objects.add_object(idx, resource.resourceName, cseBaseObjectType)            
        listChildren = myobj.get_children()
        for child in listChildren:
            self.populate_dict_name(child)                    
            if child.get_browse_name().to_string() == "2:CSE-ID":
                child.set_value(resource.CSE_ID)
            elif child.get_browse_name().to_string() == "2:cseType":
                child.set_value(resource.cseType-1)
        self.resource_node_builder(myobj, resource)
        if resource.resourceID is not None:
            self.populate_dict(myobj,resource)
        
        return myobj
    
    def ae_node_builder(self,myobj, resource):
        idx = self.server.get_namespace_index("http://dieei.unict.it/oneM2M-OPCUA/")
        aeObjectType = ua.NodeId.from_string('ns=%d;i=1007' % idx)
        aeNode = myobj.add_object(idx,resource.resourceName, aeObjectType)
        listChildren = aeNode.get_children()
        for child in listChildren:
            self.populate_dict_name(child)                    
            if child.get_browse_name().to_string() == ("%d:AE-ID" % idx):
                child.set_value(resource.AE_ID)
            elif child.get_browse_name().to_string() == ("%d:App-ID" % idx):
                child.set_value(resource.App_ID)                            
            elif child.get_browse_name().to_string() == ("%d:appName" % idx):
                child.set_value(resource.appName)                            
        self.resource_node_builder(aeNode, resource)
        self.populate_dict(aeNode, resource)
        return aeNode
    
    def container_node_builder(self,aeNodesList, containerNodesList, resource):
        idx = self.server.get_namespace_index("http://dieei.unict.it/oneM2M-OPCUA/")
        containerObjectType = ua.NodeId.from_string('ns=%d;i=1005' % idx)
        listChildren = []
        for aeNode in aeNodesList:
            if resource.parentID == aeNode.get_child("%d:resourceID" % idx).get_value():
                containerNodeAdded = aeNode.add_object(idx,resource.resourceName, containerObjectType)
                listChildren = containerNodeAdded.get_children()
        for containerNode in containerNodesList:
            if resource.parentID == containerNode.get_child("%d:resourceID" % idx).get_value():
                containerNodeAdded = containerNode.add_object(idx,resource.resourceName, containerObjectType)
                listChildren = containerNodeAdded.get_children()
        
        for child in listChildren:
            self.populate_dict_name(child)
            if child.get_browse_name().to_string() == ("%d:creationTime" % idx):
                child.set_value(resource.creationTime)
            elif child.get_browse_name().to_string() == ("%d:currentNrOfInstances" % idx):
                child.set_value(resource.currentNrOfInstances)
        self.resource_node_builder(containerNodeAdded, resource)
        self.populate_dict(containerNodeAdded, resource)

        return containerNodeAdded
                
    def content_instance_node_builder(self,containerNodesList, resource):
        idx = self.server.get_namespace_index("http://dieei.unict.it/oneM2M-OPCUA/")
        contentInstanceObjectType = ua.NodeId.from_string('ns=%d;i=1004' % idx)
        for containerNode in containerNodesList:
            if resource.parentID == containerNode.get_child("%d:resourceID" % idx).get_value():
                contentInstanceNode = containerNode.add_object(idx,resource.resourceName, contentInstanceObjectType)
                listChildren = contentInstanceNode.get_children()
                for child in listChildren:
                    self.populate_dict_name(child)                    
                    if child.get_browse_name().to_string() == ("%d:content" % idx):
                        child.set_value(resource.content.decode("utf-8"))
                    elif child.get_browse_name().to_string() == ("%d:contentSize" % idx):
                        child.set_value(resource.contentSize)
                self.resource_node_builder(contentInstanceNode, resource)
                self.populate_dict(contentInstanceNode, resource)
                
    def add_new_node(self,resource):
        if isinstance(resource, CSEBase):
            cseNode = self.cse_node_builder(resource)
        elif isinstance(resource, AE):
            self.aeNodes.append((self.ae_node_builder(cseNode, resource)))
        elif isinstance(resource, Container):
            self.containerNodes.append(self.container_node_builder(self.aeNodes,self.containerNodes, resource))
        elif isinstance(resource, ContentInstance):
            self.content_instance_node_builder(self.containerNodes,resource)
    
    def populate_dict_name(self, child):
        self.nodeid_attr_dict[child.nodeid] = (child.get_browse_name().to_string())[2:]
        self.all_nodeid_builded.append(child.nodeid)        
           
    def populate_dict(self, myobj, resource):
        listChildren = myobj.get_children()
        for child in listChildren:
            self.nodeid_uri_dict[child.nodeid] = self.xae.find_uri(resource)     
                
                
                