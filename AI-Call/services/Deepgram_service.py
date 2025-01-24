import asyncio
import websockets

class DeepgramService:
    
    def __init__(self,config_loader):
        self.api_key = config_loader.get('deepgram', 'deepgram_api_key')
        self.deepgram_url = config_loader.get('deepgram', 'deep_gram_url')
        self.ws = None  

    async def connect(self):
        headers = {'Authorization': f'Token {self.api_key}'}
        self.ws = await websockets.connect(
            self.deepgram_url,
            extra_headers=headers,
            ping_interval=10,
            ping_timeout=5 
        )
        return self.ws  # Return the WebSocket connection

    async def __aenter__(self):
        return await self.connect()

    async def __aexit__(self, exc_type, exc, tb):
        if self.ws:
            await self.ws.close()

   