from typing import Optional, List
from pydantic import BaseModel


class StepForm(BaseModel):
    stepNo: int
    stepTitle: Optional[str] = None
    stepContent: str
    imageUrl: Optional[str] = None
    note: Optional[str] = None
    faq: Optional[str] = None


class TutorialCreateRequest(BaseModel):
    processName: str
    estimatedTime: Optional[str] = None
    steps: List[StepForm]


class TutorialUpdateRequest(BaseModel):
    processName: Optional[str] = None
    estimatedTime: Optional[str] = None
    steps: Optional[List[StepForm]] = None


class StepRecord(BaseModel):
    stepId: str
    stepNo: int
    stepTitle: str = ""
    stepContent: str
    imageUrl: Optional[str] = None
    note: Optional[str] = None
    faq: Optional[str] = None


class TutorialRecord(BaseModel):
    tutorialId: str
    processName: str
    totalSteps: int = 0
    estimatedTime: str = ""


class TutorialDetail(BaseModel):
    tutorialId: str
    processName: str
    totalSteps: int = 0
    estimatedTime: str = ""
    steps: List[StepRecord] = []
