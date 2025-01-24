from twilio.rest import Client


class TwilioService:
    def __init__(self,configloader):
        self.account_sid = configloader.get('twilio', 'TWILIO_ACCOUNT_SID')
        self.auth_token = configloader.get('twilio', 'TWILIO_TOKEN')
        self.websocket_url = configloader.get('twilio', 'WEBSOCKET_URL')
        self.twilio_no = configloader.get('twilio', 'TWILIO_PHONE_NO')

        self.client = Client(self.account_sid, self.auth_token)
 
    def initiate_call(self, to_number: str, websocket_url: str):
        call = self.client.calls.create(
            twiml=f'<Response><Connect><Stream url="{websocket_url}"/></Connect></Response>',
            to=to_number,
            from_=self.twilio_no
        )
        return call
