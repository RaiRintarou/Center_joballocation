from dataclasses import dataclass, field
from typing import List, Set, Tuple
from datetime import time


@dataclass
class Operator:
    operator_id: str
    name: str
    skill_set: Set[str] = field(default_factory=set)
    available_hours: Tuple[time, time] = field(default_factory=lambda: (time(9, 0), time(17, 0)))
    
    def __post_init__(self):
        if isinstance(self.skill_set, list):
            self.skill_set = set(self.skill_set)
    
    def has_skill(self, skill: str) -> bool:
        return skill in self.skill_set
    
    def get_available_hours_in_minutes(self) -> int:
        start_minutes = self.available_hours[0].hour * 60 + self.available_hours[0].minute
        end_minutes = self.available_hours[1].hour * 60 + self.available_hours[1].minute
        return end_minutes - start_minutes
    
    def get_available_hours(self) -> float:
        return self.get_available_hours_in_minutes() / 60.0
    
    def is_available_at(self, hour: int) -> bool:
        return self.available_hours[0].hour <= hour < self.available_hours[1].hour
    
    def to_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "name": self.name,
            "skill_set": list(self.skill_set),
            "available_hours": [
                self.available_hours[0].strftime("%H:%M"),
                self.available_hours[1].strftime("%H:%M")
            ]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Operator":
        available_hours = data.get("available_hours", ["09:00", "17:00"])
        start_time = time.fromisoformat(available_hours[0])
        end_time = time.fromisoformat(available_hours[1])
        
        return cls(
            operator_id=data["operator_id"],
            name=data["name"],
            skill_set=set(data.get("skill_set", [])),
            available_hours=(start_time, end_time)
        )
    
    def __repr__(self) -> str:
        return f"Operator(id={self.operator_id}, name={self.name}, skills={self.skill_set})"