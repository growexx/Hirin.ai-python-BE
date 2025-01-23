import json
import aioboto3
import configparser
from logger.logger_config import logger

# Load configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

AWS_REGION = config['aws']['region']

async def send_message_to_sns_async(topic_arn, data, role):
    try:
        logger.info(f"Preparing to send message to SNS. Topic ARN: {topic_arn}, Role: {role}")
        
        async with aioboto3.Session().client(
            'sns',
            region_name=AWS_REGION
        ) as sns_client:
            sns_message = json.dumps(data)
            publish_params = {
                'TopicArn': topic_arn,
                'Message': sns_message
            }
            logger.debug(f"SNS message payload: {sns_message}")
            response = await sns_client.publish(**publish_params)
            logger.info(f"Message sent successfully. Response: {response}")
    except Exception as e:
        logger.error(f"Failed to send message to SNS. Error: {e}")