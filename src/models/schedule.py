from dataclasses import dataclass, field
from datetime import datetime, time
from typing import List, Dict, Optional, Tuple
from enum import Enum


class AlgorithmType(Enum):
    LINEAR_PROGRAMMING = "linear_programming"
    CP_SAT = "cp_sat"
    GENETIC_ALGORITHM = "genetic_algorithm"
    HEURISTIC = "heuristic"
    DEFERRED_ACCEPTANCE = "deferred_acceptance"


@dataclass
class Assignment:
    operator_id: str
    task_id: str
    start_hour: int
    duration_hours: int
    
    @property
    def end_hour(self) -> int:
        return self.start_hour + self.duration_hours
    
    def get_time_slot(self) -> Tuple[int, int]:
        return (self.start_hour, self.end_hour)
    
    def to_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "task_id": self.task_id,
            "start_hour": self.start_hour,
            "duration_hours": self.duration_hours
        }


@dataclass
class ScheduleResult:
    algorithm_type: AlgorithmType
    assignments: List[Assignment] = field(default_factory=list)
    execution_time_seconds: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_assignment(self, operator_id: str, task_id: str, start_hour: int, duration_hours: int):
        assignment = Assignment(
            operator_id=operator_id,
            task_id=task_id,
            start_hour=start_hour,
            duration_hours=duration_hours
        )
        self.assignments.append(assignment)
    
    def get_assignments_by_operator(self, operator_id: str) -> List[Assignment]:
        return [a for a in self.assignments if a.operator_id == operator_id]
    
    def get_assignments_by_task(self, task_id: str) -> List[Assignment]:
        return [a for a in self.assignments if a.task_id == task_id]
    
    def get_operator_schedule(self, operator_id: str) -> List[Tuple[int, int, str]]:
        assignments = self.get_assignments_by_operator(operator_id)
        schedule = [(a.start_hour, a.end_hour, a.task_id) for a in assignments]
        return sorted(schedule, key=lambda x: x[0])
    
    def get_total_assigned_hours(self) -> int:
        return sum(a.duration_hours for a in self.assignments)
    
    def get_assigned_task_ids(self) -> set:
        return {a.task_id for a in self.assignments}
    
    def get_assigned_operator_ids(self) -> set:
        return {a.operator_id for a in self.assignments}
    
    def get_utilization_by_operator(self) -> Dict[str, int]:
        utilization = {}
        for assignment in self.assignments:
            if assignment.operator_id not in utilization:
                utilization[assignment.operator_id] = 0
            utilization[assignment.operator_id] += assignment.duration_hours
        return utilization
    
    def to_dict(self) -> dict:
        return {
            "algorithm_type": self.algorithm_type.value,
            "assignments": [a.to_dict() for a in self.assignments],
            "execution_time_seconds": self.execution_time_seconds,
            "created_at": self.created_at.isoformat(),
            "statistics": {
                "total_assigned_hours": self.get_total_assigned_hours(),
                "total_tasks_assigned": len(self.get_assigned_task_ids()),
                "total_operators_used": len(self.get_assigned_operator_ids())
            }
        }


@dataclass
class ScheduleComparison:
    results: Dict[AlgorithmType, ScheduleResult] = field(default_factory=dict)
    
    def add_result(self, result: ScheduleResult):
        self.results[result.algorithm_type] = result
    
    def get_comparison_metrics(self) -> Dict[str, Dict[str, any]]:
        metrics = {}
        
        for algo_type, result in self.results.items():
            metrics[algo_type.value] = {
                "total_assigned_hours": result.get_total_assigned_hours(),
                "total_tasks_assigned": len(result.get_assigned_task_ids()),
                "total_operators_used": len(result.get_assigned_operator_ids()),
                "execution_time_seconds": result.execution_time_seconds,
                "average_utilization": result.get_total_assigned_hours() / max(len(result.get_assigned_operator_ids()), 1)
            }
        
        return metrics
    
    def get_best_algorithm(self, metric: str = "total_assigned_hours") -> Optional[AlgorithmType]:
        if not self.results:
            return None
        
        best_algo = None
        best_value = -1
        
        for algo_type, result in self.results.items():
            if metric == "total_assigned_hours":
                value = result.get_total_assigned_hours()
            elif metric == "total_tasks_assigned":
                value = len(result.get_assigned_task_ids())
            elif metric == "execution_time_seconds":
                value = -result.execution_time_seconds
            else:
                continue
            
            if value > best_value:
                best_value = value
                best_algo = algo_type
        
        return best_algo