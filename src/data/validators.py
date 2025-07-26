#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime, time

from ..models import Operator, Task, Priority


class ValidationError(Exception):
    """Validation error exception"""
    pass


class DataValidator:
    """Data validation class for operators and tasks"""
    
    @staticmethod
    def validate_operators(operators: List[Operator]) -> List[str]:
        """
        Validate operator data
        Returns: List of error messages
        """
        errors = []
        
        if not operators:
            errors.append("No operators found")
            return errors
        
        # Check for duplicate IDs
        operator_ids = [op.operator_id for op in operators]
        duplicate_ids = DataValidator._find_duplicates(operator_ids)
        if duplicate_ids:
            errors.append(f"Duplicate operator IDs: {duplicate_ids}")
        
        # Validate individual operators
        for i, operator in enumerate(operators):
            op_errors = DataValidator._validate_single_operator(operator, i)
            errors.extend(op_errors)
        
        # Check skill consistency
        all_skills = DataValidator._collect_all_skills(operators)
        skill_warnings = DataValidator._check_skill_consistency(all_skills)
        if skill_warnings:
            errors.extend(skill_warnings)
        
        return errors
    
    @staticmethod
    def validate_tasks(tasks: List[Task]) -> List[str]:
        """
        Validate task data
        Returns: List of error messages
        """
        errors = []
        
        if not tasks:
            errors.append("No tasks found")
            return errors
        
        # Check for duplicate IDs
        task_ids = [task.task_id for task in tasks]
        duplicate_ids = DataValidator._find_duplicates(task_ids)
        if duplicate_ids:
            errors.append(f"Duplicate task IDs: {duplicate_ids}")
        
        # Validate individual tasks
        for i, task in enumerate(tasks):
            task_errors = DataValidator._validate_single_task(task, i)
            errors.extend(task_errors)
        
        return errors
    
    @staticmethod
    def validate_matching(operators: List[Operator], tasks: List[Task]) -> List[str]:
        """
        Validate operator-task matching compatibility
        Returns: List of warning messages
        """
        warnings = []
        
        # Collect all operator skills
        operator_skills = set()
        for op in operators:
            operator_skills.update(op.skill_set)
        
        # Check required skills and unmatchable tasks
        required_skills = set()
        unmatchable_tasks = []
        
        for task in tasks:
            if task.required_skill:
                required_skills.add(task.required_skill)
                # Check if any operator has this skill
                has_operator = any(op.has_skill(task.required_skill) for op in operators)
                if not has_operator:
                    unmatchable_tasks.append(f"{task.task_id} (skill: {task.required_skill})")
        
        # Report unmatchable tasks
        if unmatchable_tasks:
            warnings.append(f"Tasks with no matching operators: {unmatchable_tasks}")
        
        # Report unused skills
        unused_skills = operator_skills - required_skills
        if unused_skills:
            warnings.append(f"Unused operator skills: {unused_skills}")
        
        # Check total hours capacity
        total_task_hours = sum(task.required_hours for task in tasks)
        total_operator_hours = sum(op.get_available_hours() for op in operators)
        
        if total_task_hours > total_operator_hours:
            warnings.append(
                f"Total task hours ({total_task_hours}h) exceeds "
                f"total operator capacity ({total_operator_hours}h)"
            )
        
        return warnings
    
    @staticmethod
    def _validate_single_operator(operator: Operator, index: int) -> List[str]:
        """Validate a single operator"""
        errors = []
        prefix = f"Operator {index + 1} (ID: {operator.operator_id})"
        
        # ID validation
        if not operator.operator_id:
            errors.append(f"{prefix}: ID is empty")
        elif not operator.operator_id.strip():
            errors.append(f"{prefix}: ID is whitespace only")
        
        # Name validation
        if not operator.name:
            errors.append(f"{prefix}: Name is empty")
        elif not operator.name.strip():
            errors.append(f"{prefix}: Name is whitespace only")
        
        # Available hours validation
        if operator.available_hours[0] >= operator.available_hours[1]:
            errors.append(f"{prefix}: Start time must be before end time")
        
        hours = operator.get_available_hours()
        if hours <= 0:
            errors.append(f"{prefix}: Available hours must be positive")
        elif hours > 24:
            errors.append(f"{prefix}: Available hours cannot exceed 24 hours")
        
        # Skills validation
        if not operator.skill_set:
            errors.append(f"{prefix}: No skills specified")
        
        return errors
    
    @staticmethod
    def _validate_single_task(task: Task, index: int) -> List[str]:
        """Validate a single task"""
        errors = []
        prefix = f"Task {index + 1} (ID: {task.task_id})"
        
        # ID validation
        if not task.task_id:
            errors.append(f"{prefix}: ID is empty")
        elif not task.task_id.strip():
            errors.append(f"{prefix}: ID is whitespace only")
        
        # Name validation
        if not task.name:
            errors.append(f"{prefix}: Name is empty")
        elif not task.name.strip():
            errors.append(f"{prefix}: Name is whitespace only")
        
        # Task type validation
        if not task.task_type:
            errors.append(f"{prefix}: Task type is empty")
        
        # Required hours validation
        if task.required_hours <= 0:
            errors.append(f"{prefix}: Required hours must be positive")
        
        # Deadline validation
        if task.deadline:
            if task.deadline < datetime.now():
                errors.append(f"{prefix}: Deadline is in the past")
        
        return errors
    
    @staticmethod
    def _find_duplicates(items: List[str]) -> List[str]:
        """Find duplicate items in a list"""
        seen = set()
        duplicates = set()
        
        for item in items:
            if item in seen:
                duplicates.add(item)
            seen.add(item)
        
        return list(duplicates)
    
    @staticmethod
    def _collect_all_skills(operators: List[Operator]) -> List[str]:
        """Collect all skills from all operators"""
        all_skills = []
        for op in operators:
            all_skills.extend(op.skill_set)
        return all_skills
    
    @staticmethod
    def _check_skill_consistency(skills: List[str]) -> List[str]:
        """Check for skill naming inconsistencies"""
        warnings = []
        skill_map = {}
        
        for skill in skills:
            normalized = skill.strip().lower()
            if normalized not in skill_map:
                skill_map[normalized] = set()
            skill_map[normalized].add(skill)
        
        # Report variations of the same skill
        for normalized, variations in skill_map.items():
            if len(variations) > 1:
                warnings.append(
                    f"Skill name variations detected: {list(variations)} "
                    f"Consider standardizing these names"
                )
        
        return warnings
    
    @staticmethod
    def suggest_corrections(operators: List[Operator], tasks: List[Task]) -> Dict[str, any]:
        """Suggest data corrections"""
        suggestions = {
            "skill_normalizations": {},
            "task_type_normalizations": {},
            "warnings": []
        }
        
        # Skill normalization suggestions
        all_skills = []
        for op in operators:
            all_skills.extend(op.skill_set)
        
        skill_groups = {}
        for skill in set(all_skills):
            normalized = skill.strip().lower()
            if normalized not in skill_groups:
                skill_groups[normalized] = []
            skill_groups[normalized].append(skill)
        
        for normalized, variations in skill_groups.items():
            if len(variations) > 1:
                # Use most common variant as standard
                skill_counts = {s: all_skills.count(s) for s in variations}
                standard = max(skill_counts, key=skill_counts.get)
                
                for variant in variations:
                    if variant != standard:
                        suggestions["skill_normalizations"][variant] = standard
        
        # Task type normalization suggestions
        task_types = [task.task_type for task in tasks]
        type_groups = {}
        for task_type in set(task_types):
            normalized = task_type.strip().lower()
            if normalized not in type_groups:
                type_groups[normalized] = []
            type_groups[normalized].append(task_type)
        
        for normalized, variations in type_groups.items():
            if len(variations) > 1:
                type_counts = {t: task_types.count(t) for t in variations}
                standard = max(type_counts, key=type_counts.get)
                
                for variant in variations:
                    if variant != standard:
                        suggestions["task_type_normalizations"][variant] = standard
        
        return suggestions