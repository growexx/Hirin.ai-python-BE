import uuid
import asyncio
import websockets
import json
from services.twilio_service import TwilioService
from services.Elevenlabs import ElevenLabsService
from services.Deepgram_service import DeepgramService
from services.LLM_agent import LanguageModelProcessor
from aiohttp import web
import configparser
from aiobotocore.session import AioSession
import re
from queue import Queue
import time 
import boto3
from botocore.exceptions import ClientError
import base64
import ast
from datetime import datetime

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Twilio Configuration
account_sid = config.get('twilio', 'TWILIO_ACCOUNT_SID')
auth_token = config.get('twilio', 'TWILIO_TOKEN')
twilio_no = config.get('twilio', 'TWILIO_PHONE_NO')
websocket_url = config.get('twilio', 'WEBSOCKET_URL')

# LLM Agent
llm_api_key = config.get('llm', 'api_key')
llm_model = config.get('llm', 'model_name')

# ElevenLabs
tts_voice_id = config.get('tts', 'voice_id')
elevenlabs_api_key = config.get('tts', 'api_key')

# Deepgram Access
deepgram_api_key = config.get('deepgram', 'deepgram_api_key')
deep_gram_url = config.get('deepgram', 'deep_gram_url')

# AWS Access
aws_access_key_id = config.get('aws', 'aws_access_key_id')
aws_secret_access_key = config.get('aws', 'aws_secret_access_key')
aws_region = config.get('aws', 'aws_region')
sns_topic_arn = config.get('aws', 'aws_sns_topic_arn')
queue_url = config.get('aws', 'queue_url')

# shared variables and functions

shared_data = {
    "call_instance_list":[]
}

call_status_mapping = {
    "canceled": 0,
    "completed": 1,
    "busy": 2,
    "no-answer": 3,
    "failed": 4,
}

async def sns_publisher(sns_client,message_payload):
    message_json = json.dumps(message_payload)
    response = sns_client.publish(
        TopicArn=sns_topic_arn,
        Message=message_json
    )
    return response

def validate_phone_no(phone_no:str):
    pattern = r"^\+91\d{10}$"
    return bool(re.match(pattern, phone_no))


async def websocket_handler(client_ws):
    twilio_service_instance = TwilioService()
    call_start_time = None
    buffer = bytearray()
    BUFFER_SIZE = 20 * 160
    stream_sid = {"value":""}
    call_sid = {"value":""}
    call_logs = []

    outbox = asyncio.Queue()
    deepgram_service = DeepgramService(api_key=deepgram_api_key,deepgram_url=deep_gram_url)
    deepgram_ws = None 
    deepgram_ready = asyncio.Event()
    
    accumilated_text=""
    
    llm_speaking = asyncio.Event()
    llm_processor = LanguageModelProcessor(llm_api_key=llm_api_key, llm_model=llm_model, system_prompt="")
    exit_message ="Thank you for completing the screening process. Your responses have been recorded, and we will get back to you soon regarding the next steps."
    
    elevenlabs_service = ElevenLabsService(api_key=elevenlabs_api_key, voice_id=tts_voice_id, model_id="eleven_flash_v2")

    marks =[]
    
    sns_client = boto3.client(
        'sns',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region
    )
    

    async def text_2_stream(text):
        async for chunk in elevenlabs_service.text_to_speech(text):
            payload = {
                "event": "media",
                "streamSid": stream_sid["value"],
                "media": {"payload": chunk},
            }
            await client_ws.send(json.dumps(payload))
    
    async def send_mark():
        nonlocal marks
        mark_label = str(uuid.uuid4())
        message = {
                    "streamSid": stream_sid["value"],
                    "event": "mark",
                    "mark": {"name": mark_label}
                }
        await client_ws.send(json.dumps(message))
        marks.append(mark_label)

    async def check_for_transcript(deepgram_ws,timeout=0.2):
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
            print(" Some error in websockert",e)

    async def client_reciever():
        nonlocal deepgram_ws,call_start_time,call_sid,stream_sid,accumilated_text,twilio_service_instance,buffer,marks
        empty_byte_received = False
        async for message in client_ws:
            data = json.loads(message)
            if data["event"] == "connected":
                call_start_time = time.time()
                deepgram_ws = await deepgram_service.connect()
                print("Deepgram Started")
                continue
            elif data["event"] == "start":
                stream_sid["value"] = data["streamSid"]
                call_sid["value"] = data["start"]["callSid"]
                await text_2_stream(" Hello This is AI Scrreening call , please say something to start the call ")
                await send_mark()
                deepgram_ready.set()
                llm_speaking.set()
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
                print(f"Audio of Sequence number :{sequence_number} and label :{label} has been played")
                marks = [m for m in marks if m != data["mark"]["name"]]
                print("removed mark succesfully")
                if not marks and llm_speaking.is_set():
                    llm_speaking.clear()
                    accumilated_text =""
                    print("LLM speaking is release and should be able to hear event")
            elif data["event"] == "stop":
                try :
                    print(call_logs)
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
                        call_instance_output["callStartTime"]=datetime.fromtimestamp(call_start_time).isoformat()
                        call_instance_output["callStartTime"]=datetime.fromtimestamp(time.time()).isoformat()
                        call_instance_output.pop(call_sid["value"],None)
                    await sns_publisher(message_payload=call_instance_output,sns_client=sns_client)
                    call_start_time =None
                except Exception as e:
                    print("Error in SNS topic",e )
                continue
            if len(buffer) >= BUFFER_SIZE or empty_byte_received:
                await outbox.put(buffer)
                buffer = bytearray()

    async def deepgram_sender():
        await deepgram_ready.wait()
        print("Deepgram websokcet started")
        while True:
            chunk = await outbox.get()
            await deepgram_ws.send(chunk)
        print("Deepgram websocket closed")


    async def deepgram_reciever():
        nonlocal accumilated_text, twilio_service_instance, llm_speaking
        print("Deepgram receiver started")
        await deepgram_ready.wait()
        print("Green flag from deepgram websocket")

        interaction_time = time.time()
        while True:
            # Measure time for `check_for_transcript` function
            message_json = await check_for_transcript(deepgram_ws)


            if message_json:
                print("Message detected")
                if message_json.get("is_final"):
                    print("Final message received")
                    accumilated_text += " " + message_json["channel"]["alternatives"][0]["transcript"].strip()
                    interaction_time = time.time()
                continue
            else:
                if llm_speaking.is_set():
                    interaction_time = time.time()
                    continue

                elapsed_time = time.time() - interaction_time
                if llm_speaking.is_set():
                    print(elapsed_time,"is time passed from check")
                if elapsed_time > 1.8 and accumilated_text.strip() :
                    print("Silence received")
                    print("Candidate said:", accumilated_text)

                    # Measure time for LLM processing
                    start_llm = time.time()
                    llm_response = llm_processor.process(accumilated_text)
                    end_llm = time.time()
                    llm_time = end_llm - start_llm
                    print(f"LLM processing time: {llm_time:.2f} seconds")
                    print("LLM response:", llm_response)

                    # Log the response
                    call_logs.append({"type": "user", "message": accumilated_text})
                    call_logs.append({"type": "system", "message": llm_response})

                    accumilated_text = ""

                    # Measure time for Text-to-Speech
                    start_elevenlabs = time.time()
                    await text_2_stream(llm_response)
                    end_elevenlabs = time.time()
                    elevenlabs_time = end_elevenlabs - start_elevenlabs
                    print(f"Text-to-Speech time: {elevenlabs_time:.2f} seconds")
                    await send_mark()
                    llm_speaking.set()

                    if exit_message in llm_response:
                        print("Call is ended")
                        # Measure time for Twilio call update
                        start_twilio = time.time()
                        twilio_service_instance.client.calls(call_sid["value"]).fetch().update(status="completed")
                        end_twilio = time.time()
                        twilio_time = end_twilio - start_twilio
                        print(f"Twilio update time: {twilio_time:.2f} seconds")
                        print(twilio_service_instance.client.calls(call_sid["value"]).fetch())
                        print(twilio_service_instance.client.calls(call_sid["value"]).fetch()["status"])
                elif elapsed_time > 5 and not accumilated_text :
                    silence_message = "You are not audible, could you repeat please?"
                    await text_2_stream(silence_message)
                    await send_mark()
                    interaction_time = time.time()


    await asyncio.gather(deepgram_sender(), deepgram_reciever(),client_reciever())


async def poll_queue():
    twilio_service = TwilioService()
    print("poll queue is started")
    session = AioSession()
    async with session.create_client('sqs', region_name=aws_region,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key) as client:
        while True:
            response = await client.receive_message(
                QueueUrl=queue_url,
                AttributeNames=['All'],
                MaxNumberOfMessages=10,  # Adjust based on your needs
                WaitTimeSeconds=20  # Long polling up to 20 seconds
            )
            messages = response.get('Messages', [])
            if messages:
                for message in messages:
                    print(f"Received message: {message['Body']}")
                    message_dict = ast.literal_eval(message['Body'])
                    phone_no = message_dict["mobileNumber"]
                    if validate_phone_no(phone_no=phone_no):
                        call = twilio_service.initiate_call(from_number=twilio_no,to_number=phone_no,websocket_url=websocket_url)
                        message_dict["call_sid"] = call.sid
                        print("Call Sid  is ",call.sid)
                    else:
                        print("invalid phone number , Call is rejected. ")
                        message_dict["call_sid"] = "call.sid"

                    shared_data["call_instance_list"].append(message_dict)
                    await client.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )

                    await client.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
            else:
                print("No messages received.")
            await asyncio.sleep(5)

async def main():
    asyncio.create_task(poll_queue())
    ws_server = await websockets.serve(websocket_handler, '0.0.0.0', 5001)  # Port 5001 for AI screening WebSocket
    await ws_server.wait_closed()
    print("Ending websocket")


if __name__ == "__main__":
    asyncio.run(main())
