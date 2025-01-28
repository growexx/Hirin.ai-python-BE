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
    async def send_message_to_sns_async(self,message,subject,AWS_REGION,topic_arn):
        try:
            async with aioboto3.Session().client('sns',region_name=AWS_REGION) as sns_client:
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
            logger.info("Failed to send message. Error:", e)
            return None


    @classmethod
    async def send_error_message_to_sns_async(self, error, message, subject, relevanceSummary, AWS_REGION,topic_arn):
        try:
            relevanceSummary = json.loads(relevanceSummary)
            relevanceSummary['metadata'] = message['metadata']
            relevanceSummary['error'] = error
            relevanceSummary = json.dumps(relevanceSummary)
            await SNSSender.send_message_to_sns_async(relevanceSummary,subject,AWS_REGION,topic_arn)
            logger.info(f"successfully send the error message...")
        except Exception  as e:
            logger.info("Failed to send message.Error: ",e)

         


    
