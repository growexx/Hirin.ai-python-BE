from app.logger_config import logger

class RelevanceSummary:

    
    @classmethod
    def getRelavanceSummaryLamma(cls,client,prompt, model):
        llm_response = client.chat.completions.create(
           model= model,
           messages=[{"role": "system","content": prompt}])

        return llm_response.choices[0].message.content
    
    @classmethod
    def getRelavanceSummaryOpenAI(cls,client,prompt,gptModel):
        response = client.chat.completions.create(
            model=gptModel,
            messages=[
                {"role": "system", "content": "You are an assistant that summarizes job descriptions."},
                {"role": "user", "content": prompt},
        ]
    )

        return response.choices[0].message.content
    
    @classmethod
    def getRelavanceSummaryGemma(cls,client,prompt, model):
        llm_response = client.chat.completions.create(
            model= model,
            messages=[{"role": "system","content": prompt}])

        return llm_response.choices[0].message.content