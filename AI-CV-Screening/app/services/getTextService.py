from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.logger_config import logger

class GetText:
    
    @classmethod
    @staticmethod
    def getText(filePath):
       description = ""
       print("file name : ",filePath)
       
       if filePath.lower().endswith(".pdf"):
        loader=PyPDFLoader(filePath)
        documents=loader.load()
        print("documents : ",documents)
        total_pages = len(documents)
        print("Total pages : ", total_pages)
       elif filePath.lower().endswith(".docx"):
            loader=Docx2txtLoader(filePath)
            documents=loader.load()
            print("documents : ",documents)
            total_pages = len(documents)
            print("Total pages : ", total_pages)
            
       for doc in documents:
        description += doc.page_content
    
       return description
