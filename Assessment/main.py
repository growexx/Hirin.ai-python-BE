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
queue_url = config['sqs']['queue_url']
sns_topic_arn = config['sns']['topic_arn']
model_id = config['bedrock']['model_id']  # Make model ID configurable

# Initialize SQS client with credentials
try:
    sqs = boto3.client(
        'sqs',
        region_name=AWS_REGION
    )
    logger.info("Successfully initialized SQS client.")
except Exception as e:
    logger.error(f"Failed to initialize SQS client: {e}")
    raise

# Initialize Bedrock Runtime client
try:
    brt = boto3.client(
        "bedrock-runtime",
        region_name=AWS_REGION
    )
    logger.info("Successfully initialized Bedrock client.")
except Exception as e:
    logger.error(f"Failed to initialize Bedrock client: {e}")
    raise


async def main():
    try:
        st = time.time()
        logger.info("Attempting to receive messages from SQS.")
        
        # Fetch messages from SQS
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
                    logger.debug(f"Assessments payload: {assessments}")

                    # Process the assessments using processor.py
                    success = await process_data(assessments, sns_topic_arn, brt, model_id)
                    
                    if success:
                        logger.info(f"Successfully processed message ID: {message['MessageId']}")
                        # Delete message if processing succeeded
                        sqs.delete_message(
                            QueueUrl=queue_url,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        logger.info(f"Deleted SQS message ID: {message['MessageId']}")
                    else:
                        logger.warning(f"Failed to process message ID: {message['MessageId']}, message will not be deleted.")
                
                except Exception as e:
                    logger.error(f"Error processing message ID {message['MessageId']}: {e}")
        else:
            logger.info("No messages available in the SQS queue.")
        
        et = time.time()
        logger.info(f"Total time taken: {et - st:.2f} seconds.")
    
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}")
