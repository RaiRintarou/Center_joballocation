#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import json
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import io

from ..models import ScheduleResult, ScheduleComparison, Operator, Task
from .metrics import MetricsCalculator


class ResultExporter:
    """Export optimization results to various formats"""
    
    def __init__(self, operators: List[Operator], tasks: List[Task]):
        self.operators = operators
        self.tasks = tasks
        self.operator_map = {op.operator_id: op for op in operators}
        self.task_map = {task.task_id: task for task in tasks}
    
    def export_to_csv(self, result: ScheduleResult, output_path: str) -> str:
        """Export results to CSV format"""
        output_path = Path(output_path)
        
        # Prepare assignment data
        assignments_data = []
        for assignment in result.assignments:
            operator = self.operator_map.get(assignment.operator_id)
            task = self.task_map.get(assignment.task_id)
            
            assignments_data.append({
                "Operator ID": assignment.operator_id,
                "Operator Name": operator.name if operator else "Unknown",
                "Task ID": assignment.task_id,
                "Task Name": task.name if task else "Unknown",
                "Task Type": task.task_type if task else "Unknown",
                "Start Hour": assignment.start_hour,
                "End Hour": assignment.end_hour,
                "Duration Hours": assignment.duration_hours,
                "Required Skill": task.required_skill if task else "None",
                "Priority": task.priority.name if task else "Unknown"
            })
        
        # Write to CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            if assignments_data:
                fieldnames = assignments_data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(assignments_data)
        
        return str(output_path)
    
    def export_to_excel(self, result: ScheduleResult, output_path: str) -> str:
        """Export results to Excel format with multiple sheets"""
        output_path = Path(output_path)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Assignments sheet
            assignments_data = []
            for assignment in result.assignments:
                operator = self.operator_map.get(assignment.operator_id)
                task = self.task_map.get(assignment.task_id)
                
                assignments_data.append({
                    "Operator ID": assignment.operator_id,
                    "Operator Name": operator.name if operator else "Unknown",
                    "Task ID": assignment.task_id,
                    "Task Name": task.name if task else "Unknown",
                    "Task Type": task.task_type if task else "Unknown",
                    "Start Hour": assignment.start_hour,
                    "End Hour": assignment.end_hour,
                    "Duration Hours": assignment.duration_hours,
                    "Required Skill": task.required_skill if task else "None",
                    "Priority": task.priority.name if task else "Unknown"
                })
            
            if assignments_data:
                assignments_df = pd.DataFrame(assignments_data)
                assignments_df.to_excel(writer, sheet_name='Assignments', index=False)
            
            # Operator summary sheet
            operator_summary = []
            for operator in self.operators:
                operator_assignments = [a for a in result.assignments if a.operator_id == operator.operator_id]
                total_assigned_hours = sum(a.duration_hours for a in operator_assignments)
                
                operator_summary.append({
                    "Operator ID": operator.operator_id,
                    "Operator Name": operator.name,
                    "Available Hours": operator.get_available_hours(),
                    "Assigned Hours": total_assigned_hours,
                    "Utilization Rate": f"{(total_assigned_hours / operator.get_available_hours()):.1%}" if operator.get_available_hours() > 0 else "0%",
                    "Number of Tasks": len(operator_assignments),
                    "Skills": ", ".join(operator.skill_set)
                })
            
            operator_df = pd.DataFrame(operator_summary)
            operator_df.to_excel(writer, sheet_name='Operator Summary', index=False)
            
            # Task summary sheet
            task_summary = []
            assigned_task_ids = {a.task_id for a in result.assignments}
            
            for task in self.tasks:
                is_assigned = task.task_id in assigned_task_ids
                assigned_operator = None
                
                if is_assigned:
                    assignment = next(a for a in result.assignments if a.task_id == task.task_id)
                    operator = self.operator_map.get(assignment.operator_id)
                    assigned_operator = operator.name if operator else "Unknown"
                
                task_summary.append({
                    "Task ID": task.task_id,
                    "Task Name": task.name,
                    "Task Type": task.task_type,
                    "Required Hours": task.required_hours,
                    "Required Skill": task.required_skill or "None",
                    "Priority": task.priority.name,
                    "Status": "Assigned" if is_assigned else "Unassigned",
                    "Assigned Operator": assigned_operator or "N/A"
                })
            
            task_df = pd.DataFrame(task_summary)
            task_df.to_excel(writer, sheet_name='Task Summary', index=False)
            
            # Add metrics if available
            if self.operators and self.tasks:
                metrics_calc = MetricsCalculator(self.operators, self.tasks)
                metrics = metrics_calc.calculate_all_metrics(result)
                
                # Overall metrics sheet
                overall_data = []
                overall_metrics = metrics['overall_metrics']
                overall_data.append({"Metric": "Total Assignments", "Value": overall_metrics.total_assignments})
                overall_data.append({"Metric": "Overall Efficiency", "Value": f"{overall_metrics.overall_efficiency:.1%}"})
                overall_data.append({"Metric": "Workload Balance", "Value": f"{overall_metrics.workload_balance:.3f}"})
                overall_data.append({"Metric": "Constraint Violations", "Value": overall_metrics.constraint_violations})
                overall_data.append({"Metric": "Resource Utilization", "Value": f"{overall_metrics.resource_utilization:.1%}"})
                
                overall_df = pd.DataFrame(overall_data)
                overall_df.to_excel(writer, sheet_name='Overall Metrics', index=False)
        
        return str(output_path)
    
    def export_to_json(self, result: ScheduleResult, output_path: str) -> str:
        """Export results to JSON format"""
        output_path = Path(output_path)
        
        # Prepare comprehensive data structure
        export_data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "total_assignments": len(result.assignments),
                "execution_time_seconds": getattr(result, 'execution_time_seconds', 0.0)
            },
            "assignments": [],
            "operators": [],
            "tasks": [],
            "summary": {}
        }
        
        # Add assignments
        for assignment in result.assignments:
            operator = self.operator_map.get(assignment.operator_id)
            task = self.task_map.get(assignment.task_id)
            
            assignment_data = {
                "operator_id": assignment.operator_id,
                "operator_name": operator.name if operator else "Unknown",
                "task_id": assignment.task_id,
                "task_name": task.name if task else "Unknown",
                "start_hour": assignment.start_hour,
                "end_hour": assignment.end_hour,
                "duration_hours": assignment.duration_hours
            }
            export_data["assignments"].append(assignment_data)
        
        # Add operator data
        for operator in self.operators:
            operator_assignments = [a for a in result.assignments if a.operator_id == operator.operator_id]
            total_assigned_hours = sum(a.duration_hours for a in operator_assignments)
            
            operator_data = {
                "operator_id": operator.operator_id,
                "name": operator.name,
                "available_hours": operator.get_available_hours(),
                "available_time_range": operator.available_hours,
                "skills": operator.skill_set,
                "assigned_hours": total_assigned_hours,
                "utilization_rate": total_assigned_hours / operator.get_available_hours() if operator.get_available_hours() > 0 else 0.0,
                "assigned_tasks": len(operator_assignments)
            }
            export_data["operators"].append(operator_data)
        
        # Add task data
        assigned_task_ids = {a.task_id for a in result.assignments}
        for task in self.tasks:
            is_assigned = task.task_id in assigned_task_ids
            
            task_data = {
                "task_id": task.task_id,
                "name": task.name,
                "task_type": task.task_type,
                "required_hours": task.required_hours,
                "required_skill": task.required_skill,
                "priority": task.priority.name,
                "is_assigned": is_assigned
            }
            
            if task.deadline:
                task_data["deadline"] = task.deadline.isoformat()
            
            export_data["tasks"].append(task_data)
        
        # Add summary metrics
        if self.operators and self.tasks:
            metrics_calc = MetricsCalculator(self.operators, self.tasks)
            metrics = metrics_calc.calculate_all_metrics(result)
            
            export_data["summary"] = {
                "task_metrics": {
                    "total_tasks": metrics['task_metrics'].total_tasks,
                    "assigned_tasks": metrics['task_metrics'].assigned_tasks,
                    "assignment_rate": metrics['task_metrics'].assignment_rate
                },
                "overall_metrics": {
                    "overall_efficiency": metrics['overall_metrics'].overall_efficiency,
                    "workload_balance": metrics['overall_metrics'].workload_balance,
                    "constraint_violations": metrics['overall_metrics'].constraint_violations,
                    "resource_utilization": metrics['overall_metrics'].resource_utilization
                }
            }
        
        # Write to JSON
        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    def export_comparison(self, comparison: ScheduleComparison, output_path: str, format_type: str = "excel") -> str:
        """Export algorithm comparison results"""
        output_path = Path(output_path)
        
        if format_type.lower() == "excel":
            return self._export_comparison_excel(comparison, output_path)
        elif format_type.lower() == "json":
            return self._export_comparison_json(comparison, output_path)
        elif format_type.lower() == "csv":
            return self._export_comparison_csv(comparison, output_path)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def _export_comparison_excel(self, comparison: ScheduleComparison, output_path: Path) -> str:
        """Export comparison to Excel format"""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Algorithm comparison summary
            summary_data = []
            for algorithm_name, result in comparison.results.items():
                metrics_calc = MetricsCalculator(self.operators, self.tasks)
                metrics = metrics_calc.calculate_all_metrics(result)
                
                summary_data.append({
                    "Algorithm": algorithm_name,
                    "Total Assignments": len(result.assignments),
                    "Assignment Rate": f"{metrics['task_metrics'].assignment_rate:.1%}",
                    "Overall Efficiency": f"{metrics['overall_metrics'].overall_efficiency:.1%}",
                    "Execution Time (s)": getattr(result, 'execution_time_seconds', 0.0),
                    "Constraint Violations": metrics['overall_metrics'].constraint_violations,
                    "Resource Utilization": f"{metrics['overall_metrics'].resource_utilization:.1%}"
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Algorithm Comparison', index=False)
            
            # Individual algorithm results
            for algorithm_name, result in comparison.results.items():
                sheet_name = algorithm_name.replace('_', ' ').title()[:31]  # Excel sheet name limit
                
                assignments_data = []
                for assignment in result.assignments:
                    operator = self.operator_map.get(assignment.operator_id)
                    task = self.task_map.get(assignment.task_id)
                    
                    assignments_data.append({
                        "Operator ID": assignment.operator_id,
                        "Operator Name": operator.name if operator else "Unknown",
                        "Task ID": assignment.task_id,
                        "Task Name": task.name if task else "Unknown",
                        "Start Hour": assignment.start_hour,
                        "Duration Hours": assignment.duration_hours
                    })
                
                if assignments_data:
                    assignments_df = pd.DataFrame(assignments_data)
                    assignments_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return str(output_path)
    
    def _export_comparison_json(self, comparison: ScheduleComparison, output_path: Path) -> str:
        """Export comparison to JSON format"""
        export_data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "algorithms_compared": list(comparison.results.keys())
            },
            "algorithm_results": {}
        }
        
        for algorithm_name, result in comparison.results.items():
            metrics_calc = MetricsCalculator(self.operators, self.tasks)
            metrics = metrics_calc.calculate_all_metrics(result)
            
            algorithm_data = {
                "assignments_count": len(result.assignments),
                "execution_time_seconds": getattr(result, 'execution_time_seconds', 0.0),
                "metrics": {
                    "assignment_rate": metrics['task_metrics'].assignment_rate,
                    "overall_efficiency": metrics['overall_metrics'].overall_efficiency,
                    "workload_balance": metrics['overall_metrics'].workload_balance,
                    "constraint_violations": metrics['overall_metrics'].constraint_violations,
                    "resource_utilization": metrics['overall_metrics'].resource_utilization
                },
                "assignments": [
                    {
                        "operator_id": a.operator_id,
                        "task_id": a.task_id,
                        "start_hour": a.start_hour,
                        "duration_hours": a.duration_hours
                    }
                    for a in result.assignments
                ]
            }
            
            export_data["algorithm_results"][algorithm_name] = algorithm_data
        
        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    def _export_comparison_csv(self, comparison: ScheduleComparison, output_path: Path) -> str:
        """Export comparison summary to CSV format"""
        summary_data = []
        for algorithm_name, result in comparison.results.items():
            metrics_calc = MetricsCalculator(self.operators, self.tasks)
            metrics = metrics_calc.calculate_all_metrics(result)
            
            summary_data.append({
                "Algorithm": algorithm_name,
                "Total Assignments": len(result.assignments),
                "Assignment Rate": metrics['task_metrics'].assignment_rate,
                "Overall Efficiency": metrics['overall_metrics'].overall_efficiency,
                "Execution Time (s)": getattr(result, 'execution_time_seconds', 0.0),
                "Constraint Violations": metrics['overall_metrics'].constraint_violations,
                "Resource Utilization": metrics['overall_metrics'].resource_utilization,
                "Workload Balance": metrics['overall_metrics'].workload_balance
            })
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            if summary_data:
                fieldnames = summary_data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(summary_data)
        
        return str(output_path)
    
    def create_report(self, result: ScheduleResult, output_path: str) -> str:
        """Create a comprehensive text report"""
        output_path = Path(output_path)
        
        # Generate metrics
        metrics_calc = MetricsCalculator(self.operators, self.tasks)
        metrics = metrics_calc.calculate_all_metrics(result)
        summary = metrics_calc.generate_summary_report(result)
        
        # Create report content
        report_lines = [
            "JOB ALLOCATION OPTIMIZATION REPORT",
            "=" * 50,
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Execution Time: {getattr(result, 'execution_time_seconds', 0.0):.2f} seconds",
            "",
            "EXECUTIVE SUMMARY",
            "-" * 20,
            f"Total Assignments: {summary['execution_summary']['total_assignments']}",
            f"Assignment Rate: {summary['execution_summary']['assignment_rate']}",
            f"Overall Efficiency: {summary['execution_summary']['overall_efficiency']}",
            "",
            "OPERATOR PERFORMANCE",
            "-" * 20,
            f"Best Utilization: {summary['operator_performance']['best_utilization']['name']} "
            f"({summary['operator_performance']['best_utilization']['rate']})",
            f"Worst Utilization: {summary['operator_performance']['worst_utilization']['name']} "
            f"({summary['operator_performance']['worst_utilization']['rate']})",
            f"Average Utilization: {summary['operator_performance']['average_utilization']}",
            "",
            "TASK ANALYSIS",
            "-" * 20,
            f"Most Common Task Type: {summary['task_analysis']['most_common_type']}",
            f"Unassigned Tasks: {summary['task_analysis']['unassigned_tasks']}",
            f"Unassigned Hours: {summary['task_analysis']['unassigned_hours']}",
            "",
            "QUALITY INDICATORS",
            "-" * 20,
            f"Workload Balance: {summary['quality_indicators']['workload_balance']}",
            f"Constraint Violations: {summary['quality_indicators']['constraint_violations']}",
            f"Resource Utilization: {summary['quality_indicators']['resource_utilization']}",
            "",
            "DETAILED ASSIGNMENTS",
            "-" * 20
        ]
        
        # Add assignment details
        for assignment in result.assignments:
            operator = self.operator_map.get(assignment.operator_id)
            task = self.task_map.get(assignment.task_id)
            
            operator_name = operator.name if operator else "Unknown"
            task_name = task.name if task else "Unknown"
            
            report_lines.append(
                f"{operator_name} -> {task_name} "
                f"({assignment.start_hour:02d}:00-{assignment.end_hour:02d}:00, "
                f"{assignment.duration_hours}h)"
            )
        
        # Write report
        with open(output_path, 'w', encoding='utf-8') as report_file:
            report_file.write('\n'.join(report_lines))
        
        return str(output_path)