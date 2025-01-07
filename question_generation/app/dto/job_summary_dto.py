from pydantic import BaseModel, HttpUrl, Field




class JobSummaryRequestDTO(BaseModel):
    job_description_type: str
    job_description: str
    job_description_url: str


class JobSummaryResponseDTO(BaseModel):
    job_summary: str 
    