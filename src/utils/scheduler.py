#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
from typing import List, Dict, Optional, Type, Any
from enum import Enum
import logging

from ..models import Operator, Task, ScheduleResult, ScheduleComparison, AlgorithmType
from ..algorithms.base import OptimizationAlgorithm
from ..algorithms.linear_programming import LinearProgrammingOptimizer


class SchedulerStatus(Enum):
    """Scheduler status enumeration"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


class JobScheduler:
    """Job scheduler that manages multiple optimization algorithms"""
    
    def __init__(self):
        self.operators: List[Operator] = []
        self.tasks: List[Task] = []
        self.status = SchedulerStatus.IDLE
        self.current_algorithm: Optional[OptimizationAlgorithm] = None
        self.results: Dict[AlgorithmType, ScheduleResult] = {}
        self.execution_log: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
        
        # Algorithm class mapping
        self.algorithm_classes = {
            AlgorithmType.LINEAR_PROGRAMMING: LinearProgrammingOptimizer
        }
    
    def set_data(self, operators: List[Operator], tasks: List[Task]) -> None:
        """Set operator and task data"""
        self.operators = operators
        self.tasks = tasks
        self.logger.info(f"Data set: {len(operators)} operators, {len(tasks)} tasks")
    
    def run_algorithm(self, algorithm_type: AlgorithmType, **kwargs) -> ScheduleResult:
        """Run a specific optimization algorithm"""
        if not self.operators or not self.tasks:
            raise ValueError("No data set. Please set operators and tasks first.")
        
        if algorithm_type not in self.algorithm_classes:
            raise ValueError(f"Unsupported algorithm type: {algorithm_type}")
        
        self.status = SchedulerStatus.RUNNING
        self.current_algorithm = None
        
        start_time = time.time()
        
        try:
            # Create algorithm instance
            algorithm_class = self.algorithm_classes[algorithm_type]
            algorithm = algorithm_class()
            self.current_algorithm = algorithm
            
            self.logger.info(f"Starting {algorithm_type.value} algorithm")
            
            # Setup and run optimization
            algorithm.setup(self.operators, self.tasks)
            result = algorithm.run()
            
            # Record execution time
            execution_time = time.time() - start_time
            result.execution_time_seconds = execution_time
            
            # Store result
            self.results[algorithm_type] = result
            
            # Log execution
            self.execution_log.append({
                "algorithm": algorithm_type.value,
                "timestamp": time.time(),
                "execution_time": execution_time,
                "status": "success",
                "assignments_count": len(result.assignments),
                "parameters": kwargs
            })
            
            self.status = SchedulerStatus.COMPLETED
            self.logger.info(f"Algorithm {algorithm_type.value} completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Log error
            self.execution_log.append({
                "algorithm": algorithm_type.value,
                "timestamp": time.time(),
                "execution_time": execution_time,
                "status": "error",
                "error": str(e),
                "parameters": kwargs
            })
            
            self.status = SchedulerStatus.ERROR
            self.logger.error(f"Algorithm {algorithm_type.value} failed: {str(e)}")
            
            raise
        
        finally:
            self.current_algorithm = None
    
    def run_all_algorithms(self, **kwargs) -> Dict[AlgorithmType, ScheduleResult]:
        """Run all available algorithms (currently only Linear Programming)"""
        results = {}
        
        # Only run Linear Programming
        try:
            result = self.run_algorithm(AlgorithmType.LINEAR_PROGRAMMING, **kwargs)
            results[AlgorithmType.LINEAR_PROGRAMMING] = result
        except Exception as e:
            self.logger.warning(f"Algorithm {AlgorithmType.LINEAR_PROGRAMMING.value} failed: {str(e)}")
        
        return results
    
    def get_results(self) -> Dict[AlgorithmType, ScheduleResult]:
        """Get all stored results"""
        return self.results.copy()
    
    def get_result(self, algorithm_type: AlgorithmType) -> Optional[ScheduleResult]:
        """Get result for a specific algorithm"""
        return self.results.get(algorithm_type)
    
    def clear_results(self) -> None:
        """Clear all stored results"""
        self.results.clear()
        self.execution_log.clear()
        self.logger.info("Results cleared")
    
    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get execution log"""
        return self.execution_log.copy()
    
    def get_status(self) -> SchedulerStatus:
        """Get current scheduler status"""
        return self.status
    
    def is_running(self) -> bool:
        """Check if scheduler is currently running"""
        return self.status == SchedulerStatus.RUNNING
    
    def compare_results(self, algorithm_types: List[AlgorithmType] = None) -> ScheduleComparison:
        """Compare results from multiple algorithms"""
        if algorithm_types is None:
            algorithm_types = list(self.results.keys())
        
        comparison_results = {}
        for algo_type in algorithm_types:
            if algo_type in self.results:
                comparison_results[algo_type] = self.results[algo_type]
        
        if not comparison_results:
            raise ValueError("No results available for comparison")
        
        return ScheduleComparison(comparison_results, self.operators, self.tasks)
    
    def get_algorithm_info(self, algorithm_type: AlgorithmType) -> Dict[str, Any]:
        """Get information about a specific algorithm"""
        if algorithm_type not in self.algorithm_classes:
            raise ValueError(f"Unknown algorithm type: {algorithm_type}")
        
        algorithm_class = self.algorithm_classes[algorithm_type]
        
        info = {
            "name": algorithm_type.value,
            "class": algorithm_class.__name__,
            "description": getattr(algorithm_class, "__doc__", "No description available"),
            "supported_parameters": getattr(algorithm_class, "SUPPORTED_PARAMETERS", [])
        }
        
        return info
    
    def get_all_algorithms_info(self) -> Dict[AlgorithmType, Dict[str, Any]]:
        """Get information about all available algorithms"""
        info = {}
        # Only include Linear Programming
        info[AlgorithmType.LINEAR_PROGRAMMING] = self.get_algorithm_info(AlgorithmType.LINEAR_PROGRAMMING)
        return info
    
    def validate_data(self) -> Dict[str, List[str]]:
        """Validate operator and task data"""
        from ..data.validators import DataValidator
        
        validation_results = {
            "operator_errors": [],
            "task_errors": [],
            "matching_warnings": []
        }
        
        if self.operators:
            validation_results["operator_errors"] = DataValidator.validate_operators(self.operators)
        
        if self.tasks:
            validation_results["task_errors"] = DataValidator.validate_tasks(self.tasks)
        
        if self.operators and self.tasks:
            validation_results["matching_warnings"] = DataValidator.validate_matching(
                self.operators, self.tasks
            )
        
        return validation_results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        stats = {
            "operators_count": len(self.operators),
            "tasks_count": len(self.tasks),
            "results_count": len(self.results),
            "executions_count": len(self.execution_log),
            "status": self.status.value
        }
        
        if self.operators:
            total_operator_hours = sum(op.get_available_hours() for op in self.operators)
            stats["total_operator_hours"] = total_operator_hours
            stats["average_operator_hours"] = total_operator_hours / len(self.operators)
        
        if self.tasks:
            total_task_hours = sum(task.required_hours for task in self.tasks)
            stats["total_task_hours"] = total_task_hours
            stats["average_task_hours"] = total_task_hours / len(self.tasks)
        
        if self.execution_log:
            successful_runs = [log for log in self.execution_log if log["status"] == "success"]
            stats["success_rate"] = len(successful_runs) / len(self.execution_log)
            
            if successful_runs:
                execution_times = [log["execution_time"] for log in successful_runs]
                stats["average_execution_time"] = sum(execution_times) / len(execution_times)
                stats["fastest_execution_time"] = min(execution_times)
                stats["slowest_execution_time"] = max(execution_times)
        
        return stats