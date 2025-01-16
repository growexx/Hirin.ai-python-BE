import boto3
import configparser


# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')



class LanguageModelProcessor:
    def __init__(self):
        # Initialize Bedrock LLM
        self.llm = boto3.client(
            "bedrock-runtime"
        )
        self.model_id = "meta.llama3-3-70b-instruct-v1:0"

        with open('system_prompt.txt', 'r') as file:
            system_prompt = file.read().strip()
        self.messages = [{"role":"user","content":[{"text":system_prompt}]}]

    def process(self, text: str) -> str:
        self.messages[0]["content"][0]["text"]+=f"role :user ,content:{text}\n"
        response = self.llm.converse(
            modelId=self.model_id,
            messages=self.messages,
        )
        response_text = response["output"]["message"]["content"][0]["text"]
        self.messages[0]["content"][0]["text"]+=f"role :agent ,content:{response_text}\n"
        return response_text

