import asyncio
import boto3
import json
import configparser
from processor import process_data
from logger.logger_config import logger
import time

# Load configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

AWS_REGION = config['aws']['region']
AWS_ACCESS_KEY_ID = config['aws']['access_key_id']
AWS_SECRET_ACCESS_KEY = config['aws']['secret_access_key']
queue_url = config['sqs']['queue_url']
sns_topic_arn = config['sns']['topic_arn']

# Initialize SQS client with credentials
try:
    sqs = boto3.client(
        'sqs',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    logger.info("Successfully initialized SQS client.")

except Exception as e:
    logger.error(f"Failed to initialize SQS client: {e}")
    raise

try:
    brt = boto3.client(
        "bedrock-runtime",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    
    # Set the model ID, e.g., Amazon Titan Text G1 - Express.
    model_id = "meta.llama3-3-70b-instruct-v1:0"
    logger.info("Successfully initialized bedrock client.")
except Exception as e:
    logger.error(f"Failed to initialize SQS client: {e}")
    raise

async def main():
    try:
        st = time.time()
        # Fetch messages from SQS
        logger.info("Attempting to receive messages from SQS.")
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=5,
            MessageAttributeNames=['All']
        )

        if 'Messages' in response:
            for message in response['Messages']:
                try:
                    logger.info(f"Processing message ID: {message['MessageId']}")
                    assessments = json.loads(message['Body'])
                    logger.info(f"assessments :: {assessments}")  # Parse the message as JSON

                    # Process the assessments using processor.py
                    success = await process_data(assessments, sns_topic_arn, brt, model_id)
                    logger.info(f"success :: {success}")
                    if success:
                        logger.info(f"Successfully processed: {message['MessageId']}")
                        try:
                            qs = boto3.client(
                                'sqs',
                                region_name=AWS_REGION,
                                aws_access_key_id=AWS_ACCESS_KEY_ID,
                                aws_secret_access_key=AWS_SECRET_ACCESS_KEY
                            )
                            qs.delete_message(
                                QueueUrl=queue_url,
                                ReceiptHandle=message['ReceiptHandle']
                            )
                            logger.info("Successfully Message Deleted.")

                        except Exception as e:
                            logger.error(f"Failed to initialize SQS client: {e}")
                            raise
                     
                    else:
                        logger.warning(f"Failed to process message ID: {message['MessageId']}")
                    
                except json.JSONDecodeError as je:
                    logger.error(f"JSON decoding error for message ID {message['MessageId']}: {je}")
                except Exception as e:
                    logger.error(f"Error processing message ID {message['MessageId']}: {e}")

            et = time.time()
            totalTime = et-st
            logger.info(f"time taken :: {totalTime}")

        else:
            et = time.time()
            totalTime = et-st
            logger.info(f"time taken :: {totalTime}")
            logger.info("No messages available in the SQS queue.")

        et = time.time()
        totalTime = et-st
        logger.info(f"time taken :: {totalTime}")
    except Exception as e:
        logger.error(f"Failed to read messages from SQS: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}")
