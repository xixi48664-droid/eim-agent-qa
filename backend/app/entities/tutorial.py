import uuid
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.mysql import Base


def _gen_id() -> str:
    return uuid.uuid4().hex


class Tutorial(Base):
    __tablename__ = "tutorial"

    tutorial_id = Column(String(32), primary_key=True, default=_gen_id)
    process_name = Column(String(100), nullable=False)
    total_steps = Column(Integer, nullable=False, default=0)
    estimated_time = Column(String(50), nullable=True)

    steps = relationship("TutorialStep", back_populates="tutorial")


class TutorialStep(Base):
    __tablename__ = "tutorial_step"

    step_id = Column(String(32), primary_key=True, default=_gen_id)
    tutorial_id = Column(String(32), ForeignKey("tutorial.tutorial_id"), nullable=False)
    step_no = Column(Integer, nullable=False)
    step_title = Column(String(200), nullable=True)
    step_content = Column(Text, nullable=False)
    image_url = Column(String(255), nullable=True)
    note = Column(Text, nullable=True)
    faq = Column(Text, nullable=True)

    tutorial = relationship("Tutorial", back_populates="steps")
