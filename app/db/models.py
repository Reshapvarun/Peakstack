from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # User-specific analyses
    analyses = relationship("AnalysisRecord", back_populates="owner")

class AnalysisRecord(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Status and progress
    status = Column(String, default="pending") # pending, processing, completed, failed
    error_message = Column(String, nullable=True)
    
    # Metadata
    analysis_name = Column(String)
    csv_file_id = Column(String)
    
    # Result storage (JSON)
    results = Column(JSON)
    inputs = Column(JSON)

    owner = relationship("User", back_populates="analyses")
