from logger.logger_config import logger
from services.Twilio_service import TwilioService
import asyncio
from aiobotocore.session import AioSession
import ast
from utils.validators import validate_phone_no

async def call_status_check(shared_data,call_status_mapping,configloader,queue_messages,dup_set):
    queue_url = configloader.get('aws', 'queue_url')
    websocket_url = configloader.get('twilio', 'WEBSOCKET_URL')
    session = AioSession()
    twilio_service = TwilioService(configloader=configloader)


    async def delete_from_queue(message_id):
        try:
            async with session.create_client('sqs') as client:
                response = await client.receive_message(
                    QueueUrl=queue_url,
                    AttributeNames=['All'],
                    MaxNumberOfMessages=1,  
                    WaitTimeSeconds=20,
                    VisibilityTimeout=0,
                )
                
                messages = response.get('Messages', [])
                logger.info(messages)
                
                if messages:
                    for message in messages:
                        whole_message_dict = ast.literal_eval(message['Body'])
                        if message_id == whole_message_dict["MessageId"]:
                            logger.info("Got that the message has ended , Deleting message from Queue")
                            await client.delete_message(QueueUrl=queue_url,ReceiptHandle=message['ReceiptHandle'])
        except Exception as e:
            logger.error(f"Error in deleting the message from queue : {e}")

    while True:

        for message in queue_messages["message_list"]:

            shared_data_match = next((item for item in shared_data["call_instance_list"] if item["message_id"] == message["MessageId"]),None)
            

            if shared_data_match is not None:

                call_status = twilio_service.client.calls(shared_data_match["call_sid"]).fetch().status
                logger.info(f"Call status is {call_status}")
                
                if call_status_mapping.get(call_status) in [0,1,2,3,4]:
                    logger.info("Call has ended and we can stop the task for now")
                    delete_from_queue(message_id=message["MessageId"])
                    queue_messages["message_list"].remove(message)
                    logger.info(queue_messages["message_list"])
                    
            else:
                logger.info(f"Found {message} in queue_message but not in shared_data, This happens when it is removed with websockthandler possibly when call has ended")
                await delete_from_queue(message_id=message["MessageId"])
                queue_messages["message_list"].remove(message)

        await asyncio.sleep(2)

