from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Union
from typing import List


class QuestionSkillCreationInputDTO(BaseModel):
    job_title: str
    job_description : str
    total_questions : int
    interview_duration: int
    job_description_type : str

class QuestionSkillCreationOutputDTO(BaseModel):
    status : str
    key_skills: List[str]
    proficiency_level: List[str]
    questions_per_skill: List[int]
    message: str = None

