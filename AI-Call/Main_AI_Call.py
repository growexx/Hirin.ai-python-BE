import asyncio
import websockets
from handlers.websocket_handler import websocket_handler

from tasks.poll_queue import poll_queue
from tasks.recall_and_status import recall_and_status
from tasks.check_status_second import call_status_check
from logger.logger_config import logger
from config.config_loader import ConfigLoader


import websockets

shared_data = {
    "call_instance_list":[]
}
queue_messages = {
    "message_list":[]
}
call_status_mapping = {

    "canceled": 0,
    "completed": 1,
    "busy": 2,
    "no-answer": 3,
    "failed": 4,
    "queued":5,
    "ringing":6,
    "in-progress":7
}

duplicate_message_set = set()


async def main():
    config_loader = ConfigLoader(config_file="config.ini")
    logger.info("Starting application...")
    asyncio.create_task(poll_queue(configloader=config_loader,shared_data=shared_data,queue_messages = queue_messages,dup_set = duplicate_message_set))
    asyncio.create_task(call_status_check(shared_data=shared_data,call_status_mapping=call_status_mapping,configloader=config_loader,queue_messages=queue_messages,dup_set = duplicate_message_set))
    ws_server = await websockets.serve(
        lambda websocket,
        path :websocket_handler(client_ws=websocket,configloader=config_loader,shared_data=shared_data,call_status_mapping=call_status_mapping,queue_messages=queue_messages),
        '0.0.0.0',
        5001
        )
    await ws_server.wait_closed()
    logger.info("WebSocket server closed.")

if __name__ == "__main__":
    asyncio.run(main())
