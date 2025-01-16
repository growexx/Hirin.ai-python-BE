import boto3
import json
import uuid
import configparser
import asyncio
from faceDetectionServiceFile import FaceDetectionService
from snsPublisherFile import send_message_to_sns_async
from logger.logger_config import logger

# Load configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# AWS Configuration
AWS_REGION = config['aws']['region']
queue_url = config['sqs']['queue_url']
sns_topic_arn = config['sns']['topic_arn']

# Initialize SQS client
sqs = boto3.client(
    'sqs',
    region_name=AWS_REGION
)

# Dictionary to track processing tasks
processing_tasks = {}

def process_video(video_url, task_id, folder_index, metadata, tab_switch_count, tab_switch_timestamps, tab_switch_time, exit_full_screen):
    logger.info(f"Starting video processing: {video_url}, Task ID: {task_id}")
    try:
        service = FaceDetectionService(folder_index)
        
        total_tab_switch_time = service.processing_tab_timestamps(tab_switch_time, tab_switch_timestamps)
        
        result = service.process_video(video_url, metadata)
        
        if result:
            # Ensure `multipleFacesDetected` is handled correctly
            multiple_faces = result.get('multipleFacesDetected', False)
            proctoring_score = service.calculate_proctoring_score({
                'exit_full_screen': exit_full_screen,
                'tab_switch_count': tab_switch_count,
                'tab_switch_time': total_tab_switch_time,
                'result': result,
                'multipleFacesDetected': multiple_faces
            })
            
            logger.info(f"Proctoring Score: {proctoring_score['Proctoring Final Score']}")
            processing_tasks[task_id] = {"status": "completed", "result": result, "proctoring_score": proctoring_score}
        return result

    except Exception as e:
        logger.error(f"Failed to process video for Task ID: {task_id}: {e}", exc_info=True)
        processing_tasks[task_id] = {"status": "failed", "error": str(e)}
        return None

def fetch_and_process_from_sqs():
    logger.info("Starting to fetch messages from SQS...")
    
    try:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=5,
            MessageAttributeNames=['All']
        )

        if 'Messages' in response:
            for message in response['Messages']:
                try:
                    logger.info(f"Processing SQS message ID: {message['MessageId']}")
                    assessments = json.loads(message['Body'])
                    parsed_message = json.loads(assessments.get('Message', '{}'))
                    metadata = parsed_message['metadata']
                    questions = parsed_message["questions"]
                    tab_switch_count = parsed_message["tab_switch_count"]
                    tab_switch_timestamps = parsed_message["tab_switch_timestamps"]
                    tab_switch_time = parsed_message["tab_switch_time"]
                    exit_full_screen = parsed_message["exit_full_screen"]
                    candidate_id = metadata.get("candidate_id")  # Extract candidate_id

                    aggregated_results = []
                    for index, question in enumerate(questions, start=1):
                        user_video_url = question.get("user_video_url")
                        if not user_video_url:
                            logger.warning(f"Missing user_video_url in question {index}")
                            continue

                        task_id = str(uuid.uuid4())
                        processing_tasks[task_id] = {"status": "processing"}
                        result = process_video(
                            user_video_url, task_id, index, metadata,
                            tab_switch_count, tab_switch_timestamps, tab_switch_time,
                            exit_full_screen
                        )
                        if result:
                            # Add additional fields to the result
                            result.update({
                                "multipleFacesDetected": result.get("numberOfFacesDetected", 0) > 1,
                                "noFaceDetected": result.get("numberOfFacesDetected", 0) == 0,
                                "tab_switch_count": tab_switch_count,
                                "exit_full_screen": exit_full_screen,
                                "tab_switch_time": tab_switch_time,
                                "proctor_score": processing_tasks[task_id].get("proctoring_score", {}).get("Proctoring Final Score"),
                                "candidate_id": candidate_id,
                                "tab_switch_timestamps": tab_switch_timestamps,
                            })
                            aggregated_results.append(result)
                        
                        
                        finalResult = {
                            "metadata" : metadata,
                            "proctoringData": aggregated_results
                        }

                    asyncio.run(send_message_to_sns_async(sns_topic_arn, finalResult, metadata))
                    
                    # Delete the SQS message after processing
                    sqs.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                    logger.info(f"Successfully processed and deleted SQS message ID: {message['MessageId']}")

                except Exception as e:
                    logger.error(f"Error processing SQS message ID: {message['MessageId']}: {e}", exc_info=True)
                    continue
        else:
            logger.info("No messages available in SQS.")
        
    except Exception as e:
        logger.critical(f"Failed to fetch messages from SQS: {e}", exc_info=True)


if __name__ == "__main__":
    fetch_and_process_from_sqs()
