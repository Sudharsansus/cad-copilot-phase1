# database.py - Database Models and Queries
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
from app.config import DATABASE_URL
from app.utils.helpers import log_info, log_error

Base = declarative_base()

# Models
class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True)
    filename = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Geometry(Base):
    __tablename__ = "geometries"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36))
    type = Column(String(50))
    data = Column(JSON)
    layer_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

class Command(Base):
    __tablename__ = "commands"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36))
    command_text = Column(String(500))
    operation = Column(String(50))
    parameters = Column(JSON)
    success = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ValidationLog(Base):
    __tablename__ = "validation_logs"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36))
    check_type = Column(String(50))
    passed = Column(Boolean, default=True)
    details = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

# Database Connection
class Database:
    def __init__(self):
        try:
            self.engine = create_engine(DATABASE_URL)
            self.SessionLocal = sessionmaker(bind=self.engine)
            Base.metadata.create_all(self.engine)
            log_info("Database connected successfully")
        except Exception as e:
            log_error("Database connection failed", e)
    
    def get_session(self):
        return self.SessionLocal()
    
    def save_project(self, project_id: str, filename: str):
        """Save project to database"""
        try:
            session = self.get_session()
            project = Project(id=project_id, filename=filename)
            session.add(project)
            session.commit()
            session.close()
            log_info(f"Project saved: {project_id}")
        except Exception as e:
            log_error("Save project failed", e)
    
    def save_geometry(self, geom_id: str, project_id: str, geom_type: str, data: dict, layer: str):
        """Save geometry to database"""
        try:
            session = self.get_session()
            geometry = Geometry(
                id=geom_id,
                project_id=project_id,
                type=geom_type,
                data=data,
                layer_name=layer
            )
            session.add(geometry)
            session.commit()
            session.close()
        except Exception as e:
            log_error("Save geometry failed", e)
    
    def get_geometries(self, project_id: str):
        """Get all geometries for project"""
        try:
            session = self.get_session()
            geometries = session.query(Geometry).filter_by(project_id=project_id).all()
            result = [{
                "id": g.id,
                "type": g.type,
                "data": g.data,
                "layer": g.layer_name
            } for g in geometries]
            session.close()
            return result
        except Exception as e:
            log_error("Get geometries failed", e)
            return []
    
    def save_command(self, cmd_id: str, project_id: str, cmd_text: str, operation: str, params: dict, success: bool):
        """Save command to database"""
        try:
            session = self.get_session()
            command = Command(
                id=cmd_id,
                project_id=project_id,
                command_text=cmd_text,
                operation=operation,
                parameters=params,
                success=success
            )
            session.add(command)
            session.commit()
            session.close()
        except Exception as e:
            log_error("Save command failed", e)
    
    def save_validation_log(self, log_id: str, project_id: str, check_type: str, passed: bool, details: str):
        """Save validation result"""
        try:
            session = self.get_session()
            log = ValidationLog(
                id=log_id,
                project_id=project_id,
                check_type=check_type,
                passed=passed,
                details=details
            )
            session.add(log)
            session.commit()
            session.close()
        except Exception as e:
            log_error("Save validation log failed", e)

# Global instance
db = Database()
