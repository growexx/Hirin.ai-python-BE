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

























# import json
# import aioboto3
# import configparser
# from logger_config import logger 

# # Load configuration from config.ini
# config = configparser.ConfigParser()
# config.read('config.ini')

# AWS_REGION = config['aws']['region']
# AWS_ACCESS_KEY_ID = config['aws']['access_key_id']
# AWS_SECRET_ACCESS_KEY = config['aws']['secret_access_key']

# async def send_message_to_sns_async(topic_arn, data, role):
#     try:
#         async with aioboto3.Session().client(
#             'sns',
#             region_name=AWS_REGION,
#             aws_access_key_id=AWS_ACCESS_KEY_ID,
#             aws_secret_access_key=AWS_SECRET_ACCESS_KEY
#         ) as sns_client:
#             sns_message = json.dumps(data, indent=2)
#             publish_params = {
#                 'TopicArn': topic_arn,
#                 'Message': sns_message,
#                 'Subject': f"Assessment Results for Role: {role}"
#             }
#             response = await sns_client.publish(**publish_params)
#             print("Message sent successfully. Response:", response)
#     except Exception as e:
#         print("Failed to send message. Error:", e)






# import json
# import aioboto3
# import configparser

# # Load configuration from config.ini
# config = configparser.ConfigParser()
# config.read('config.ini')

# AWS_REGION = config['aws']['region']
# AWS_ACCESS_KEY_ID = config['aws']['access_key_id']
# AWS_SECRET_ACCESS_KEY = config['aws']['secret_access_key']

# async def send_message_to_sns_async(topic_arn, data, role):
#     try:
#         async with aioboto3.Session().client(
#             'sns',
#             region_name=AWS_REGION,
#             aws_access_key_id=AWS_ACCESS_KEY_ID,
#             aws_secret_access_key=AWS_SECRET_ACCESS_KEY
#         ) as sns_client:
#             sns_message = json.dumps(data, indent=2)
#             publish_params = {
#                 'TopicArn': topic_arn,
#                 'Message': sns_message,
#                 'Subject': f"Assessment Results for Role: {role}"
#             }
#             response = await sns_client.publish(**publish_params)
#             print("Message sent successfully. Response:", response)
#     except Exception as e:
#         print("Failed to send message. Error:", e)