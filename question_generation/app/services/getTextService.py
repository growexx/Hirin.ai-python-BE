from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import Docx2txtLoader
from app.logger_config import logger

class GetText:
    
    @classmethod
    def getText(cls,filePath):
       description = ""
       logger.info("file name : ",filePath)
       
       if filePath.lower().endswith(".pdf"):
        loader=PyPDFLoader(filePath)
        documents=loader.load()
        logger.info("documents : ",documents)
        total_pages = len(documents)
        logger.info("Total pages : ", total_pages)
       elif filePath.lower().endswith(".docx"):
            loader=Docx2txtLoader(filePath)
            documents=loader.load()
            logger.info("documents : ",documents)
            total_pages = len(documents)
            logger.info("Total pages : ", total_pages)
            
       for doc in documents:
        description += doc.page_content
    
       return description
