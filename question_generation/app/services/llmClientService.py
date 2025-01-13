from app.logger_config import logger
import asyncio
from groq import AsyncGroq
import aiobotocore
from aiobotocore.session import AioSession
import json
import boto3

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
            return "Error in Groq client"

    @classmethod
    async def call_groq_llm(cls,async_groq_client, prompt, model):
        semaphore = asyncio.Semaphore(5)
        async with semaphore:  # Throttle API calls
            try:
                response = await async_groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    model=model,
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"Failed to generate result using GROQ: {e}")
                return f"Error in Groq client"

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
    

    @classmethod
    async def AsyncBedRockLLM(cls, prompt, model,region):
        try:
        
            session = AioSession()
            async with session.create_client('bedrock-runtime', 
                region_name = region) as client:
                
                request_body = json.dumps({"prompt": prompt})
                response = await client.invoke_model(
                modelId=model,
                accept='application/json',
                body=request_body
            )
          
            result = await response['body'].read()
            resultText = result.decode('utf-8')
            resultJson = json.loads(resultText)
            return resultJson['generation']


        except Exception as e:
            logger.error(f"Failed to generate result using Bedrock: {e}")
            return "Error in BedRock client"
        
    
    @classmethod
    def BedRockLLM(cls,client, prompt, model):
        try:
             
            model_id = model
            conversation = [{
                "role": "user",
                "content": [{"text": prompt}],
                }]
          
            response = client.converse(
                modelId=model_id,
                messages=conversation,
                )
            
            response_text = response["output"]["message"]["content"][0]["text"]
            return response_text

        except Exception as e:
            logger.error(f"Failed to generate result using Bedrock: {e}")
            return "Error in BedRock client"
