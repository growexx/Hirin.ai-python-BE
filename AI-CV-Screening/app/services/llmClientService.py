from app.utils.logger_config import logger


class LLMClient:
    @classmethod
    def GroqLLM(cls,groq_client, prompt, model):
        try:
            llm_response = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": prompt}
                   
                ],
                model=model,
            )
            return llm_response.choices[0].message.content
        except Exception as e:
            logger.error(f"Failed to generate result using GROQ: {e}")
            return "Error in groq client"
    
    @classmethod
    def OpenAILLM(cls,openai_client,prompt,gptModel):
        response = openai_client.chat.completions.create(
            model=gptModel,
            messages=[
                {"role": "system", "content":prompt},
        ]
    )

        return response.choices[0].message.content
    
    @classmethod
    def GemmaLLM(cls,gemma_client,prompt, model):
        llm_response = gemma_client.chat.completions.create(
            model= model,
            messages=[{"role": "system","content": prompt}])

        return llm_response.choices[0].message.content