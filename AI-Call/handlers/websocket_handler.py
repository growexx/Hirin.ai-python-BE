from services.Twilio_service import TwilioService
from services.Deepgram_service import DeepgramService
from services.LLM_agent import LanguageModelProcessor
from services.Elevenlabs import ElevenLabsService
from services.Sns_publisher import SnsPublisher
from aiobotocore.session import AioSession
import ast

from logger.logger_config import logger

import uuid
import asyncio
import json
import time
import base64
from datetime import datetime


async def websocket_handler(client_ws,configloader,shared_data,call_status_mapping,queue_messages):
    queue_url = configloader.get('aws', 'queue_url')

    twilio_service_instance = TwilioService(configloader=configloader)
    call_start_time = None
    buffer = bytearray()
    BUFFER_SIZE = 20 * 160
    stream_sid = {"value":""}
    call_sid = {"value":""}
    call_logs = []

    outbox = asyncio.Queue()
    deepgram_service = DeepgramService(config_loader=configloader)
    deepgram_ws = None 
    deepgram_ready = asyncio.Event()
    
    accumilated_text=""
    
    llm_speaking = asyncio.Event()
    llm_processor = LanguageModelProcessor(config_loader=configloader)
    exit_message ="goodbye."
    
    elevenlabs_service = ElevenLabsService(config_loader=configloader)

    marks =[]
    
    sns_instance = SnsPublisher(configloader=configloader)

    exit_event = asyncio.Event()

    session = AioSession()

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

    # Helpful Functions
    async def text_2_stream(text):
        try:
            async for chunk in elevenlabs_service.text_to_speech(text):
                payload = {
                    "event": "media",
                    "streamSid": stream_sid["value"],
                    "media": {"payload": chunk},
                }
                await client_ws.send(json.dumps(payload))

            logger.info(f"Successfully sent text audio to Twilio")
        
        except Exception as e:

            logger.info(f"Error in sending {text} to stream, particularly {e}")

    async def send_mark(occasion="default"):
        nonlocal marks
        try:
            if occasion=="default":
                mark_label = str(uuid.uuid4())
            elif occasion=="end call":
                mark_label = "end call"
            
            message = {
                        "streamSid": stream_sid["value"],
                        "event": "mark",
                        "mark": {"name": mark_label}
                    }
            await client_ws.send(json.dumps(message))
            marks.append(mark_label)

        except Exception as e:
            logger.error(f"Found Error in sending a Mark message to twilio : {e}")

    async def check_for_transcript(deepgram_ws,timeout=0.1):
        try:

            mid_message = await asyncio.wait_for(deepgram_ws.recv(), timeout=timeout)
            dg_json = json.loads(mid_message)
            if "channel" in dg_json :
                if dg_json["channel"]["alternatives"][0]["transcript"].strip():
                    return dg_json
                return None
            else:
                return None
        except asyncio.TimeoutError:
            return None 
        
        except Exception as e:
            logger.error(f" Some error in websocket {e}")

    async def client_reciever():
        # deepgram_ws: for tts close and open ,accumilated_text : for storing and clearing text , call_start_time ,twilio_service instance to getlogs and share it 
        nonlocal deepgram_ws, call_start_time, call_sid, stream_sid, accumilated_text, twilio_service_instance, buffer, marks
        
        empty_byte_received = False

        async for message in client_ws:
            if exit_event.is_set():
                logger.info("Exit signal received in client_reciever.")
                break
            data = json.loads(message)
            if data["event"] == "connected":
                call_start_time = time.time()
                deepgram_ws = await deepgram_service.connect()
                logger.info("Deepgram websocket Connected")
                deepgram_ready.set()
                continue

            elif data["event"] == "start":
                stream_sid["value"] = data["streamSid"]
                call_sid["value"] = data["start"]["callSid"]
                await text_2_stream(" Hello This is AI Screening call , please say something to start the call ")
                await send_mark()
                llm_speaking.set()
                llm_processor.process("start the chat")
                continue

            elif data["event"] == "media":
                media = data["media"]
                chunk = base64.b64decode(media["payload"])
                buffer.extend(chunk)
                if chunk == b'':
                    empty_byte_received = True
                
            elif data["event"] == "mark":
                label = data["mark"]["name"]
                sequence_number = data["sequenceNumber"]
                logger.info(f"Audio of Sequence number :{sequence_number} and label :{label} has been played")
                marks = [m for m in marks if m != data["mark"]["name"]]
                logger.info("Removed mark succesfully")
                if not marks and llm_speaking.is_set():
                    llm_speaking.clear()
                    accumilated_text =""
                    logger.info("LLm has finshed speaking and is ready to hear")

                if label == "end call":
                    logger.info(f"Call logs Collected after completing questions are :{call_logs}")
                    exit_event.set()
                    # End the call
                    twilio_service_instance.client.calls(call_sid["value"]).fetch().update(status="completed")
                    call_status = twilio_service_instance.client.calls(call_sid["value"]).fetch().status

                    call_instance_output = next((d for d in shared_data["call_instance_list"] if d["call_sid"]==call_sid["value"]),None)
                    
                    shared_data["call_instance_list"] = [item for item in shared_data["call_instance_list"] if item != call_instance_output]


                    if call_instance_output is not None:
                        

                        call_instance_output["call_status"]= call_status_mapping.get(call_status)
                        call_instance_output["transcript"]=call_logs
                        call_instance_output["callS_start_time"]=datetime.fromtimestamp(call_start_time).isoformat()
                        call_instance_output["call_end_time"]=datetime.fromtimestamp(time.time()).isoformat()
                        call_instance_output["event"]="aiCallEnded"
                        call_instance_output.pop(call_sid["value"],None)
                        logger.info(f"{call_instance_output} is call instance given after all questions answered")
                        

                        message_id  = call_instance_output["message_id"]
                        
                        queue_msg_element = next((item for item in queue_messages["message_list"] if item["MessageId"] == message_id),None)

                        if queue_msg_element is not None:
                            logger.info(f"Found element and deleting it")
                            queue_messages["message_list"].remove(queue_msg_element)
                            delete_from_queue(message_id= message_id)

                        else:
                            logger.warning("Found out that there is not element in ")
                        
                        await sns_instance.publish(message_payload=call_instance_output)

                    call_start_time =None
                    llm_speaking.clear()
                    logger.warning("call has ended")
                    deepgram_ws.send(json.dumps({"type": "CloseStream"}))
                    deepgram_ws = None 
                    break
                
            elif data["event"] == "stop":
                try :
                    exit_event.set()
                    logger.info(call_logs)
                    logger.info("Call logs appended as call stopped in between")
                    deepgram_ready.clear() 
                    llm_speaking.clear()

                    call_status = twilio_service_instance.client.calls(call_sid["value"]).fetch().status
                    call_instance_output = next((d for d in shared_data["call_instance_list"] if d["call_sid"]==call_sid["value"]),None)
                    shared_data["call_instance_list"] = [
                        item for item in shared_data["call_instance_list"] if item != call_instance_output
                        ]

                    if call_instance_output is not None:
                        call_instance_output["call_status"]= call_status_mapping.get(call_status)
                        call_instance_output["transcript"]=call_logs
                        call_instance_output["callS_start_time"]=datetime.fromtimestamp(call_start_time).isoformat()
                        call_instance_output["call_end_time"]=datetime.fromtimestamp(time.time()).isoformat()
                        call_instance_output["event"]="aiCallEnded"
                        call_instance_output.pop(call_sid["value"],None)

                        # Remving message from queue and queue_messages list 
                        message_id  = call_instance_output["message_id"]
                        queue_msg_element = next((item for item in queue_messages["message_list"] if item["MessageId"] == message_id),None)

                        if queue_msg_element is not None:
                            logger.info(f"Found element and deleting it")
                            queue_messages["message_list"].remove(queue_msg_element)
                            delete_from_queue(message_id= message_id)

                        else:
                            logger.warning("Found out that there is not element in ")
                        await sns_instance.publish(message_payload=call_instance_output)


                    call_start_time =None
                    
                    deepgram_ws.send(json.dumps({"type": "CloseStream"}))
                    deepgram_ws = None 
                    
                    break
                except Exception as e:
                    logger.error(f"Error in SNS topic {e}")

                continue

            if len(buffer) >= BUFFER_SIZE or empty_byte_received:
                await outbox.put(buffer)
                buffer = bytearray()

    async def deepgram_sender():
        await deepgram_ready.wait()
        logger.info("Deepgram websocket started")
        while True:
            chunk = await outbox.get()
            await deepgram_ws.send(chunk)

    async def deepgram_reciever():
        
        nonlocal accumilated_text, twilio_service_instance, llm_speaking,call_sid,call_start_time
        logger.info("Starting Deepgram websocket")
        await deepgram_ready.wait()
        logger.info("Deepgram websockcet started")

        interaction_time = time.time()

        try:
            while True and deepgram_ready.is_set():
                if exit_event.is_set():
                    break

                deepgram_ready.wait()

                message_json = await check_for_transcript(deepgram_ws)

                if message_json:
                    if message_json.get("is_final"):
                        logger.info("Final message received")
                        accumilated_text += " " + message_json["channel"]["alternatives"][0]["transcript"].strip()
                    logger.info(f"recieved small audio with interim results signnifying speaker is speaking at time: {time.time() - interaction_time}")
                    interaction_time = time.time()
                    continue

                else:
                    if llm_speaking.is_set():
                        interaction_time = time.time()
                        continue

                    elapsed_time = time.time() - interaction_time

                    if elapsed_time > 1.6 and accumilated_text.strip() :
                        logger.info(f"Candidate said:{accumilated_text}.  at time {elapsed_time}")

                        # Measure time for LLM processing
                        start_llm = time.time()
                        llm_response = llm_processor.process(accumilated_text)
                        end_llm = time.time()
                        llm_time = end_llm - start_llm
                        logger.info(f"LLM processing time: {llm_time:.2f} seconds")
                        logger.info(f"LLM response: {llm_response}" )

                        # Log the response
                        call_logs.append({"type": "user", "message": accumilated_text})
                        call_logs.append({"type": "system", "message": llm_response})

                        accumilated_text = ""

                        # Measure time for Text-to-Speech
                        start_elevenlabs = time.time()
                        await text_2_stream(llm_response)
                        end_elevenlabs = time.time()
                        elevenlabs_time = end_elevenlabs - start_elevenlabs
                        logger.info(f"Text-to-Speech time: {elevenlabs_time:.2f} seconds")
                        
                        if exit_message in llm_response:
                            await send_mark(occasion="end call")
                        else:
                            await send_mark()
                        llm_speaking.set()
                    
                    elif elapsed_time > 5 and not accumilated_text and not llm_speaking.is_set():
                        silence_message = "You are not audible, could you repeat please?"
                        await text_2_stream(silence_message)
                        await send_mark()
                        interaction_time = time.time()
        
        except Exception as e:
            logger.error(f"error {e} found in Deepgram receievr")

    try:
        await asyncio.gather(deepgram_sender(), deepgram_reciever(),client_reciever())
    except Exception as e:
        logger.error(f"Failed Websocket handler due to {e}")
