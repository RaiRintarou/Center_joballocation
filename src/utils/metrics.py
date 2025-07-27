#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
import statistics
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, time
import numpy as np

from ..models import ScheduleResult, ScheduleComparison, Operator, Task, Assignment


@dataclass
class OperatorMetrics:
    """Operator performance metrics"""
    operator_id: str
    operator_name: str
    assigned_tasks_count: int
    total_assigned_hours: int
    available_hours: float
    utilization_rate: float  # Usage rate (0.0-1.0)
    idle_hours: float
    average_task_duration: float
    task_types: List[str]


@dataclass
class TaskMetrics:
    """Task-related metrics"""
    total_tasks: int
    assigned_tasks: int
    unassigned_tasks: int
    assignment_rate: float  # Assignment rate (0.0-1.0)
    total_required_hours: float
    total_assigned_hours: float
    average_task_duration: float
    task_type_distribution: Dict[str, int]
    priority_distribution: Dict[str, int]


@dataclass
class OverallMetrics:
    """Overall optimization metrics"""
    total_assignments: int
    overall_efficiency: float
    workload_balance: float  # Standard deviation of operator utilization rates
    constraint_violations: int
    unassigned_hours: float
    resource_utilization: float


@dataclass
class AlgorithmMetrics:
    """Algorithm-specific metrics"""
    algorithm_name: str
    execution_time_seconds: float
    operator_metrics: List[OperatorMetrics]
    task_metrics: TaskMetrics
    overall_metrics: OverallMetrics


class MetricsCalculator:
    """Calculate various performance metrics for job allocation results"""
    
    def __init__(self, operators: List[Operator], tasks: List[Task]):
        self.operators = operators
        self.tasks = tasks
        self.operator_map = {op.operator_id: op for op in operators}
        self.task_map = {task.task_id: task for task in tasks}
    
    def calculate_all_metrics(self, result: ScheduleResult) -> Dict[str, Any]:
        """Calculate all metrics for a schedule result"""
        operator_metrics = self.calculate_operator_metrics(result)
        task_metrics = self.calculate_task_metrics(result)
        overall_metrics = self.calculate_overall_metrics(result, operator_metrics)
        
        return {
            "operator_metrics": operator_metrics,
            "task_metrics": task_metrics,
            "overall_metrics": overall_metrics
        }
    
    def calculate_operator_metrics(self, result: ScheduleResult) -> List[OperatorMetrics]:
        """Calculate metrics for each operator"""
        operator_metrics = []
        
        # Group assignments by operator
        operator_assignments = defaultdict(list)
        for assignment in result.assignments:
            operator_assignments[assignment.operator_id].append(assignment)
        
        for operator in self.operators:
            assignments = operator_assignments.get(operator.operator_id, [])
            
            # Calculate metrics
            assigned_tasks_count = len(assignments)
            total_assigned_hours = sum(a.duration_hours for a in assignments)
            available_hours = operator.get_available_hours()
            utilization_rate = total_assigned_hours / available_hours if available_hours > 0 else 0.0
            idle_hours = available_hours - total_assigned_hours
            
            average_task_duration = (
                total_assigned_hours / assigned_tasks_count 
                if assigned_tasks_count > 0 else 0.0
            )
            
            # Get task types for this operator
            task_types = []
            for assignment in assignments:
                task = self.task_map.get(assignment.task_id)
                if task and task.task_type not in task_types:
                    task_types.append(task.task_type)
            
            metrics = OperatorMetrics(
                operator_id=operator.operator_id,
                operator_name=operator.name,
                assigned_tasks_count=assigned_tasks_count,
                total_assigned_hours=total_assigned_hours,
                available_hours=available_hours,
                utilization_rate=utilization_rate,
                idle_hours=idle_hours,
                average_task_duration=average_task_duration,
                task_types=task_types
            )
            
            operator_metrics.append(metrics)
        
        return operator_metrics
    
    def calculate_task_metrics(self, result: ScheduleResult) -> TaskMetrics:
        """Calculate task-related metrics"""
        total_tasks = len(self.tasks)
        assigned_tasks = len(result.assignments)
        unassigned_tasks = total_tasks - assigned_tasks
        assignment_rate = assigned_tasks / total_tasks if total_tasks > 0 else 0.0
        
        total_required_hours = sum(task.required_hours for task in self.tasks)
        total_assigned_hours = sum(a.duration_hours for a in result.assignments)
        
        average_task_duration = (
            total_assigned_hours / assigned_tasks 
            if assigned_tasks > 0 else 0.0
        )
        
        # Task type distribution
        task_type_distribution = defaultdict(int)
        priority_distribution = defaultdict(int)
        
        for task in self.tasks:
            task_type_distribution[task.task_type] += 1
            priority_distribution[task.priority.name] += 1
        
        return TaskMetrics(
            total_tasks=total_tasks,
            assigned_tasks=assigned_tasks,
            unassigned_tasks=unassigned_tasks,
            assignment_rate=assignment_rate,
            total_required_hours=total_required_hours,
            total_assigned_hours=total_assigned_hours,
            average_task_duration=average_task_duration,
            task_type_distribution=dict(task_type_distribution),
            priority_distribution=dict(priority_distribution)
        )
    
    def calculate_overall_metrics(self, result: ScheduleResult, operator_metrics: List[OperatorMetrics]) -> OverallMetrics:
        """Calculate overall optimization metrics"""
        total_assignments = len(result.assignments)
        
        # Calculate overall efficiency (percentage of required hours that were assigned)
        total_required_hours = sum(task.required_hours for task in self.tasks)
        total_assigned_hours = sum(a.duration_hours for a in result.assignments)
        overall_efficiency = total_assigned_hours / total_required_hours if total_required_hours > 0 else 0.0
        
        # Calculate workload balance (standard deviation of utilization rates)
        utilization_rates = [om.utilization_rate for om in operator_metrics]
        workload_balance = statistics.stdev(utilization_rates) if len(utilization_rates) > 1 else 0.0
        
        # Count constraint violations (simplified - could be extended)
        constraint_violations = self._count_constraint_violations(result)
        
        # Calculate unassigned hours
        unassigned_hours = total_required_hours - total_assigned_hours
        
        # Calculate resource utilization
        total_available_hours = sum(op.get_available_hours() for op in self.operators)
        resource_utilization = total_assigned_hours / total_available_hours if total_available_hours > 0 else 0.0
        
        return OverallMetrics(
            total_assignments=total_assignments,
            overall_efficiency=overall_efficiency,
            workload_balance=workload_balance,
            constraint_violations=constraint_violations,
            unassigned_hours=unassigned_hours,
            resource_utilization=resource_utilization
        )
    
    def _count_constraint_violations(self, result: ScheduleResult) -> int:
        """Count various constraint violations"""
        violations = 0
        
        # Check for time overlaps for each operator
        operator_assignments = defaultdict(list)
        for assignment in result.assignments:
            operator_assignments[assignment.operator_id].append(assignment)
        
        for operator_id, assignments in operator_assignments.items():
            # Sort assignments by start time
            assignments.sort(key=lambda a: a.start_hour)
            
            # Check for overlaps
            for i in range(len(assignments) - 1):
                current_end = assignments[i].start_hour + assignments[i].duration_hours
                next_start = assignments[i + 1].start_hour
                
                if current_end > next_start:
                    violations += 1
        
        # Check skill requirements
        for assignment in result.assignments:
            operator = self.operator_map.get(assignment.operator_id)
            task = self.task_map.get(assignment.task_id)
            
            if operator and task and task.required_skill:
                if not operator.has_skill(task.required_skill):
                    violations += 1
        
        # Check working hours constraints
        for assignment in result.assignments:
            operator = self.operator_map.get(assignment.operator_id)
            if operator:
                start_time = assignment.start_hour
                end_time = assignment.start_hour + assignment.duration_hours
                
                available_start = operator.available_hours[0].hour
                available_end = operator.available_hours[1].hour
                
                if start_time < available_start or end_time > available_end:
                    violations += 1
        
        return violations
    
    def compare_algorithms(self, results: Dict[str, ScheduleResult]) -> Dict[str, AlgorithmMetrics]:
        """Compare metrics across multiple algorithms"""
        comparison = {}
        
        for algorithm_name, result in results.items():
            metrics_data = self.calculate_all_metrics(result)
            
            algorithm_metrics = AlgorithmMetrics(
                algorithm_name=algorithm_name,
                execution_time_seconds=getattr(result, 'execution_time_seconds', 0.0),
                operator_metrics=metrics_data["operator_metrics"],
                task_metrics=metrics_data["task_metrics"],
                overall_metrics=metrics_data["overall_metrics"]
            )
            
            comparison[algorithm_name] = algorithm_metrics
        
        return comparison
    
    def generate_summary_report(self, result: ScheduleResult) -> Dict[str, Any]:
        """Generate a comprehensive summary report"""
        metrics = self.calculate_all_metrics(result)
        
        # Best and worst performing operators
        operator_metrics = metrics["operator_metrics"]
        best_utilization = max(operator_metrics, key=lambda om: om.utilization_rate, default=None)
        worst_utilization = min(operator_metrics, key=lambda om: om.utilization_rate, default=None)
        
        # Most common task types
        task_metrics = metrics["task_metrics"]
        most_common_task_type = max(
            task_metrics.task_type_distribution.items(), 
            key=lambda x: x[1], 
            default=("None", 0)
        )
        
        summary = {
            "execution_summary": {
                "total_assignments": len(result.assignments),
                "assignment_rate": f"{task_metrics.assignment_rate:.1%}",
                "overall_efficiency": f"{metrics['overall_metrics'].overall_efficiency:.1%}",
                "execution_time": f"{getattr(result, 'execution_time_seconds', 0.0):.2f}s"
            },
            "operator_performance": {
                "best_utilization": {
                    "name": best_utilization.operator_name if best_utilization else "N/A",
                    "rate": f"{best_utilization.utilization_rate:.1%}" if best_utilization else "N/A"
                },
                "worst_utilization": {
                    "name": worst_utilization.operator_name if worst_utilization else "N/A",
                    "rate": f"{worst_utilization.utilization_rate:.1%}" if worst_utilization else "N/A"
                },
                "average_utilization": f"{statistics.mean([om.utilization_rate for om in operator_metrics]):.1%}" if operator_metrics else "N/A"
            },
            "task_analysis": {
                "most_common_type": most_common_task_type[0],
                "unassigned_tasks": task_metrics.unassigned_tasks,
                "unassigned_hours": f"{metrics['overall_metrics'].unassigned_hours:.1f}h"
            },
            "quality_indicators": {
                "workload_balance": f"{metrics['overall_metrics'].workload_balance:.3f}",
                "constraint_violations": metrics['overall_metrics'].constraint_violations,
                "resource_utilization": f"{metrics['overall_metrics'].resource_utilization:.1%}"
            }
        }
        
        return summary
    
    def plot_shift_schedule(self, df: pd.DataFrame, date: str) -> plt.Figure:
        """
        Create a Gantt chart visualization of staff shifts.
        
        Args:
            df: DataFrame with columns ['staff', 'task', 'start', 'end']
            date: Date string in format "YYYY-MM-DD"
            
        Returns:
            matplotlib.Figure object
        """
        # Set up the figure with white background
        fig, ax = plt.subplots(figsize=(12, 8), facecolor='white')
        ax.set_facecolor('white')
        
        # Configure font - try to use a font that supports Japanese
        import matplotlib.font_manager as fm
        
        # Try to find a Japanese font
        japanese_fonts = ['Hiragino Sans', 'Yu Gothic', 'MS Gothic', 'Noto Sans CJK JP']
        font_found = False
        
        for font_name in japanese_fonts:
            if any(font_name in f.name for f in fm.fontManager.ttflist):
                plt.rcParams['font.family'] = font_name
                font_found = True
                break
        
        # Fallback to sans-serif if no Japanese font found
        if not font_found:
            plt.rcParams['font.family'] = 'sans-serif'
            
        plt.rcParams['font.size'] = 10
        
        # Get unique staff members in order
        staff_list = df['staff'].unique().tolist() if not df.empty else []
        staff_positions = {staff: i for i, staff in enumerate(staff_list)}
        
        # Color mapping for tasks (fixed hex codes)
        task_colors = {
            'task1': '#FF6B6B',  # Red
            'task2': '#4ECDC4',  # Teal
            'task3': '#45B7D1',  # Blue
            'task4': '#96CEB4',  # Green
            'task5': '#FECA57',  # Yellow
            'task6': '#DDA0DD',  # Plum
            'task7': '#98D8C8',  # Mint
            'task8': '#F7DC6F',  # Light Yellow
        }
        
        # Default color for unmapped tasks
        default_color = '#A0A0A0'
        
        # Process each shift
        bar_height = 0.8
        stacked_shifts = defaultdict(list)  # Track overlapping shifts per staff
        
        for _, row in df.iterrows():
            staff = row['staff']
            task = row['task']
            start = row['start']
            end = row['end']
            
            # Convert to hours if datetime objects
            if isinstance(start, (datetime, pd.Timestamp)):
                start_hour = start.hour + start.minute / 60
            else:
                start_hour = float(start)
                
            if isinstance(end, (datetime, pd.Timestamp)):
                end_hour = end.hour + end.minute / 60
            else:
                end_hour = float(end)
            
            # Handle midnight crossing (split into two bars)
            if end_hour < start_hour:
                # First part: from start to midnight (24)
                self._draw_shift_bar(ax, staff_positions[staff], start_hour, 24,
                                   task, task_colors.get(task, default_color),
                                   bar_height, stacked_shifts[staff])
                # Second part: from midnight (0) to end
                self._draw_shift_bar(ax, staff_positions[staff], 0, end_hour,
                                   task, task_colors.get(task, default_color),
                                   bar_height, stacked_shifts[staff])
            else:
                self._draw_shift_bar(ax, staff_positions[staff], start_hour, end_hour,
                                   task, task_colors.get(task, default_color),
                                   bar_height, stacked_shifts[staff])
        
        # Set up axes
        ax.set_ylim(-0.5, len(staff_list) - 0.5)
        ax.set_xlim(9, 18)
        
        # Y-axis: staff names
        ax.set_yticks(range(len(staff_list)))
        ax.set_yticklabels(staff_list)
        ax.invert_yaxis()  # Top to bottom
        
        # X-axis: hours
        ax.set_xticks(range(9, 19))
        ax.set_xlabel('Hour')
        ax.grid(True, axis='x', alpha=0.3, color='gray', linestyle='-', linewidth=0.5)
        
        # Add date as title
        ax.set_title(date, fontsize=14, pad=20)
        
        # Add border
        for spine in ax.spines.values():
            spine.set_edgecolor('black')
            spine.set_linewidth(1)
        
        # Create legend
        legend_elements = []
        for task, color in sorted(task_colors.items()):
            if task in df['task'].values:
                legend_elements.append(mpatches.Patch(color=color, label=task))
        
        if legend_elements:
            ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
        
        # Tight layout
        plt.tight_layout()
        
        # Save the figure
        output_path = f'./shift_{date}.png'
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        
        return fig
    
    def _draw_shift_bar(self, ax, staff_pos, start_hour, end_hour, task_name,
                       color, bar_height, stacked_list):
        """Helper method to draw a single shift bar with stacking support"""
        # Calculate vertical offset for stacking
        overlaps = []
        for existing in stacked_list:
            if not (end_hour <= existing['start'] or start_hour >= existing['end']):
                overlaps.append(existing['offset'])
        
        # Find the minimum available offset
        offset = 0
        if overlaps:
            offset = max(overlaps) + 0.15  # 4px ≈ 0.15 in figure units
        
        # Draw the bar
        duration = end_hour - start_hour
        y_position = staff_pos - bar_height/2 + offset
        
        rect = mpatches.Rectangle((start_hour, y_position), duration, bar_height,
                                 facecolor=color, edgecolor='black', linewidth=0.5)
        ax.add_patch(rect)
        
        # Add task name text
        text_x = start_hour + duration / 2
        text_y = y_position + bar_height / 2
        ax.text(text_x, text_y, task_name, ha='center', va='center',
               fontsize=9, color='white' if self._is_dark_color(color) else 'black')
        
        # Track this shift for stacking
        stacked_list.append({
            'start': start_hour,
            'end': end_hour,
            'offset': offset
        })
    
    def _is_dark_color(self, hex_color):
        """Helper to determine if text should be white or black"""
        # Convert hex to RGB
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        # Calculate luminance
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return luminance < 0.5
    
    def generate_gantt_chart_from_result(self, result: ScheduleResult, date: str = None) -> plt.Figure:
        """
        Generate a Gantt chart from a ScheduleResult object.
        
        Args:
            result: ScheduleResult containing assignments
            date: Optional date string, defaults to today
            
        Returns:
            matplotlib.Figure object
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Convert ScheduleResult to DataFrame format
        data = []
        for assignment in result.assignments:
            operator = self.operator_map.get(assignment.operator_id)
            task = self.task_map.get(assignment.task_id)
            
            if operator and task:
                # Convert hour-based times to datetime for consistency
                start_time = datetime.strptime(f"{assignment.start_hour:02d}:00", "%H:%M")
                end_hour = assignment.start_hour + assignment.duration_hours
                end_time = datetime.strptime(f"{int(end_hour):02d}:{int((end_hour % 1) * 60):02d}", "%H:%M")
                
                data.append({
                    'staff': operator.name,
                    'task': task.name,
                    'start': start_time,
                    'end': end_time
                })
        
        df = pd.DataFrame(data)
        return self.plot_shift_schedule(df, date)