import asyncio
import websockets
import base64
import json
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

deepgram_api_key = config.get('deepgram', 'deepgram_api_key')
deepgram_url = config.get('deepgram', 'deep_gram_url')

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
    def __init__(self):
        self.api_key = deepgram_api_key
        self.deepgram_url = deepgram_url
        self.ws = None  

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

   
