import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.mysql import Base


def _gen_id() -> str:
    return uuid.uuid4().hex


class Component(Base):
    __tablename__ = "component"

    component_id = Column(String(32), primary_key=True, default=_gen_id)
    model = Column(String(100), nullable=False)
    type = Column(String(50), nullable=True)
    package_type = Column(String(50), nullable=True)
    manufacturer = Column(String(100), nullable=True)
    datasheet_url = Column(String(255), nullable=True)
    image_url = Column(String(255), nullable=True)
    create_time = Column(DateTime, server_default=func.now())
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now())

    params = relationship("ComponentParam", back_populates="component")


class ComponentParam(Base):
    __tablename__ = "component_param"

    param_id = Column(String(32), primary_key=True, default=_gen_id)
    component_id = Column(String(32), ForeignKey("component.component_id"), nullable=False)
    param_name = Column(String(100), nullable=False)
    param_value = Column(String(100), nullable=False)
    param_unit = Column(String(50), nullable=True)

    component = relationship("Component", back_populates="params")
