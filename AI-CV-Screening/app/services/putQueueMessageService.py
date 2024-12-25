import oci
from app.utils.config_loader import Config
import os
import time

class PutMessageQueue:
    service_endpoint = Config.get('Queue','service_endpoint')
    queue_id = Config.get('Queue','queue_id')
    mainPath = Config.get('Queue','mainPath')
    confFilePath =  Config.get('Queue','confFilePath')
    
    @classmethod
    @staticmethod
    def putMessage(cls):
        time.sleep(10)
        print(f"service_endpoint:{cls.service_endpoint}")
        path = os.path.join(cls.mainPath, cls.confFilePath) 
        config = oci.config.from_file(path)
        queue_client = oci.queue.QueueClient(
            config,
            service_endpoint= cls.service_endpoint
        )
        
        put_messages_response = queue_client.put_messages(
            queue_id= cls.queue_id,
            put_messages_details=oci.queue.models.PutMessagesDetails(
                messages=[
                    oci.queue.models.PutMessagesDetailsEntry(
                        content="python message send demo to queue jainil",
                        metadata=oci.queue.models.MessageMetadata(
                            custom_properties={
                                'demo': 'hirin'}))]))
        
        print(put_messages_response.data)
