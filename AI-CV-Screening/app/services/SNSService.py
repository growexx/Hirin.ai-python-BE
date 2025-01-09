import asyncio
import aioboto3
import json
from app.utils.config_loader import Config
from app.utils.logger_config import logger
from app.services.getTextService import GetText
from app.services.llmClientService import LLMClient
from app.utils.hepler import Helper
from groq import Groq
from openai import OpenAI
from datetime import datetime


class SNSSender:
          
    @classmethod
    async def send_message_to_sns_async(self,message,subject,AWS_REGION,AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY,topic_arn):
        try:
            async with aioboto3.Session().client('sns',region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY) as sns_client:
                publish_params = {
                    'TopicArn': topic_arn,
                    'Message': message,
                }
                if subject:
                    publish_params['Subject'] = subject
                    
                response = await sns_client.publish(**publish_params)
                logger.info("Message sent successfully. Response:", response)
                return response
        except Exception as e:
            print("Failed to send message. Error:", e)
            return None
        


    
