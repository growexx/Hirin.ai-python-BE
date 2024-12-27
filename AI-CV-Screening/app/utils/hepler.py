from app.logger_config import logger

class Helper:

    @classmethod
    def read_prompt(cls, file_name):
        try:
            with open(file_name, 'r') as file:
                content = file.read()
                logger.info(f"Successfully read prompt file: {file_name}")
                return content
        except Exception as e:
            logger.info(f"Failed to read prompt file {file_name}: {e}")
            return ""