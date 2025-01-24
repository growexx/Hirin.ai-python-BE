from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import base64

class ElevenLabsService:
    def __init__(self,config_loader):
        self.tts_voice_id = config_loader.get('tts', 'voice_id')
        self.elevenlabs_api_key = config_loader.get('tts', 'api_key')
        self.elevenlabs_model = config_loader.get('tts', 'tts_model')
        
        self.client = ElevenLabs(api_key=self.elevenlabs_api_key)
        self.voice_settings = VoiceSettings(stability=0.6, similarity_boost=1.0, style=0.1, use_speaker_boost=True)
 
    async def text_to_speech(self, text: str):
        audio_stream = self.client.text_to_speech.convert_as_stream(
            text=text,
            voice_id=self.tts_voice_id,
            model_id=self.elevenlabs_model,
            voice_settings=self.voice_settings,
            output_format="ulaw_8000"
        )
        for chunk in audio_stream:
            yield base64.b64encode(chunk).decode('utf-8')
