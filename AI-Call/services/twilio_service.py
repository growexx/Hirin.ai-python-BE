from twilio.rest import Client
import configparser


# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Twilio Configuration
account_sid = config.get('twilio', 'TWILIO_ACCOUNT_SID')
auth_token = config.get('twilio', 'TWILIO_TOKEN')
twilio_no = config.get('twilio', 'TWILIO_PHONE_NO')
websocket_url = config.get('twilio', 'WEBSOCKET_URL')

websocket_url = "wss://" + websocket_url

class TwilioService:
    def __init__(self, account_sid: str, auth_token: str):
        self.client = Client(account_sid, auth_token)
 
    def initiate_call(self, to_number: str, from_number: str, websocket_url: str):
        call = self.client.calls.create(
            twiml=f'<Response><Connect><Stream url="{websocket_url}"/></Connect></Response>',
            to=to_number,
            from_=from_number
        )
        return call
