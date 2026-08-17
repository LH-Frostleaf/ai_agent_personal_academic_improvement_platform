from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
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
    knowledge_points = Column(JSON, nullable=True)
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

    owner = relationship("User", back_populates="courses")

class DiagnosisReport(Base):
    __tablename__ = "diagnosis_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    report_summary = Column(Text)
    weak_points = Column(Text)  # JSON 字符串
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    icon = Column(String(50), nullable=True)
    sort_order = Column(Integer, default=0)

class KnowledgePoint(Base):
    __tablename__ = "knowledge_points"

    id = Column(Integer, primary_key=True, index=True)
    kp_id = Column(String(50), unique=True, nullable=False, index=True)  # 与向量库保持一致
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    parent_kp_id = Column(String(50), nullable=True)  # 父知识点ID（可选，用于层级）

    # 关联关系
    subject = relationship("Subject", backref="knowledge_points")

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_point_id = Column(Integer, ForeignKey("knowledge_points.id"), nullable=False)
    title = Column(String(200), nullable=False)
    type = Column(String(20), nullable=False)  # video / article / exercise / course
    url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    difficulty = Column(Integer, default=2)  # 1-5
    source = Column(String(50), nullable=True)  # B站 / 慕课 / 自建
    created_at = Column(DateTime(timezone=True), server_default=func.now())