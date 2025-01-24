import json
import boto3
from logger.logger_config import logger

class SnsPublisher:
    def __init__(self,configloader):
        self.sns_topic_arn = configloader.get('aws', 'aws_sns_topic_arn')
        try:
            self.sns_client=boto3.client(
                'sns'
            )
        except Exception as e:
            logger.error("              --------------- SNS Client not made")
    async def publish(self,message_payload):
        try:
            message_json = json.dumps(message_payload)
            response = self.sns_client.publish(
                TopicArn=self.sns_topic_arn,
                Message=message_json
            )
            logger.info(f"Successfully published message on SNS topic with message Id :{response}")
            return response
        
        except Exception as e:
            logger.error(f"Unable to publish message on SNS topic due to {e}")
