#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import random
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

from .base import OptimizationAlgorithm
from ..models import AlgorithmType, ScheduleResult, Assignment


class HeuristicOptimizer(OptimizationAlgorithm):
    """Heuristic optimization algorithm using greedy approach with local improvement"""
    
    def __init__(self, improvement_iterations=100):
        super().__init__(AlgorithmType.HEURISTIC)
        self.improvement_iterations = improvement_iterations
        self.assignment_history = []
    
    def _optimize(self) -> ScheduleResult:
        """Run heuristic optimization"""
        # Initial greedy assignment
        result = self._greedy_assignment()
        
        # Local improvement
        result = self._improve_solution(result)
        
        return result
    
    def _greedy_assignment(self) -> ScheduleResult:
        """Greedy assignment algorithm"""
        result = ScheduleResult(algorithm_type=self.algorithm_type)
        
        # Sort tasks by priority
        sorted_tasks = sorted(self.tasks, key=self.calculate_priority_score, reverse=True)
        
        # Initialize operator schedules with their available hours
        operator_schedules = {}
        for operator in self.operators:
            work_start = operator.available_hours[0].hour
            work_end = operator.available_hours[1].hour
            operator_schedules[operator.operator_id] = [(work_start, work_end)]
        
        # Assign tasks greedily
        for task in sorted_tasks:
            best_assignment = self._find_best_assignment(task, operator_schedules)
            
            if best_assignment:
                operator_id, start_hour = best_assignment
                
                # Add assignment
                result.add_assignment(
                    operator_id=operator_id,
                    task_id=task.task_id,
                    start_hour=start_hour,
                    duration_hours=task.required_hours
                )
                
                # Update operator schedule
                end_hour = start_hour + task.required_hours
                self._update_operator_schedule(operator_schedules[operator_id], start_hour, end_hour)
        
        return result
    
    def _find_best_assignment(self, task, operator_schedules: Dict) -> Optional[Tuple[str, int]]:
        """Find the best operator and time slot for a task"""
        best_operator = None
        best_start_hour = None
        best_score = -1
        
        for operator in self.operators:
            # Check skill compatibility
            if not self.can_assign(operator.operator_id, task.task_id):
                continue
            
            # Find available time slots
            available_slots = self._find_available_slots(
                operator_schedules[operator.operator_id], 
                task.required_hours
            )
            
            for start_hour in available_slots:
                # Calculate assignment score
                score = self._calculate_assignment_score(operator, task, start_hour)
                
                if score > best_score:
                    best_score = score
                    best_operator = operator.operator_id
                    best_start_hour = start_hour
        
        if best_operator:
            return (best_operator, best_start_hour)
        return None
    
    def _find_available_slots(self, schedule: List[Tuple[int, int]], duration: int) -> List[int]:
        """Find available time slots in an operator's schedule"""
        available_slots = []
        
        # Sort schedule by start time
        sorted_schedule = sorted(schedule)
        
        for i in range(len(sorted_schedule) - 1):
            current_end = sorted_schedule[i][1]
            next_start = sorted_schedule[i + 1][0]
            
            # Check if there's enough time between current and next
            if next_start - current_end >= duration:
                # Add all possible start times in this gap
                for start_hour in range(current_end, next_start - duration + 1):
                    available_slots.append(start_hour)
        
        return available_slots
    
    def _calculate_assignment_score(self, operator, task, start_hour: int) -> float:
        """Calculate score for assigning task to operator at specific time"""
        score = 0.0
        
        # Base score from task priority
        score += self.calculate_priority_score(task)
        
        # Prefer earlier start times (to leave flexibility for later tasks)
        score += (17 - start_hour) * 0.1
        
        # Prefer operators with more available hours
        available_hours = operator.get_available_hours()
        score += available_hours * 0.05
        
        return score
    
    def _update_operator_schedule(self, schedule: List[Tuple[int, int]], start_hour: int, end_hour: int):
        """Update operator schedule with new assignment"""
        # Remove the time slot that was used
        new_schedule = []
        
        for slot_start, slot_end in schedule:
            if start_hour >= slot_start and end_hour <= slot_end:
                # Split the slot
                if start_hour > slot_start:
                    new_schedule.append((slot_start, start_hour))
                if end_hour < slot_end:
                    new_schedule.append((end_hour, slot_end))
            else:
                new_schedule.append((slot_start, slot_end))
        
        schedule.clear()
        schedule.extend(new_schedule)
    
    def _improve_solution(self, result: ScheduleResult) -> ScheduleResult:
        """Apply local improvement to the solution"""
        best_result = result
        best_score = self._evaluate_solution(result)
        
        for iteration in range(self.improvement_iterations):
            # Try different improvement strategies
            improved_result = self._try_improvements(best_result)
            
            if improved_result:
                improved_score = self._evaluate_solution(improved_result)
                
                if improved_score > best_score:
                    best_result = improved_result
                    best_score = improved_score
        
        return best_result
    
    def _try_improvements(self, result: ScheduleResult) -> Optional[ScheduleResult]:
        """Try various improvement strategies"""
        if not result.assignments:
            return None
        
        # Strategy 1: Swap two random assignments
        if len(result.assignments) >= 2:
            improved = self._try_swap_assignments(result)
            if improved:
                return improved
        
        # Strategy 2: Move assignment to different time
        improved = self._try_move_assignment(result)
        if improved:
            return improved
        
        # Strategy 3: Reassign task to different operator
        improved = self._try_reassign_task(result)
        if improved:
            return improved
        
        return None
    
    def _try_swap_assignments(self, result: ScheduleResult) -> Optional[ScheduleResult]:
        """Try swapping two assignments"""
        assignments = result.assignments.copy()
        
        if len(assignments) < 2:
            return None
        
        # Pick two random assignments
        idx1, idx2 = random.sample(range(len(assignments)), 2)
        assignment1 = assignments[idx1]
        assignment2 = assignments[idx2]
        
        # Try swapping operators
        new_assignment1 = Assignment(
            operator_id=assignment2.operator_id,
            task_id=assignment1.task_id,
            start_hour=assignment1.start_hour,
            duration_hours=assignment1.duration_hours
        )
        
        new_assignment2 = Assignment(
            operator_id=assignment1.operator_id,
            task_id=assignment2.task_id,
            start_hour=assignment2.start_hour,
            duration_hours=assignment2.duration_hours
        )
        
        # Create new result
        new_result = ScheduleResult(algorithm_type=self.algorithm_type)
        
        for i, assignment in enumerate(assignments):
            if i == idx1:
                if self._is_valid_assignment(new_assignment1, assignments, idx1):
                    new_result.assignments.append(new_assignment1)
                else:
                    return None
            elif i == idx2:
                if self._is_valid_assignment(new_assignment2, assignments, idx2):
                    new_result.assignments.append(new_assignment2)
                else:
                    return None
            else:
                new_result.assignments.append(assignment)
        
        return new_result
    
    def _try_move_assignment(self, result: ScheduleResult) -> Optional[ScheduleResult]:
        """Try moving an assignment to a different time"""
        if not result.assignments:
            return None
        
        # Pick random assignment
        assignment = random.choice(result.assignments)
        
        # Find operator
        operator = next(op for op in self.operators if op.operator_id == assignment.operator_id)
        
        # Try different start times
        work_start = operator.available_hours[0].hour
        work_end = operator.available_hours[1].hour
        
        for new_start_hour in range(work_start, work_end - assignment.duration_hours + 1):
            if new_start_hour == assignment.start_hour:
                continue
            
            new_assignment = Assignment(
                operator_id=assignment.operator_id,
                task_id=assignment.task_id,
                start_hour=new_start_hour,
                duration_hours=assignment.duration_hours
            )
            
            # Check if this new time is valid
            other_assignments = [a for a in result.assignments if a != assignment]
            if self._is_valid_assignment(new_assignment, other_assignments):
                # Create new result
                new_result = ScheduleResult(algorithm_type=self.algorithm_type)
                for a in other_assignments:
                    new_result.assignments.append(a)
                new_result.assignments.append(new_assignment)
                return new_result
        
        return None
    
    def _try_reassign_task(self, result: ScheduleResult) -> Optional[ScheduleResult]:
        """Try reassigning a task to a different operator"""
        if not result.assignments:
            return None
        
        # Pick random assignment
        assignment = random.choice(result.assignments)
        
        # Find task
        task = next(t for t in self.tasks if t.task_id == assignment.task_id)
        
        # Try different operators
        for operator in self.operators:
            if operator.operator_id == assignment.operator_id:
                continue
            
            if not self.can_assign(operator.operator_id, task.task_id):
                continue
            
            # Try different start times for this operator
            work_start = operator.available_hours[0].hour
            work_end = operator.available_hours[1].hour
            
            for start_hour in range(work_start, work_end - task.required_hours + 1):
                new_assignment = Assignment(
                    operator_id=operator.operator_id,
                    task_id=task.task_id,
                    start_hour=start_hour,
                    duration_hours=task.required_hours
                )
                
                # Check if this is valid
                other_assignments = [a for a in result.assignments if a != assignment]
                if self._is_valid_assignment(new_assignment, other_assignments):
                    # Create new result
                    new_result = ScheduleResult(algorithm_type=self.algorithm_type)
                    for a in other_assignments:
                        new_result.assignments.append(a)
                    new_result.assignments.append(new_assignment)
                    return new_result
        
        return None
    
    def _is_valid_assignment(self, assignment: Assignment, other_assignments: List[Assignment], skip_index: int = -1) -> bool:
        """Check if an assignment is valid given other assignments"""
        # Check for time conflicts with same operator
        for i, other in enumerate(other_assignments):
            if skip_index >= 0 and i == skip_index:
                continue
            
            if other.operator_id == assignment.operator_id:
                # Check for time overlap
                end_hour = assignment.start_hour + assignment.duration_hours
                other_end_hour = other.start_hour + other.duration_hours
                
                if not (end_hour <= other.start_hour or assignment.start_hour >= other_end_hour):
                    return False
        
        return True
    
    def _evaluate_solution(self, result: ScheduleResult) -> float:
        """Evaluate solution quality"""
        if not result.assignments:
            return 0.0
        
        score = 0.0
        
        # Score based on number of assignments
        score += len(result.assignments) * 10.0
        
        # Score based on task priorities
        for assignment in result.assignments:
            task = next(t for t in self.tasks if t.task_id == assignment.task_id)
            score += self.calculate_priority_score(task)
        
        # Penalty for operator overload
        operator_hours = defaultdict(int)
        for assignment in result.assignments:
            operator_hours[assignment.operator_id] += assignment.duration_hours
        
        for operator_id, hours in operator_hours.items():
            operator = next(op for op in self.operators if op.operator_id == operator_id)
            max_hours = operator.get_available_hours()
            if hours > max_hours:
                score -= (hours - max_hours) * 20.0
        
        return score
    
    def get_algorithm_parameters(self) -> Dict[str, any]:
        """Get algorithm parameters"""
        return {
            "algorithm": "Heuristic Algorithm",
            "improvement_iterations": self.improvement_iterations,
            "strategy": "Greedy assignment with local improvement",
            "improvement_methods": [
                "Assignment swapping",
                "Time slot adjustment", 
                "Operator reassignment"
            ]
        }