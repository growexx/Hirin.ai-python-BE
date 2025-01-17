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
        async with aioboto3.Session().client(
            'sns',
            region_name=AWS_REGION
        ) as sns_client:
            sns_message = json.dumps(data)
            sns_modified_message = sns_message.replace("\n", "")
            publish_params = {
                'TopicArn': topic_arn,
                'Message': sns_modified_message,
                'Subject': f"Assessment Results for Role: {role}"
            }

            response = await sns_client.publish(**publish_params)
            logger.info(f"Message sent successfully to SNS. Topic ARN: {topic_arn}, Role: {role}")
            logger.debug(f"SNS Response: {response}")
            logger.info(f"Message sent successfully. Response: {response}")

    except Exception as e:
        logger.error(f"Failed to send message to SNS. Topic ARN: {topic_arn}, Role: {role}, Error: {e}")
        logger.info("Failed to send message. Error:", e)
        raise