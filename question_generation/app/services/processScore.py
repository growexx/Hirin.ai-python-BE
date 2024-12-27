from app.services.getTextService import GetText
from app.services.jdSummarizationService import JDSummary
from app.services.relevanceSummaryService import RelevanceSummary
from app.utils.hepler import Helper
import time
from app.logger_config import logger



class ProcessCVScore:
    @classmethod
    def getCVScore(cls,gClient,oClient,lmodel,gmodel,openModel,JdType,JdDescription,resume):

        try:
            if lmodel == '' or lmodel is None:
                logger.info('Missing LLM model confiiguration...')
            else:
                prompt_template =  Helper.read_prompt('AI-CV-Screening/app/services/job_description.txt')
                

                if JdType == 'link':
                    summarized_jd = ''
                    prompt = prompt_template.format(job_description=summarized_jd)
                    lammaJDSummary = JDSummary.getSummerizedJDUsigLamma(gClient,prompt,lmodel)
                    if lammaJDSummary != "" and resume != "":
                        relevance_prompt_template = Helper.read_prompt('AI-CV-Screening/app/services/resumeRelevance.txt')
                        prompt = relevance_prompt_template.format(job_description=lammaJDSummary,resume=resume)
                        RelevanceSummary.getRelavanceSummaryLamma(gClient,prompt,lmodel)
                    
                    openAIJDSummary=JDSummary.getSummerizedJDUsingOpenAI(oClient,prompt,openModel)

                    if openAIJDSummary != "" and resume != "":
                        relevance_prompt_template = Helper.read_prompt('AI-CV-Screening/app/services/resumeRelevance.txt')
                        prompt = relevance_prompt_template.format(job_description=openAIJDSummary,resume=resume)
                        RelevanceSummary.getRelavanceSummaryLamma(oClient,prompt,openModel)

                    gemmaJDSummary = JDSummary.getSummerizedJDUsingGemma(gClient,prompt,gmodel)
                    if gemmaJDSummary != "" and resume != "":
                        relevance_prompt_template = Helper.read_prompt('AI-CV-Screening/app/services/resumeRelevance.txt')
                        prompt = relevance_prompt_template.format(job_description=openAIJDSummary,resume=resume)
                        RelevanceSummary.getRelavanceSummaryLamma(gClient,prompt,gmodel)
                else:
                    summarized_jd = JdDescription
                    prompt = prompt_template.format(job_description=summarized_jd)
                    lammaJDSummary = JDSummary.getSummerizedJDUsigLamma(gClient,prompt,lmodel)
                    if lammaJDSummary != "" and resume != "":
                        relevance_prompt_template = Helper.read_prompt('AI-CV-Screening/app/services/resumeRelevance.txt')
                        prompt = relevance_prompt_template.format(job_description=lammaJDSummary,resume=resume)
                        RelevanceSummary.getRelavanceSummaryLamma(gClient,prompt,lmodel)
                    
                    openAIJDSummary=JDSummary.getSummerizedJDUsingOpenAI(oClient,prompt,openModel)

                    if openAIJDSummary != "" and resume != "":
                        relevance_prompt_template = Helper.read_prompt('AI-CV-Screening/app/services/resumeRelevance.txt')
                        prompt = relevance_prompt_template.format(job_description=openAIJDSummary,resume=resume)
                        RelevanceSummary.getRelavanceSummaryLamma(oClient,prompt,openModel)

                    gemmaJDSummary = JDSummary.getSummerizedJDUsingGemma(gClient,prompt,gmodel)
                    if gemmaJDSummary != "" and resume != "":
                        relevance_prompt_template = Helper.read_prompt('AI-CV-Screening/app/services/resumeRelevance.txt')
                        prompt = relevance_prompt_template.format(job_description=openAIJDSummary,resume=resume)
                        RelevanceSummary.getRelavanceSummaryLamma(gClient,prompt,gmodel)

        except Exception as e:
            logger.info(f"{e}")


            





