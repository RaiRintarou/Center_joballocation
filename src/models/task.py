from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
    
    @classmethod
    def from_string(cls, value: str) -> "Priority":
        mapping = {
            "low": cls.LOW,
            "medium": cls.MEDIUM,
            "high": cls.HIGH,
            "urgent": cls.URGENT
        }
        return mapping.get(value.lower(), cls.MEDIUM)


@dataclass
class Task:
    task_id: str
    name: str
    task_type: str
    required_hours: int
    deadline: Optional[datetime] = None
    priority: Priority = Priority.MEDIUM
    required_skill: Optional[str] = None
    
    def __post_init__(self):
        if self.required_hours < 1:
            raise ValueError("Required hours must be at least 1")
        if self.required_hours > 8:
            raise ValueError("Required hours cannot exceed 8 (one working day)")
        
        if isinstance(self.priority, str):
            self.priority = Priority.from_string(self.priority)
    
    def get_priority_value(self) -> int:
        return self.priority.value
    
    def is_urgent(self) -> bool:
        return self.priority == Priority.URGENT
    
    def has_deadline(self) -> bool:
        return self.deadline is not None
    
    def days_until_deadline(self, from_date: datetime = None) -> Optional[int]:
        if not self.deadline:
            return None
        
        from_date = from_date or datetime.now()
        delta = self.deadline - from_date
        return delta.days
    
    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "task_type": self.task_type,
            "required_hours": self.required_hours,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "priority": self.priority.name,
            "required_skill": self.required_skill
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        deadline = None
        if data.get("deadline"):
            deadline = datetime.fromisoformat(data["deadline"])
        
        return cls(
            task_id=data["task_id"],
            name=data["name"],
            task_type=data["task_type"],
            required_hours=int(data["required_hours"]),
            deadline=deadline,
            priority=Priority.from_string(data.get("priority", "medium")),
            required_skill=data.get("required_skill")
        )
    
    def __repr__(self) -> str:
        return f"Task(id={self.task_id}, name={self.name}, hours={self.required_hours}, priority={self.priority.name})"