from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import Docx2txtLoader
from app.logger_config import logger
 
class GetText:
 
    @classmethod
#     @staticmethod
    def getText(cls,filePath):
       description = ""
       logger.info(f"file name : {filePath}")
 
       if filePath.lower().endswith(".pdf"):
        loader=PyPDFLoader(filePath)
        documents=loader.load()
        logger.info(f"documents : {documents}")
        total_pages = len(documents)
        logger.info(f"Total pages : {total_pages}")
       elif filePath.lower().endswith(".docx"):
            loader=Docx2txtLoader(filePath)
            documents=loader.load()
            logger.info(f"documents : {documents}")
            total_pages = len(documents)
            logger.info(f"Total pages : {total_pages}")
 
       for doc in documents:
        description += doc.page_content
 
       return description