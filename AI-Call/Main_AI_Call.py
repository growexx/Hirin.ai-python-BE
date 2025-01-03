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
aws_secret_access_key = config.get('aws', 'aws_secret_accesss_key')
aws_region = config.get('aws', 'aws_region')
sns_topic_arn = config.get('aws', 'aws_sns_topic_arn')
queue_url = config.get('aws', 'queue_url')
deep_gram_url = config.get('deepgram', 'deep_gram_url')

websocket_url = "wss://" + websocket_url
SILENCE_THRESHOLD = 12

def validate_phone_no(phone_no:str):
    pattern = r"^\+91\d{10}$"
    return bool(re.match(pattern, phone_no))

# WebSocket server to handle incoming WebSocket connections
async def websocket_handler(client_ws):
    start_time = time.time()
    Call_ongoing = asyncio.Lock()
    deepgram_service = DeepgramService(api_key=deepgram_api_key,deepgram_url=deep_gram_url)
    llm_processor = LanguageModelProcessor(llm_api_key=llm_api_key, llm_model=llm_model, system_prompt="")
    elevenlabs_service = ElevenLabsService(api_key=elevenlabs_api_key, voice_id=tts_voice_id, model_id="eleven_flash_v2")
    sqs_client = boto3.resource('sqs', region_name=aws_region,aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

    async with deepgram_service as deepgram_ws:
        outbox = asyncio.Queue()
        stream_sid = {"value": 0}
        silence_start_time = None
        silence_count = 0
        is_message_playing =False
        small_silence_threshold = 0.2
        big_silence_threshold = 8
        transcript = ""
        call_logs=[]
        sns_client = boto3.client(
            'sns',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
            )
        


        async def stop_current_stream():
            if Call_ongoing.locked():
                print("Stopped current Stream")
                payload = {
                    "event": "clear",
                    "streamSid": stream_sid["value"],
                }
                silence_count =0 
                await client_ws.send(json.dumps(payload))


        async def deepgram_sender():
            nonlocal call_logs
            while True:
                chunk = await outbox.get()
                await deepgram_ws.send(chunk)

        async def deepgram_receiver():
            receiver_start_time = time.time()
            print(f"Deepgram receiver started at {receiver_start_time:.2f}")

            nonlocal silence_start_time, is_message_playing, transcript
            async for message in deepgram_ws:
                message_start_time = time.time()

                # Parsing message
                dg_json = json.loads(message)
                if "channel" not in dg_json:
                    continue

                new_transcript = dg_json["channel"]["alternatives"][0]["transcript"]
                
                if new_transcript.strip():
                    transcript_start_time = time.time()
                    transcript += " " + new_transcript
                    silence_start_time = None 
                    print(f"Partial transcript updated at {transcript_start_time:.2f}: {transcript}")

                else:
                    # Handling silence
                    if silence_start_time is None:
                        silence_start_time = time.time()
                        print(f"Started silence at {silence_start_time:.2f}")
                        continue

                    elif time.time() - silence_start_time > small_silence_threshold:
                        if len(transcript.strip()) > 0:
                            silence_threshold_time = time.time()
                            print(f"Reached small silence threshold at {(time.time()-silence_threshold_time):.2f}")

                            llm_response_start_time = time.time()
                            llm_response = llm_processor.process(transcript)
                            print(f"LLM response generated at {(time.time()-llm_response_start_time):.2f}: {llm_response}")
                            
                            # SNS publishing and storing the call logs
                            call_logs.append({"speaker": "Candidate Response", "message": transcript})
                            call_logs.append({"speaker": "Agent", "message": llm_response})

                            is_message_playing = True
                            transcript = " "

                            # Text-to-speech conversion
                            elevenlabs_start_time = time.time()
                            async for chunk in elevenlabs_service.text_to_speech(llm_response):
                                payload = {
                                    "event": "media",
                                    "streamSid": stream_sid["value"],
                                    "media": {"payload": chunk},
                                }
                                await client_ws.send(json.dumps(payload))
                            print(f"Text-to-speech completed at {time.time() - elevenlabs_start_time:.2f} seconds")

                            silence_start_time = None
                            continue
                        else:
                            if time.time() - silence_start_time > big_silence_threshold:
                                is_message_playing = False

                # Handling long silence (quiet message)
                    elif time.time() - silence_start_time > 15 and not is_message_playing:
                        silence_message_time = time.time()
                        print(f"Reached large silence threshold at {silence_message_time:.2f}")
                        silence_message = "It seems quiet. Let me know if you need anything!"
                        is_message_playing = True

                        async for chunk in elevenlabs_service.text_to_speech(silence_message):
                            payload = {
                                "event": "media",
                                "streamSid": stream_sid["value"],
                                "media": {"payload": chunk},
                            }
                            await client_ws.send(json.dumps(payload))
                        print(f"Sent silence message at {time.time() - silence_message_time:.2f} seconds")
                        silence_start_time = None

            print(f"Deepgram receiver finished in {time.time() - receiver_start_time:.2f} seconds")

                                              
        async def client_receiver():
            nonlocal call_logs,sns_client
            await deepgram_service.client_receiver(client_ws, outbox, stream_sid,call_ongoing=Call_ongoing,call_logs = call_logs,sns_topic_arn=sns_topic_arn,sns_client=sns_client)

        await asyncio.gather(deepgram_sender(), deepgram_receiver(), client_receiver())


async def poll_queue():
    twilio_service = TwilioService(account_sid=account_sid,auth_token=auth_token)
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
                    if validate_phone_no(message['Body']):
                        call = twilio_service.initiate_call(from_number=twilio_no,to_number=message['Body'],websocket_url=websocket_url)
                        print(call.sid)
                    
                    else:
                        print("invalid phone number , Call is rejected. ")

                    await client.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
            else:
                print("No messages received.")
            # Wait for 5 seconds before the next poll
            await asyncio.sleep(5)

async def main():
    asyncio.create_task(poll_queue())
    ws_server = await websockets.serve(websocket_handler, 'localhost', 5001)  # Port 5001 for AI screening WebSocket
    await ws_server.wait_closed()
    print("Ending websocket")

if __name__ == "__main__":
    asyncio.run(main())
