#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
import random

from .base import OptimizationAlgorithm
from ..models import AlgorithmType, ScheduleResult


class DeferredAcceptanceOptimizer(OptimizationAlgorithm):
    """Deferred Acceptance (Gale-Shapley) algorithm for task-operator matching"""
    
    def __init__(self, max_iterations=1000):
        super().__init__(AlgorithmType.DEFERRED_ACCEPTANCE)
        self.max_iterations = max_iterations
        self.matching_history = []
    
    def _optimize(self) -> ScheduleResult:
        """Run deferred acceptance algorithm"""
        # Create preference lists
        task_preferences = self._create_task_preferences()
        operator_preferences = self._create_operator_preferences()
        
        # Run deferred acceptance algorithm
        matches = self._deferred_acceptance(task_preferences, operator_preferences)
        
        # Convert matches to schedule result
        result = self._create_schedule_result(matches)
        
        return result
    
    def _create_task_preferences(self) -> Dict[str, List[str]]:
        """Create preference lists for tasks over operators"""
        task_preferences = {}
        
        for task in self.tasks:
            # Get all compatible operators
            compatible_operators = [
                op for op in self.operators 
                if self.can_assign(op.operator_id, task.task_id)
            ]
            
            # Sort operators by preference score
            operator_scores = []
            for operator in compatible_operators:
                score = self._calculate_task_operator_preference(task, operator)
                operator_scores.append((operator.operator_id, score))
            
            # Sort by score (descending)
            operator_scores.sort(key=lambda x: x[1], reverse=True)
            
            task_preferences[task.task_id] = [op_id for op_id, _ in operator_scores]
        
        return task_preferences
    
    def _create_operator_preferences(self) -> Dict[str, List[str]]:
        """Create preference lists for operators over tasks"""
        operator_preferences = {}
        
        for operator in self.operators:
            # Get all compatible tasks
            compatible_tasks = [
                task for task in self.tasks
                if self.can_assign(operator.operator_id, task.task_id)
            ]
            
            # Sort tasks by preference score
            task_scores = []
            for task in compatible_tasks:
                score = self._calculate_operator_task_preference(operator, task)
                task_scores.append((task.task_id, score))
            
            # Sort by score (descending)
            task_scores.sort(key=lambda x: x[1], reverse=True)
            
            operator_preferences[operator.operator_id] = [task_id for task_id, _ in task_scores]
        
        return operator_preferences
    
    def _calculate_task_operator_preference(self, task, operator) -> float:
        """Calculate how much a task prefers an operator"""
        score = 0.0
        
        # Prefer operators with more available hours
        available_hours = operator.get_available_hours()
        score += available_hours * 0.1
        
        # Prefer operators with exact skill match
        if hasattr(task, 'required_skill') and hasattr(operator, 'skill_set'):
            if task.required_skill in operator.skill_set:
                score += 10.0
        
        # Add some randomness to break ties
        score += random.random() * 0.01
        
        return score
    
    def _calculate_operator_task_preference(self, operator, task) -> float:
        """Calculate how much an operator prefers a task"""
        score = 0.0
        
        # Prefer higher priority tasks
        score += self.calculate_priority_score(task)
        
        # Prefer tasks that fit well within available hours
        available_hours = operator.get_available_hours()
        if task.required_hours <= available_hours:
            score += (available_hours - task.required_hours) * 0.1
        
        # Add some randomness to break ties
        score += random.random() * 0.01
        
        return score
    
    def _deferred_acceptance(self, task_preferences: Dict[str, List[str]], 
                           operator_preferences: Dict[str, List[str]]) -> Dict[str, str]:
        """Run the deferred acceptance algorithm"""
        # Initialize
        matches = {}  # operator_id -> task_id
        task_proposals = defaultdict(int)  # task_id -> number of proposals made
        rejected_by = defaultdict(set)  # task_id -> set of operators who rejected it
        
        # Keep track of free tasks (tasks proposing side)
        free_tasks = set(task_preferences.keys())
        
        iteration = 0
        while free_tasks and iteration < self.max_iterations:
            iteration += 1
            
            # Each free task proposes to its most preferred operator who hasn't rejected it
            current_proposals = {}  # operator_id -> task_id
            
            for task_id in list(free_tasks):
                if task_id not in task_preferences or not task_preferences[task_id]:
                    free_tasks.remove(task_id)
                    continue
                
                # Find the most preferred operator who hasn't rejected this task
                preferred_operator = None
                for operator_id in task_preferences[task_id]:
                    if operator_id not in rejected_by[task_id]:
                        preferred_operator = operator_id
                        break
                
                if preferred_operator is None:
                    # No more operators to propose to
                    free_tasks.remove(task_id)
                    continue
                
                # Make proposal
                if preferred_operator in current_proposals:
                    # Operator already has a proposal, need to choose better one
                    competing_task = current_proposals[preferred_operator]
                    if self._operator_prefers_task(preferred_operator, task_id, competing_task, operator_preferences):
                        # Reject the competing task
                        rejected_by[competing_task].add(preferred_operator)
                        free_tasks.add(competing_task)
                        current_proposals[preferred_operator] = task_id
                    else:
                        # Reject current task
                        rejected_by[task_id].add(preferred_operator)
                else:
                    current_proposals[preferred_operator] = task_id
            
            # Update matches and remove accepted tasks from free list
            for operator_id, task_id in current_proposals.items():
                if operator_id in matches:
                    # Operator was previously matched, reject old task
                    old_task = matches[operator_id]
                    if old_task != task_id:
                        rejected_by[old_task].add(operator_id)
                        free_tasks.add(old_task)
                
                matches[operator_id] = task_id
                free_tasks.discard(task_id)
        
        # Return task -> operator mapping (reverse of matches)
        task_operator_matches = {}
        for operator_id, task_id in matches.items():
            task_operator_matches[task_id] = operator_id
        
        return task_operator_matches
    
    def _operator_prefers_task(self, operator_id: str, task1_id: str, task2_id: str, 
                              operator_preferences: Dict[str, List[str]]) -> bool:
        """Check if operator prefers task1 over task2"""
        if operator_id not in operator_preferences:
            return False
        
        prefs = operator_preferences[operator_id]
        
        task1_index = len(prefs)  # Default to end if not found
        task2_index = len(prefs)  # Default to end if not found
        
        try:
            task1_index = prefs.index(task1_id)
        except ValueError:
            pass
        
        try:
            task2_index = prefs.index(task2_id)
        except ValueError:
            pass
        
        # Lower index means higher preference
        return task1_index < task2_index
    
    def _create_schedule_result(self, matches: Dict[str, str]) -> ScheduleResult:
        """Convert matches to schedule result with time assignments"""
        result = ScheduleResult(algorithm_type=self.algorithm_type)
        
        # Track operator schedules for time assignment
        operator_schedules = {}
        for operator in self.operators:
            work_start = operator.available_hours[0].hour
            work_end = operator.available_hours[1].hour
            operator_schedules[operator.operator_id] = [(work_start, work_end)]
        
        # Sort matched tasks by priority for time assignment
        matched_tasks = []
        for task_id, operator_id in matches.items():
            task = next(t for t in self.tasks if t.task_id == task_id)
            matched_tasks.append((task, operator_id))
        
        matched_tasks.sort(key=lambda x: self.calculate_priority_score(x[0]), reverse=True)
        
        # Assign time slots
        for task, operator_id in matched_tasks:
            operator = next(op for op in self.operators if op.operator_id == operator_id)
            
            # Find available time slot
            start_hour = self._find_time_slot(operator_schedules[operator_id], task.required_hours)
            
            if start_hour is not None:
                # Add assignment
                result.add_assignment(
                    operator_id=operator_id,
                    task_id=task.task_id,
                    start_hour=start_hour,
                    duration_hours=task.required_hours
                )
                
                # Update operator schedule
                end_hour = start_hour + task.required_hours
                self._update_schedule(operator_schedules[operator_id], start_hour, end_hour)
        
        return result
    
    def _find_time_slot(self, schedule: List[Tuple[int, int]], duration: int) -> Optional[int]:
        """Find first available time slot of given duration"""
        for start_time, end_time in schedule:
            if end_time - start_time >= duration:
                return start_time
        return None
    
    def _update_schedule(self, schedule: List[Tuple[int, int]], start_hour: int, end_hour: int):
        """Update schedule by removing used time slot"""
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
    
    def get_algorithm_parameters(self) -> Dict[str, any]:
        """Get algorithm parameters"""
        return {
            "algorithm": "Deferred Acceptance (Gale-Shapley)",
            "max_iterations": self.max_iterations,
            "strategy": "Two-sided matching with task preferences over operators",
            "preference_factors": [
                "Task priority",
                "Operator availability", 
                "Skill compatibility",
                "Time slot fitting"
            ]
        }