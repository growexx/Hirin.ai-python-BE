from groq import Groq
from openai import OpenAI
from app.logger_config import logger

class JDSummary:
    

    @classmethod
    def getSummerizedJDUsigLamma(cls,client,prompt,model):
        llm_response = client.chat.completions.create(
           model= model,
           messages=[{"role": "system","content": prompt}])

        return llm_response.choices[0].message.content
    
    @classmethod
    def getSummerizedJDUsingGemma(cls, client,prompt,model):
        llm_response = client.chat.completions.create(
            model= model,
            messages=[{"role": "system","content": prompt}])

        return llm_response.choices[0].message.content
    

    @classmethod
    def getSummerizedJDUsingOpenAI(cls,client,prompt,model):
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an assistant that summarizes job descriptions."},
                {"role": "user", "content": prompt},
        ]
        )
        
        return response.choices[0].message.content
