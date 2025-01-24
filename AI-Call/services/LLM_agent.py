import boto3


class LanguageModelProcessor:
    def __init__(self,config_loader):

        self.llm = boto3.client(
            "bedrock-runtime",
        )
        self.model_id = config_loader.get("llm",'model_id')

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
