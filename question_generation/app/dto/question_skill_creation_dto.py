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
    keySkills: List[str]
    proficiencyLevel: List[str]
    questionsPerSkill: List[int]
    message: str = None

