"""
SQLite存储模块 - 历史记录
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List, Dict, Any, Optional
import json

from config import DB_PATH


Base = declarative_base()


class TaskRecord(Base):
    """任务记录"""
    __tablename__ = "task_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(String(50), nullable=False)  # template / sample
    input_file = Column(String(500))  # 输入文件名
    output_file = Column(String(500))  # 输出文件名
    rules_applied = Column(Text)  # 应用的规则JSON
    status = Column(String(20), default="pending")  # pending / success / failed
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_type": self.task_type,
            "input_file": self.input_file,
            "output_file": self.output_file,
            "rules_applied": json.loads(self.rules_applied) if self.rules_applied else {},
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Storage:
    """存储管理器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def create_task(self, task_type: str, input_file: str = None) -> int:
        """创建新任务"""
        session = self.Session()
        try:
            task = TaskRecord(
                task_type=task_type,
                input_file=input_file,
                status="pending"
            )
            session.add(task)
            session.commit()
            return task.id
        finally:
            session.close()
    
    def update_task(self, task_id: int, **kwargs):
        """更新任务"""
        session = self.Session()
        try:
            task = session.query(TaskRecord).filter_by(id=task_id).first()
            if task:
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        if key == "rules_applied" and isinstance(value, dict):
                            setattr(task, key, json.dumps(value, ensure_ascii=False))
                        else:
                            setattr(task, key, value)
                session.commit()
        finally:
            session.close()
    
    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """获取任务"""
        session = self.Session()
        try:
            task = session.query(TaskRecord).filter_by(id=task_id).first()
            return task.to_dict() if task else None
        finally:
            session.close()
    
    def list_tasks(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """列出任务"""
        session = self.Session()
        try:
            tasks = session.query(TaskRecord)\
                .order_by(TaskRecord.created_at.desc())\
                .limit(limit)\
                .offset(offset)\
                .all()
            return [t.to_dict() for t in tasks]
        finally:
            session.close()
    
    def delete_task(self, task_id: int) -> bool:
        """删除任务"""
        session = self.Session()
        try:
            task = session.query(TaskRecord).filter_by(id=task_id).first()
            if task:
                session.delete(task)
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        session = self.Session()
        try:
            total = session.query(TaskRecord).count()
            success = session.query(TaskRecord).filter_by(status="success").count()
            failed = session.query(TaskRecord).filter_by(status="failed").count()
            pending = session.query(TaskRecord).filter_by(status="pending").count()
            
            return {
                "total": total,
                "success": success,
                "failed": failed,
                "pending": pending,
                "success_rate": f"{(success/total*100):.1f}%" if total > 0 else "0%"
            }
        finally:
            session.close()


# 全局存储实例
_storage: Optional[Storage] = None


def get_storage() -> Storage:
    """获取存储实例"""
    global _storage
    if _storage is None:
        _storage = Storage()
    return _storage
