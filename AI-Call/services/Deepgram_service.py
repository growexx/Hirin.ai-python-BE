import asyncio
import websockets
import base64
import json
import configparser

config = configparser.ConfigParser()
config.read('config.ini')


async def sns_publisher(sns_client,sns_topic_arn,message):
    message_payload = {
        "message": message,
    }
    message_json = json.dumps(message_payload)
    response = sns_client.publish(
        TopicArn=sns_topic_arn,
        Message=message_json
    )
    return response

class DeepgramService:
    def __init__(self, api_key: str,deepgram_url:str):
        self.api_key = api_key
        self.deepgram_url = deepgram_url
        self.ws = None  # Store the WebSocket connection here

    async def connect(self):
        headers = {'Authorization': f'Token {self.api_key}'}
        self.ws = await websockets.connect(
            self.deepgram_url,
            extra_headers=headers,
            ping_interval=10,  # Send a ping every 20 seconds      
            ping_timeout=5 # Wait 10 seconds for a pong response
        )
        return self.ws  # Return the WebSocket connection

    async def __aenter__(self):
        return await self.connect()

    async def __aexit__(self, exc_type, exc, tb):
        if self.ws:
            await self.ws.close()

    async def client_receiver(self, client_ws, outbox: asyncio.Queue, stream_sid: dict,call_ongoing,call_logs:list,sns_client,sns_topic_arn):
        BUFFER_SIZE = 20 * 160
        buffer = bytearray()
        empty_byte_received = False
        audio_cursor = 0.0

        async for message in client_ws:
            try:
                data = json.loads(message)
                if data["event"] == "connected":
                    await call_ongoing.acquire()
                    continue
                elif data["event"] == "start":
                    stream_sid["value"] = data["streamSid"]
                    if not call_ongoing.locked():
                        await call_ongoing.acquire()
                    continue
                elif data["event"] == "media":
                    media = data["media"]
                    chunk = base64.b64decode(media["payload"])
                    time_increment = len(chunk) / 8000.0
                    audio_cursor += time_increment
                    buffer.extend(chunk)
                    if chunk == b'':
                        empty_byte_received = True
                elif data["event"] == "stop":
                    call_ongoing.release()
                    try :
                        await sns_publisher(message=call_logs,sns_client=sns_client,sns_topic_arn=sns_topic_arn)
                    except Exception as e:
                        print("Error in SNS topic",e )
                    print("Call ended")
                    break

                if len(buffer) >= BUFFER_SIZE or empty_byte_received:
                    await outbox.put(buffer)
                    buffer = bytearray()
            except Exception as e:
                break

        await outbox.put(b'')