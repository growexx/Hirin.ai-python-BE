import asyncio
from app.utils.logger_config import logger
import aioboto3

class SQSMessage:
    
    @classmethod
    async def receive_messages(self, sqs,queueUrl,maxNumberOfMessage,waitTime):
        try:
            response = await sqs.receive_message(
                QueueUrl=queueUrl,
                MaxNumberOfMessages=maxNumberOfMessage,
                WaitTimeSeconds=waitTime,
                MessageAttributeNames=['all'],
                VisibilityTimeout=100
            )
            messages = response.get('Messages', [])
            return messages
        except Exception as e:
            logger.info(f"Error while reading message from queue: {e}")
            return None
    

    @classmethod
    async def delete_message(cls,message,queueUrl,AWS_REGION):
        try:
            async with aioboto3.Session().client('sqs',region_name=AWS_REGION) as sqs:
                await sqs.delete_message(
                    QueueUrl=queueUrl,
                    ReceiptHandle=message['ReceiptHandle']
                )

            logger.info(f"message deleted successfully : {message['Body']}")
            return True
            
        except Exception as e:
            logger.error(f"Error occured while delete message from queue: {e}")
            return False