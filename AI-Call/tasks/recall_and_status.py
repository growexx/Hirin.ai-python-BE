from logger.logger_config import logger
from services.Twilio_service import TwilioService
import asyncio




async def recall_and_status(shared_data,call_status_mapping,configloader):
    twilio_no = configloader.get('twilio', 'TWILIO_PHONE_NO')
    websocket_url = configloader.get('twilio', 'WEBSOCKET_URL')
    
    while True:
        try:
            call_instance = shared_data["call_instance_list"]
            logger.info(f"The recheck call demonstates following data gathered : {call_instance}")
    
            for instance in shared_data["call_instance_list"]:
                
                twilio_service = TwilioService(configloader=configloader)
                call_status = twilio_service.client.calls(instance["call_sid"]).fetch().status
                logger.info(f"call status is {call_status}")
    
                if call_status_mapping.get(call_status) in [0,2,3,4,5] :
        
                    if instance["wait_n_mins"] == 0:
        
                        call= twilio_service.initiate_call(to_number = instance["mobileNumber"], websocket_url=websocket_url)
                        instance["call_sid"] = call.sid
                        instance["wait_n_mins"] = 3
                        mobile_no = instance["mobileNumber"]
                        logger.info(f" Recalling phone no {mobile_no}")

                    else:
                        instance["wait_n_mins"] -= 1

        except Exception as e:
            logger.error(f"Error in recall specifically {e}. ")
        
        finally:
            await asyncio.sleep(60)
