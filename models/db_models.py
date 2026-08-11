from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from config.database_config import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)  # 存加密后的密码
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联（一对多）
    mistakes = relationship("Mistake", back_populates="owner")
    courses = relationship("StudyRecord", back_populates="owner")

class Mistake(Base):
    __tablename__ = "mistakes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_name = Column(String, nullable=False)
    ocr_text = Column(Text, nullable=True)
    image_path = Column(String, nullable=True)
    knowledge_points = Column(String, nullable=True)  # 暂存 JSON 字符串
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="mistakes")

class StudyRecord(Base):
    __tablename__ = "study_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_name = Column(String, nullable=False)
    score = Column(Float, nullable=True)
    study_duration = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # __table_args__ = (UniqueConstraint('user_id', 'course_name'),)

    owner = relationship("User", back_populates="courses")