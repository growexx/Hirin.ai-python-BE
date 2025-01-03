from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain


class LanguageModelProcessor:
    def __init__(self, system_prompt: str,llm_model:str,llm_api_key:str):
        self.llm = ChatGroq(temperature=0, model_name=llm_model, groq_api_key=llm_api_key)
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        with open('system_prompt.txt', 'r') as file:
            system_prompt = file.read().strip()
        
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{text}")
        ])

        self.conversation = LLMChain(
            llm=self.llm,
            prompt=self.prompt,
            memory=self.memory
        )
 
    def process(self, text: str) -> str:
        self.memory.chat_memory.add_user_message(text)
        response = self.conversation.run({"text": text})
        self.memory.chat_memory.add_ai_message(response)
        return response
