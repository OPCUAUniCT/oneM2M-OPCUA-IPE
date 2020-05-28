from datetime import  timedelta
from enum import Enum
import logging
from opcua.common.callback import CallbackType, ServerItemCallback, CallbackDispatcher
from threading import Lock
import time

from opcua import ua
from opcua.common import utils
from opcua.common.node import Node
from opcua.server.address_space import AddressSpace, AttributeService, MethodService, NodeManagementService, ViewService
from opcua.server.history import HistoryManager
from opcua.server.internal_server import InternalSession, InternalServer
from opcua.server.subscription_service import SubscriptionService
from opcua.server.user_manager import UserManager

from src.StoppableThread import StoppableThread 


class SessionState(Enum):
    Created = 0
    Activated = 1
    Closed = 2
    
class CustomInternalServer(InternalServer):

    def __init__(self, interworking_manager, shelffile=None, parent=None, session_cls=None):
        self.logger = logging.getLogger(__name__)
        
        self._parent = parent
        self.server_callback_dispatcher = CallbackDispatcher()

        self.endpoints = []
        self._channel_id_counter = 5
        self.disabled_clock = False  # for debugging we may want to disable clock that writes too much in log
        self._local_discovery_service = None # lazy-loading

        self.aspace = AddressSpace()
        self.attribute_service = AttributeService(self.aspace)
        self.view_service = ViewService(self.aspace)
        self.method_service = MethodService(self.aspace)
        self.node_mgt_service = NodeManagementService(self.aspace)

        self.load_standard_address_space(shelffile)

        self.loop = None
        self.asyncio_transports = []
        self.subscription_service = SubscriptionService(self.aspace)

        self.history_manager = HistoryManager(self)

        # create a session to use on server side
        self.session_cls = session_cls or CustomInternalSession
        self.interworking_manager = interworking_manager

        self.isession = self.session_cls(self, self.aspace, \
          self.subscription_service, "Internal",self.interworking_manager.data_cache_state, user=UserManager.User.Admin)
        
        self.current_time_node = Node(self.isession, ua.NodeId(ua.ObjectIds.Server_ServerStatus_CurrentTime))
        self._address_space_fixes()
        self.setup_nodes()
    
    def user_manager(self):
        return InternalServer.user_manager(self)

    def thread_loop(self):
        return InternalServer.thread_loop(self)

    def local_discovery_service(self):
        return InternalServer.local_discovery_service(self)

    def setup_nodes(self):
        InternalServer.setup_nodes(self)

    def load_standard_address_space(self, shelffile=None):
        InternalServer.load_standard_address_space(self, shelffile=shelffile)

    def _address_space_fixes(self):
        InternalServer._address_space_fixes(self)


    def load_address_space(self, path):
        InternalServer.load_address_space(self, path)

    def dump_address_space(self, path):
        InternalServer.dump_address_space(self, path)

    def start(self):
        InternalServer.start(self)

    def stop(self):
        InternalServer.stop(self)

    def is_running(self):
        return InternalServer.is_running(self)

    def _set_current_time(self):
        InternalServer._set_current_time(self)
    
    def get_new_channel_id(self):
        return InternalServer.get_new_channel_id(self)

    def add_endpoint(self, endpoint):
        InternalServer.add_endpoint(self, endpoint)

    def get_endpoints(self, params=None, sockname=None):
        return InternalServer.get_endpoints(self, params=params, sockname=sockname)

    def create_session(self, name, user=UserManager.User.Anonymous, external=False):
        return self.session_cls(self, self.aspace, self.subscription_service, name, self.interworking_manager.data_cache_state, user=user, external=external)

    def enable_history_data_change(self, node, period=timedelta(days=7), count=0):
        InternalServer.enable_history_data_change(self, node, period=period, count=count)

    def disable_history_data_change(self, node):
        InternalServer.disable_history_data_change(self, node)

    def enable_history_event(self, source, period=timedelta(days=7), count=0):
        InternalServer.enable_history_event(self, source, period=period, count=count)

    def disable_history_event(self, source):
        InternalServer.disable_history_event(self, source)

    def subscribe_server_callback(self, event, handle):
        InternalServer.subscribe_server_callback(self, event, handle)

    def unsubscribe_server_callback(self, event, handle):
        InternalServer.unsubscribe_server_callback(self, event, handle)
    
    def set_attribute_value(self, nodeid, datavalue, attr=ua.AttributeIds.Value):
        InternalServer.set_attribute_value(self, nodeid, datavalue, attr=attr)
    
#Custom class of InternalSession used to enable OPC UA Server to interworking features: 
#__ini__, create_monitored_items(), delete_monitored_items(), read(), write(), get_data_request(),write_data_request(),read_for_data_cache(), read_periodically()   
class CustomInternalSession(InternalSession):
    _counter = 10
    _auth_counter = 1000

    def __init__(self, internal_server, aspace, submgr, name,data_cache_state, user=UserManager.User.Anonymous, external=False ):
        self.logger = logging.getLogger(__name__)
        self.iserver = internal_server
        self.external = external  
        self.aspace = aspace
        self.subscription_service = submgr
        self.name = name
        #manage datacache
        self.data_cache_state = data_cache_state
        self.initialization_cache = False
        self.user = user

        self.nonce = None
        self.state = SessionState.Created
        self.session_id = ua.NodeId(self._counter)
        InternalSession._counter += 1
        self.authentication_token = ua.NodeId(self._auth_counter)
        InternalSession._auth_counter += 1
        self.subscriptions = []
        self.logger.info("Created internal session %s", self.name)
        self._lock = Lock()
        self.m_item_id_thread_dict = {}

    @property
    def user_manager(self):
        return self.iserver.user_manager

    def __str__(self):
        return "InternalSession(name:{0}, user:{1}, id:{2}, auth_token:{3})".format(
            self.name, self.user, self.session_id, self.authentication_token)

    def get_endpoints(self, params=None, sockname=None):
        return self.iserver.get_endpoints(params, sockname)

    def create_session(self, params, sockname=None):
        self.logger.info("Create session request")

        result = ua.CreateSessionResult()
        result.SessionId = self.session_id
        result.AuthenticationToken = self.authentication_token
        result.RevisedSessionTimeout = params.RequestedSessionTimeout
        result.MaxRequestMessageSize = 65536
        self.nonce = utils.create_nonce(32)
        result.ServerNonce = self.nonce
        result.ServerEndpoints = self.get_endpoints(sockname=sockname)

        return result

    def close_session(self, delete_subs=True):
        self.logger.info("close session %s with subscriptions %s", self, self.subscriptions)
        self.state = SessionState.Closed
        self.delete_subscriptions(self.subscriptions[:])

    def activate_session(self, params):
        self.logger.info("activate session")
        result = ua.ActivateSessionResult()
        if self.state != SessionState.Created:
            raise utils.ServiceError(ua.StatusCodes.BadSessionIdInvalid)
        self.nonce = utils.create_nonce(32)
        result.ServerNonce = self.nonce
        for _ in params.ClientSoftwareCertificates:
            result.Results.append(ua.StatusCode())
        self.state = SessionState.Activated
        id_token = params.UserIdentityToken
        if isinstance(id_token, ua.UserNameIdentityToken):
            if self.user_manager.check_user_token(self, id_token) == False:
                raise utils.ServiceError(ua.StatusCodes.BadUserAccessDenied)
        self.logger.info("Activated internal session %s for user %s", self.name, self.user)
        return result

    

    def history_read(self, params):
        return self.iserver.history_manager.read_history(params)

    def browse(self, params):
        return self.iserver.view_service.browse(params)

    def translate_browsepaths_to_nodeids(self, params):
        return self.iserver.view_service.translate_browsepaths_to_nodeids(params)

    def add_nodes(self, params):
        return self.iserver.node_mgt_service.add_nodes(params, self.user)

    def delete_nodes(self, params):
        return self.iserver.node_mgt_service.delete_nodes(params, self.user)

    def add_references(self, params):
        return self.iserver.node_mgt_service.add_references(params, self.user)

    def delete_references(self, params):
        return self.iserver.node_mgt_service.delete_references(params, self.user)

    def add_method_callback(self, methodid, callback):
        return self.aspace.add_method_callback(methodid, callback)

    def call(self, params):
        return self.iserver.method_service.call(params)

    def create_subscription(self, params, callback, ready_callback=None):
        result = self.subscription_service.create_subscription(params, callback)
        with self._lock:
            self.subscriptions.append(result.SubscriptionId)
        return result

    def modify_subscription(self, params, callback):
        return self.subscription_service.modify_subscription(params, callback)

    def create_monitored_items(self, params):
        subscription_result = self.subscription_service.create_monitored_items(params)
        self.iserver.server_callback_dispatcher.dispatch(
            CallbackType.ItemSubscriptionCreated, ServerItemCallback(params, subscription_result))
        if params.ItemsToCreate[0].ItemToMonitor.NodeId.NamespaceIndex == 2 and subscription_result[0].StatusCode.is_good():
            node_to_read = params.ItemsToCreate[0].ItemToMonitor.NodeId
            frequency = subscription_result[0].RevisedSamplingInterval
            monitored_ited_id = subscription_result[0].MonitoredItemId
            monitor_thread = StoppableThread(target=self.read_periodically,args=[node_to_read, frequency])
            self.m_item_id_thread_dict[monitored_ited_id] = monitor_thread
            monitor_thread.start()
        return subscription_result

    def modify_monitored_items(self, params):
        subscription_result = self.subscription_service.modify_monitored_items(params)
        self.iserver.server_callback_dispatcher.dispatch(
            CallbackType.ItemSubscriptionModified, ServerItemCallback(params, subscription_result))
        return subscription_result

    def republish(self, params):
        return self.subscription_service.republish(params)

    def delete_subscriptions(self, ids):
        for i in ids:
            with self._lock:
                if i in self.subscriptions:
                    self.subscriptions.remove(i)
        return self.subscription_service.delete_subscriptions(ids)

    def delete_monitored_items(self, params):
        subscription_result = self.subscription_service.delete_monitored_items(params)
        self.iserver.server_callback_dispatcher.dispatch(
            CallbackType.ItemSubscriptionDeleted, ServerItemCallback(params, subscription_result))
        self.m_item_id_thread_dict.get(params.MonitoredItemIds[0]).stop()
        
        return subscription_result

    def publish(self, acks=None):
        if acks is None:
            acks = []
        return self.subscription_service.publish(acks)
    
    def read(self, params):
        with self.aspace._lock:
            if params.NodesToRead[0].NodeId.NamespaceIndex == 2:
                if self.data_cache_state:  #or params.MaxAge == 0 or self.data_cache_state
                    logging.debug("--- Reading from DataCache ---")
                    results = self.iserver.attribute_service.read(params)
                    return results
                else:
                    logging.debug("--- Direct Access Read ---")
                    self.get_data_request(params.NodesToRead[0].NodeId)
            results = self.iserver.attribute_service.read(params)
            return results
        
    #custom read method
    def get_data_request(self, node_to_read):
        old_value = self.iserver.aspace.get_attribute_value(node_to_read, ua.AttributeIds.Value).Value.Value
        self.iserver.interworking_manager.translate_read_request(node_to_read, old_value)
        
    def write(self, params):
        with self.aspace._lock:
            if params.NodesToWrite[0].NodeId.NamespaceIndex == 2 :
                if self.data_cache_state:
                    logging.debug("--- DataCache Write ---")

                    if self.initialization_cache:
                        self.write_data_request(params.NodesToWrite[0].NodeId, 
                                            params.NodesToWrite[0].Value.Value._value)
                        return self.iserver.attribute_service.write(params, self.user)
                    
                    uncertain_status = ua.StatusCode(ua.StatusCodes.Uncertain)
                    uncertain_response = self.iserver.attribute_service.write(params, self.user)
                    uncertain_response[0] = uncertain_status
                    #need to implement ack from onem2m side
                    self.write_data_request(params.NodesToWrite[0].NodeId, 
                                            params.NodesToWrite[0].Value.Value._value)
                    return uncertain_response

                else:
                    logging.debug("--- Direct Access Write ---")
                    self.write_data_request(params.NodesToWrite[0].NodeId, 
                                            params.NodesToWrite[0].Value.Value._value)
                    return self.iserver.attribute_service.write(params, self.user)
                
                
                
            return self.iserver.attribute_service.write(params, self.user)
   
    #custom write method
    def write_data_request(self, node_to_write, val):
        self.iserver.interworking_manager.translate_write_request(node_to_write, val)
        
        
    def read_periodically(self,node_to_read, frequency):
        self.get_data_request(node_to_read)
        time.sleep(frequency/1000)
        print("thread  "+ str(frequency))
        
    def read_for_data_cache(self, node_ids):
        with self.aspace._lock:
            for mapped_nodeid in node_ids:
                print("--- Update event ---")
                self.get_data_request(mapped_nodeid)
        