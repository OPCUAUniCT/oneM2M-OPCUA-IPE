from openmtc_app.flask_runner import FlaskRunner
from openmtc_app.onem2m import XAE
from openmtc_onem2m import OneM2MRequest
from openmtc_onem2m.client.http import OneM2MHTTPClient
from openmtc_onem2m.model import AE, Container, ResourceTypeE
from random import random
from threading import Thread

from src.ResourceBuilder import ResourceBuilder


class IpeAe(XAE):
    #used to apply observer pattern
    interworking_manager = []
    #list of discovered resources
    resourceDiscovered = []
    #list of disceovered container
    container_discovered = []
    #dictionary uri as a key and resource as a value
    uri_resource_dict = {}
    #exposed resource ids
    exposed_ids = []
    
    client = OneM2MHTTPClient("http://0.0.0.0:8000",False)
    sub_state = False
    
    def __init__(self, name_ae, poas):
        XAE.__init__(self,name=name_ae,poas=poas)
        self.max_nr_of_instances=0
        self.resource_builder = ResourceBuilder()

    def _on_register(self):
        while True:
            
            if self.sub_state:
                self.subscribe_to_discovered_resource()
                break
            
            
        #Alternative of mn-init script, example at the bottom can be used 
        #self.example_init()
        #self.retrieve_request()
        self.logger.debug('registered')
        
    def start_activity(self):
        ipe_ae_thread = Thread(target= self.connect_to_local)
        ipe_ae_thread.start()
        
    def start_subscription(self):
        subscription_thread = Thread(target=self.subscribe_to_discovered_resource)
        subscription_thread.start()
        
    def subscribe_to_discovered_resource(self):
        print("SUBSCRIBE---------------------------------")

        self.sub_state = False
        print(self.resourceDiscovered)
        for response in self.resourceDiscovered:
            if response.resourceType == ResourceTypeE.AE or response.resourceType == ResourceTypeE.CSEBase:
                self.subscribe_to(self.find_uri(response))
                
            elif response.resourceType == ResourceTypeE.container:
                self.add_container_subscription(self.find_uri(response), self.handle_cin_creation)
               
            elif response.resourceType == ResourceTypeE.contentInstance:
                pass
            
    def retrieve_request(self):
        app = AE(appName = "appName")
        onem2m_request = OneM2MRequest("update", to="onem2m/ipe_ae", pc=app)
        promise = self.client.send_onem2m_request(onem2m_request)
        content_request = self.discover()
        for resource in content_request:
            onem2m_request = OneM2MRequest("retrieve", to=resource)
            promise = self.client.send_onem2m_request(onem2m_request)
            onem2m_response = promise.get()
            response = onem2m_response.content
            res_builded = self.resource_retrieved_builder(response)
            

            self.resourceDiscovered.append(res_builded)
            self.uri_resource_dict[resource] = res_builded
        # remove None values in list 
        self.resourceDiscovered = [i for i in self.resourceDiscovered if i]
        self.update_label_request()
        #self.start_subscription()
        self.sub_state = True
        
    def resource_retrieved_builder(self, response):
        #AE-Builder
        if response.resourceType == ResourceTypeE.AE and response.AE_ID != "ipe-ae":
            self.exposed_ids.append(response.resourceID)
            return self.resource_builder.ae_builder(response)
        #CSEBase-Builder
        elif response.resourceType == ResourceTypeE.CSEBase:
            self.exposed_ids.append(response.resourceID)
            return self.resource_builder.cse_base_builder(response)
        #Container-Builder
        elif response.resourceType == ResourceTypeE.container:
            cnt = self.resource_builder.container_builder(response)
            self.exposed_ids.append(response.resourceID)
            self.container_discovered.append(cnt)
            return cnt
        #ContentInstance-Builder
        elif response.resourceType == ResourceTypeE.contentInstance:
            self.exposed_ids.append(response.resourceID)
            return self.resource_builder.content_instance_builder(response)
    
    def find_uri(self,resource):
        return next((k for k, v in self.uri_resource_dict.items() if v is not None and  v.resourceID == resource.resourceID), None)
    
    def connect_to_local(self):
        print("IpeAe Starting....")
        runner = FlaskRunner(self)
        runner.run("http://localhost:8000")
        
    def update_label_request(self):
        labels_ = [{"Exposed-Resource-IDs": self.exposed_ids}]
        app = AE(labels = labels_)
        onem2m_request = OneM2MRequest("update", to="onem2m/ipe_ae", pc=app)
        promise = self.client.send_onem2m_request(onem2m_request)

    #override
    @staticmethod
    def _get_content_from_cin(cin):
        return cin
    
    def handle_cin_creation(self,cnt, cin):
        print('handle child creation under container: %s' % cnt)
        print('cin: %s' % cin)
        print('cin.resourceID: %s' % cin.resourceID)
        print('cin.content: %s' % cin.content)
        print('')
        cin_builded = self.resource_builder.content_instance_builder(cin)
        self.resourceDiscovered.append(cin_builded)
        uri = ("%s/%s" %(cnt, cin.resourceName))
        self.uri_resource_dict[uri] = cin_builded
        self.exposed_ids.append(cin.resourceID)
        self.update_label_request()  
        self.notify_cin_creation(cin)
    
    def subscribe_to(self, subscribe_to):
        self.add_subscription(
            subscribe_to,
            self.handle_subscribe_to)
    
    def handle_subscribe_to(self, sub, net, rep):
        print('handle_subscribe to...')
        print('subscription path: %s' % sub)
        print('notification event type: %s' % net)
        print('representation: %s' % rep)
        print('Calling refresh node')
        #AttributeError at first startup
        self.notify_event()
   
    #Subject set
    def add(self, interworking_manager):
        self.interworking_manager = interworking_manager
        
    def remove(self):
        self.interworking_manager = None
        
    def notify_cin_creation(self,res):
        print("-----AE_IPE notify InterworkingManager-----")
        self.interworking_manager.update_cin(res)
        
    def notify_event(self):
        try:
            self.interworking_manager.update_nodes()
        except AttributeError:
            pass
        
    
    
    
    
    
    
    
    
    
    
    
    
    #---------------EXAMPLE SETUP-------------------
    # sensors to create
    sensors = [
        'tmp'

    ]

    # available actuators
    actuators = [
        'a1'
    ]

    # settings for random sensor data generation
    threshold = 0.2
    temp_range = 25
    temp_offset = 10
    humi_range = 50
    humi_offset = 30
    
    
    def handle_command(self, container, value):
            print('handle_command...')
            print('container: %s' % container)
            print('value: %s' % value)
            print('value: %s' % value.resourceID)
            print('value: %s' % value.content)
            print('')
            
    def get_random_data(self):

        # at random time intervals
        if random() > self.threshold:

            # select a random sensor
            sensor = self.sensors[int(random() * len(self.sensors))]

            # set parameters depending on sensor type
            if sensor.startswith('Temp'):
                value_range = self.temp_range
                value_offset = self.temp_offset
            else:
                value_range = self.humi_range
                value_offset = self.humi_offset

            # generate random sensor data
            value = int(random() * value_range + value_offset)
            self.handle_sensor_data(sensor, value)

    def handle_sensor_data(self, sensor, value):
        if sensor not in self._recognized_sensors:
            self.create_sensor_structure(sensor)
        self.push_sensor_data(sensor, value)

    def example_init(self):
        self._recognized_sensors = {}
        self._recognized_measurement_containers = {}
        self._command_containers = {}

        label = 'devices'
        container = Container(resourceName=label)
        self._devices_container = self.create_container(None,
                                                        container,
                                                        labels=[label],
                                                        max_nr_of_instances=0)

        # create container for each actuator
        for actuator in self.actuators:
            actuator_container = Container(resourceName=actuator)
            self.create_container(
                self._devices_container.path,  # the target resource/path parenting the Container
                actuator_container,            # the Container resource or a valid container ID
                max_nr_of_instances=0,         # the container's max_nr_of_instances (here: 0=unlimited)
                labels=['actuator']            # (optional) the container's labels
            )
            # create container for the commands of the actuators
            commands_container = Container(resourceName='commands')
            commands_container = self.create_container(
                actuator_container.path,
                commands_container,
                max_nr_of_instances=0,
                labels=['commands']
            )
            # add commands_container of current actuator to self._command_containers
            self._command_containers[actuator] = commands_container
            #self.subscribe to command container of each actuator to the handler command
            self.add_container_subscription(
                commands_container.path,    # the Container or it's path to be subscribed
                self.handle_cin_creation  # reference of the notification handling function
            )
           # self.subscribe_to()

    def create_sensor_structure(self, sensor):
        print('initializing sensor: %s' % sensor)
        # create sensor container
        device_container = Container(resourceName=sensor)
        device_container = self.create_container(self._devices_container.path,
                                                 device_container,
                                                 labels=['sensor'],
                                                 max_nr_of_instances=0)

        # add sensor to _recognized_sensors
        self._recognized_sensors[sensor] = device_container

        # create measurements container
        labels = ['measurements']
        if sensor.startswith('Temp'):
            labels.append('temperature')
        else:
            labels.append('humidity')
        measurements_container = Container(resourceName='measurements')
        measurements_container = self.create_container(device_container.path,
                                                       measurements_container,
                                                       labels=labels,
                                                       max_nr_of_instances=0)

        # add measurements_container from sensor to _recognized_measurement_containers
        self._recognized_measurement_containers[sensor] = measurements_container

    def push_sensor_data(self, sensor, value):
        # build data set with value and metadata
        if sensor.startswith('Temp'):
            data = {
                'value': value,
                'type': 'temperature',
                'unit': 'degreeC'
            }
        else:
            data = {
                'value': value,
                'type': 'humidity',
                'unit': 'percentage'
            }

        # print the new data set
        print ('%s: %s' % (sensor, data))

        # finally, push the data set to measurements_container of the sensor
        self.push_content(self._recognized_measurement_containers[sensor], data)

    
    
    
    
    
    
    