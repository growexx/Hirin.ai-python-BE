from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import base64
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

tts_voice_id = config.get('tts', 'voice_id')
elevenlabs_api_key = config.get('tts', 'api_key')
elevenlabs_model = config.get('tts', 'tts_model')


class ElevenLabsService:
    def __init__(self):
        self.client = ElevenLabs(api_key=elevenlabs_api_key)
        self.voice_id = tts_voice_id
        self.model_id = elevenlabs_model
        self.voice_settings = VoiceSettings(stability=0.6, similarity_boost=1.0, style=0.1, use_speaker_boost=True)
 
    async def text_to_speech(self, text: str):
        audio_stream = self.client.text_to_speech.convert_as_stream(
            text=text,
            voice_id=self.voice_id,
            model_id=self.model_id,
            voice_settings=self.voice_settings,
            output_format="ulaw_8000"
        )
        for chunk in audio_stream:
            yield base64.b64encode(chunk).decode('utf-8')

