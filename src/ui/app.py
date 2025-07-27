#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import time
from typing import List, Dict, Optional
import io
from pathlib import Path
import sys
import os
from datetime import datetime, date
import matplotlib.pyplot as plt

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.models import AlgorithmType
from src.data.operator_loader import OperatorLoader
from src.data.task_loader import TaskLoader
from src.data.validators import DataValidator
from src.utils.scheduler import JobScheduler
from src.utils.metrics import MetricsCalculator
from src.utils.export import ResultExporter
from src.ui.gantt_chart import plot_shift_schedule


class JobAllocationApp:
    """Job Allocation Management System"""
    
    def __init__(self):
        self.initialize_session_state()
        self.scheduler = JobScheduler()
        self.operator_loader = OperatorLoader()
        self.task_loader = TaskLoader()
        self.validator = DataValidator()
    
    def initialize_session_state(self):
        """Initialize session state"""
        if 'operators' not in st.session_state:
            st.session_state.operators = []
        if 'tasks' not in st.session_state:
            st.session_state.tasks = []
        if 'results' not in st.session_state:
            st.session_state.results = {}
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
        if 'algorithms_executed' not in st.session_state:
            st.session_state.algorithms_executed = []
        if 'current_algorithm' not in st.session_state:
            st.session_state.current_algorithm = None
        if 'execution_status' not in st.session_state:
            st.session_state.execution_status = "idle"
    
    def run(self):
        """Run main application"""
        self.setup_page_layout()
        self.render_sidebar()
        self.render_main_view()
    
    def setup_page_layout(self):
        """Setup page layout"""
        st.set_page_config(
            page_title="Job Allocation System",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            padding: 1rem 0;
            border-bottom: 2px solid #1f77b4;
            margin-bottom: 2rem;
        }
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #1f77b4;
        }
        .success-message {
            background-color: #d4edda;
            color: #155724;
            padding: 0.75rem;
            border-radius: 0.25rem;
            border: 1px solid #c3e6cb;
        }
        .error-message {
            background-color: #f8d7da;
            color: #721c24;
            padding: 0.75rem;
            border-radius: 0.25rem;
            border: 1px solid #f5c6cb;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header
        st.markdown('<div class="main-header">Job Allocation Optimization System</div>', 
                   unsafe_allow_html=True)
        
        # Description
        st.markdown("""
        **Optimize job allocation using multiple algorithms and analyze performance metrics**
        
        ---
        """)
    
    def render_sidebar(self):
        """Render sidebar"""
        with st.sidebar:
            st.header("Settings")
            
            # Data loading section
            self.render_data_loading_section()
            
            st.divider()
            
            # Algorithm execution section
            self.render_algorithm_execution_section()
            
            st.divider()
            
            # Results export section
            self.render_export_section()
            
            st.divider()
            
            # System information
            self.render_system_info()
    
    def render_data_loading_section(self):
        """Data loading section"""
        st.subheader("Data Loading")
        
        # Operator file upload
        st.write("**Operator Data**")
        operator_file = st.file_uploader(
            "Upload operator file",
            type=['csv', 'xlsx', 'json'],
            key="operator_file",
            help="Upload CSV, Excel, or JSON file with operator data"
        )
        
        # Task file upload
        st.write("**Task Data**")
        task_file = st.file_uploader(
            "Upload task file",
            type=['csv', 'xlsx', 'json'],
            key="task_file",
            help="Upload CSV, Excel, or JSON file with task data"
        )
        
        # Load data button
        if st.button("Load Data", disabled=not (operator_file and task_file)):
            self.load_data(operator_file, task_file)
        
        # Data status
        if st.session_state.data_loaded:
            st.success("Data loaded successfully")
            st.metric("Operators", len(st.session_state.operators))
            st.metric("Tasks", len(st.session_state.tasks))
        else:
            st.info("Please upload data files to get started")
    
    def render_algorithm_execution_section(self):
        """Algorithm execution section"""
        st.subheader("Algorithm Execution")
        
        if not st.session_state.data_loaded:
            st.warning("Please load data first")
            return
        
        # Algorithm selection
        algorithm_options = {
            "Linear Programming (PuLP)": AlgorithmType.LINEAR_PROGRAMMING
        }
        
        selected_algorithm = st.selectbox(
            "Select Algorithm",
            options=list(algorithm_options.keys()),
            help="Choose the optimization algorithm to execute"
        )
        
        # Algorithm parameters
        algorithm_type = algorithm_options[selected_algorithm]
        params = self.render_algorithm_parameters(algorithm_type)
        
        # Execution buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Run", disabled=st.session_state.execution_status == "running"):
                self.execute_algorithm(algorithm_type, params)
        
        with col2:
            if st.button("Run All", disabled=st.session_state.execution_status == "running"):
                self.execute_all_algorithms()
        
        # Execution status
        if st.session_state.execution_status == "running":
            st.info(f"Running {st.session_state.current_algorithm}...")
            
        # Executed algorithms list
        if st.session_state.algorithms_executed:
            st.write("**Executed Algorithms:**")
            for algo in st.session_state.algorithms_executed:
                st.write(f"✓ {algo}")
    
    def render_algorithm_parameters(self, algorithm_type: AlgorithmType) -> dict:
        """Render algorithm parameters UI"""
        params = {}
        
        with st.expander("Advanced Parameters", expanded=False):
            # Linear Programming doesn't need additional parameters
            pass
        
        return params
    
    def render_export_section(self):
        """Results export section"""
        st.subheader("Export Results")
        
        if not st.session_state.results:
            st.info("No results to export yet")
            return
        
        # Result selection
        available_results = list(st.session_state.results.keys())
        selected_result = st.selectbox(
            "Select Result",
            options=available_results,
            format_func=lambda x: x.replace('_', ' ').title()
        )
        
        # Format selection
        export_format = st.radio(
            "Export Format",
            options=["CSV", "Excel", "JSON"],
            horizontal=True
        )
        
        # Export button
        if st.button("Export"):
            self.export_results(selected_result, export_format)
    
    def render_system_info(self):
        """System information"""
        st.subheader("System Info")
        
        with st.expander("Details", expanded=False):
            st.write("**Available Algorithms:**")
            st.write("• Linear Programming (PuLP)")
            st.write("• Constraint Programming (OR-Tools CP-SAT)")
            st.write("• Genetic Algorithm (DEAP)")
            st.write("• Heuristic Algorithm")
            st.write("• Deferred Acceptance (Gale-Shapley)")
            
            st.write("**Supported Formats:**")
            st.write("• CSV (.csv)")
            st.write("• Excel (.xlsx)")
            st.write("• JSON (.json)")
    
    def render_main_view(self):
        """Render main view"""
        if not st.session_state.data_loaded:
            self.render_welcome_screen()
        else:
            self.render_data_overview()
            
            if st.session_state.results:
                st.divider()
                self.render_results_section()
    
    def render_welcome_screen(self):
        """Welcome screen"""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            ### Getting Started
            
            1. **Upload Data**: Upload operator and task files using the sidebar
            2. **Run Algorithm**: Select and execute optimization algorithms
            3. **View Results**: Analyze the allocation results and metrics
            4. **Export Data**: Download results in your preferred format
            
            ### Sample Data Available
            
            **To test the application immediately:**
            - Use `data/sample_operators.csv` for operator data
            - Use `data/sample_tasks.csv` for task data
            
            ### Required Data Format
            
            **Operator Data:**
            - operator_id, name, skill_set, available_hours
            
            **Task Data:**
            - task_id, name, task_type, estimated_hours, priority, deadline, required_skills
            """)
    
    def render_data_overview(self):
        """Data overview"""
        st.header("Data Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Operators")
            if st.session_state.operators:
                # Operator metrics
                operator_df = pd.DataFrame([op.to_dict() for op in st.session_state.operators])
                
                metrics_col1, metrics_col2 = st.columns(2)
                with metrics_col1:
                    st.metric("Count", len(st.session_state.operators))
                    
                with metrics_col2:
                    avg_hours = sum(op.get_available_hours() for op in st.session_state.operators) / len(st.session_state.operators)
                    st.metric("Avg Available Hours", f"{avg_hours:.1f}h")
                
                # Operator data preview
                with st.expander("Data Preview (First 5 rows)", expanded=False):
                    st.dataframe(operator_df.head(), use_container_width=True)
        
        with col2:
            st.subheader("Tasks")
            if st.session_state.tasks:
                # Task metrics
                task_df = pd.DataFrame([task.to_dict() for task in st.session_state.tasks])
                
                metrics_col1, metrics_col2 = st.columns(2)
                with metrics_col1:
                    st.metric("Count", len(st.session_state.tasks))
                    
                with metrics_col2:
                    avg_hours = sum(task.required_hours for task in st.session_state.tasks) / len(st.session_state.tasks)
                    st.metric("Avg Required Hours", f"{avg_hours:.1f}h")
                
                # Priority distribution
                priority_counts = task_df['priority'].value_counts()
                st.write("**Priority Distribution:**")
                st.bar_chart(priority_counts)
                
                # Task data preview
                with st.expander("Data Preview (First 5 rows)", expanded=False):
                    st.dataframe(task_df.head(), use_container_width=True)
    
    def render_results_section(self):
        """Results section"""
        st.header("Results")
        
        # Results tabs
        tabs = st.tabs([name.replace('_', ' ').title() for name in st.session_state.results.keys()])
        
        for i, (algorithm_name, result) in enumerate(st.session_state.results.items()):
            with tabs[i]:
                self.render_algorithm_result(algorithm_name, result)
        
        # Comparison section
        if len(st.session_state.results) > 1:
            st.divider()
            self.render_comparison_section()
    
    def render_algorithm_result(self, algorithm_name: str, result):
        """Individual algorithm result"""
        st.subheader(f"{algorithm_name.replace('_', ' ').title()} Results")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Assignments", len(result.assignments))
        with col2:
            st.metric("Total Hours", f"{result.get_total_assigned_hours()}h")
        with col3:
            st.metric("Assigned Operators", len(result.get_assigned_operator_ids()))
        with col4:
            st.metric("Execution Time", f"{result.execution_time_seconds:.2f}s")
        
        # Detailed results
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Assignments")
            if result.assignments:
                assignments_data = []
                for assignment in result.assignments:
                    operator = next(op for op in st.session_state.operators if op.operator_id == assignment.operator_id)
                    task = next(task for task in st.session_state.tasks if task.task_id == assignment.task_id)
                    
                    assignments_data.append({
                        "Operator": operator.name,
                        "Task": task.name,
                        "Start Time": f"{assignment.start_hour:02d}:00",
                        "End Time": f"{assignment.end_hour:02d}:00",
                        "Duration": f"{assignment.duration_hours}h"
                    })
                
                assignments_df = pd.DataFrame(assignments_data)
                st.dataframe(assignments_df, use_container_width=True)
            else:
                st.info("No assignments found")
        
        with col2:
            st.subheader("Metrics")
            if st.session_state.operators and st.session_state.tasks:
                metrics_calc = MetricsCalculator(st.session_state.operators, st.session_state.tasks)
                metrics = metrics_calc.calculate_all_metrics(result)
                
                # Overall metrics
                overall = metrics['overall_metrics']
                task_metrics = metrics['task_metrics']
                
                st.write(f"**Assignment Rate:** {task_metrics.assignment_rate:.1%}")
                st.write(f"**Overall Efficiency:** {overall.overall_efficiency:.1%}")
                st.write(f"**Workload Balance:** {overall.workload_balance:.2f}")
                st.write(f"**Constraint Violations:** {overall.constraint_violations}")
                
                # Operator utilization chart
                operator_metrics = metrics['operator_metrics']
                utilization_data = {
                    om.operator_name: om.utilization_rate 
                    for om in operator_metrics
                }
                
                st.write("**Operator Utilization:**")
                st.bar_chart(utilization_data)
        
        # Gantt chart section
        st.divider()
        st.subheader("Schedule Gantt Chart")
        
        if result.assignments:
            # Convert assignments to DataFrame format for Gantt chart
            gantt_data = []
            for assignment in result.assignments:
                operator = next(op for op in st.session_state.operators if op.operator_id == assignment.operator_id)
                task = next(task for task in st.session_state.tasks if task.task_id == assignment.task_id)
                
                # Create datetime objects for start and end times
                today = date.today()
                start_time = datetime.combine(today, datetime.min.time().replace(hour=assignment.start_hour))
                end_time = datetime.combine(today, datetime.min.time().replace(hour=assignment.end_hour))
                
                gantt_data.append({
                    'staff': operator.name,
                    'task': task.name,
                    'start': start_time,
                    'end': end_time
                })
            
            gantt_df = pd.DataFrame(gantt_data)
            
            # Generate Gantt chart
            date_str = today.strftime('%Y-%m-%d')
            fig = plot_shift_schedule(gantt_df, date_str)
            
            # Display in Streamlit
            st.pyplot(fig)
            
            # Add download button for the chart
            chart_path = f'./shift_{date_str}.png'
            if os.path.exists(chart_path):
                with open(chart_path, 'rb') as f:
                    st.download_button(
                        label="Download Gantt Chart",
                        data=f.read(),
                        file_name=f'gantt_chart_{algorithm_name}_{date_str}.png',
                        mime='image/png'
                    )
        else:
            st.info("No assignments to display in Gantt chart")
    
    def render_comparison_section(self):
        """Algorithm comparison section"""
        st.header("Algorithm Comparison")
        
        # Comparison metrics
        comparison_data = []
        for algorithm_name, result in st.session_state.results.items():
            metrics_calc = MetricsCalculator(st.session_state.operators, st.session_state.tasks)
            metrics = metrics_calc.calculate_all_metrics(result)
            
            comparison_data.append({
                "Algorithm": algorithm_name.replace('_', ' ').title(),
                "Assignments": len(result.assignments),
                "Assignment Rate": f"{metrics['task_metrics'].assignment_rate:.1%}",
                "Overall Efficiency": f"{metrics['overall_metrics'].overall_efficiency:.1%}",
                "Execution Time (s)": f"{result.execution_time_seconds:.2f}",
                "Constraint Violations": metrics['overall_metrics'].constraint_violations
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Assignment Count Comparison")
            chart_data = {
                row["Algorithm"]: row["Assignments"] 
                for _, row in comparison_df.iterrows()
            }
            st.bar_chart(chart_data)
        
        with col2:
            st.subheader("Execution Time Comparison")
            chart_data = {
                row["Algorithm"]: float(row["Execution Time (s)"]) 
                for _, row in comparison_df.iterrows()
            }
            st.bar_chart(chart_data)
    
    def load_data(self, operator_file, task_file):
        """Load data from uploaded files"""
        try:
            with st.spinner("Loading data..."):
                # Reset file pointers to beginning
                if operator_file:
                    operator_file.seek(0)
                if task_file:
                    task_file.seek(0)
                
                # Load operator data
                operator_data = self.operator_loader.load_from_uploaded_file(operator_file)
                
                # Load task data
                task_data = self.task_loader.load_from_uploaded_file(task_file)
                
                # Validate data
                operator_errors = self.validator.validate_operators(operator_data)
                task_errors = self.validator.validate_tasks(task_data)
                
                if operator_errors or task_errors:
                    error_msg = "Validation errors:\n"
                    if operator_errors:
                        error_msg += f"Operators: {'; '.join(operator_errors)}\n"
                    if task_errors:
                        error_msg += f"Tasks: {'; '.join(task_errors)}"
                    st.error(error_msg)
                    return
                
                # Update session state
                st.session_state.operators = operator_data
                st.session_state.tasks = task_data
                st.session_state.data_loaded = True
                
                # Configure scheduler
                self.scheduler.set_data(operator_data, task_data)
                
                st.success("Data loaded successfully!")
                
        except PermissionError:
            st.error("File access denied. Please check file permissions and try again.")
        except pd.errors.EmptyDataError:
            st.error("The uploaded file appears to be empty. Please check your file and try again.")
        except pd.errors.ParserError as e:
            st.error(f"Error parsing file format: {str(e)}")
        except ValueError as e:
            st.error(f"Data validation error: {str(e)}")
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            # Show more details for debugging
            st.error(f"Error type: {type(e).__name__}")
            if hasattr(e, '__cause__') and e.__cause__:
                st.error(f"Caused by: {str(e.__cause__)}")
    
    def execute_algorithm(self, algorithm_type: AlgorithmType, params: dict):
        """Execute single algorithm"""
        try:
            # Ensure scheduler has the latest data
            if not st.session_state.data_loaded or not st.session_state.operators or not st.session_state.tasks:
                st.error("No data loaded. Please upload and load data files first.")
                return
            
            # Re-set data in scheduler to ensure it has the latest data
            self.scheduler.set_data(st.session_state.operators, st.session_state.tasks)
            
            st.session_state.execution_status = "running"
            st.session_state.current_algorithm = algorithm_type.value
            
            with st.spinner(f"Running {algorithm_type.value}..."):
                result = self.scheduler.run_algorithm(algorithm_type, **params)
                
                # Store result
                st.session_state.results[algorithm_type.value] = result
                
                if algorithm_type.value not in st.session_state.algorithms_executed:
                    st.session_state.algorithms_executed.append(algorithm_type.value)
                
                st.session_state.execution_status = "completed"
                st.success(f"{algorithm_type.value} completed successfully!")
                
                # Refresh page
                st.rerun()
                
        except Exception as e:
            st.session_state.execution_status = "error"
            st.error(f"Execution error: {str(e)}")
    
    def execute_all_algorithms(self):
        """Execute all algorithms"""
        try:
            # Ensure scheduler has the latest data
            if not st.session_state.data_loaded or not st.session_state.operators or not st.session_state.tasks:
                st.error("No data loaded. Please upload and load data files first.")
                return
            
            # Re-set data in scheduler to ensure it has the latest data
            self.scheduler.set_data(st.session_state.operators, st.session_state.tasks)
            
            st.session_state.execution_status = "running"
            
            algorithms = [
                AlgorithmType.LINEAR_PROGRAMMING
            ]
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, algorithm_type in enumerate(algorithms):
                st.session_state.current_algorithm = algorithm_type.value
                status_text.text(f"Running: {algorithm_type.value}")
                
                try:
                    result = self.scheduler.run_algorithm(algorithm_type)
                    st.session_state.results[algorithm_type.value] = result
                    
                    if algorithm_type.value not in st.session_state.algorithms_executed:
                        st.session_state.algorithms_executed.append(algorithm_type.value)
                        
                except Exception as e:
                    st.warning(f"{algorithm_type.value} failed: {str(e)}")
                
                progress_bar.progress((i + 1) / len(algorithms))
            
            st.session_state.execution_status = "completed"
            status_text.text("All algorithms completed!")
            st.success("All algorithms completed successfully!")
            
            # Refresh page
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.session_state.execution_status = "error"
            st.error(f"Execution error: {str(e)}")
    
    def export_results(self, algorithm_name: str, export_format: str):
        """Export results to file"""
        try:
            result = st.session_state.results[algorithm_name]
            exporter = ResultExporter(st.session_state.operators, st.session_state.tasks)
            
            # Generate filename with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"job_allocation_{algorithm_name}_{timestamp}"
            
            if export_format == "CSV":
                # CSV export with download button
                assignments_data = []
                for assignment in result.assignments:
                    operator = next(op for op in st.session_state.operators if op.operator_id == assignment.operator_id)
                    task = next(task for task in st.session_state.tasks if task.task_id == assignment.task_id)
                    
                    assignments_data.append({
                        "Operator ID": assignment.operator_id,
                        "Operator Name": operator.name,
                        "Task ID": assignment.task_id,
                        "Task Name": task.name,
                        "Start Hour": assignment.start_hour,
                        "Duration Hours": assignment.duration_hours
                    })
                
                df = pd.DataFrame(assignments_data)
                csv = df.to_csv(index=False)
                
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"{filename}.csv",
                    mime="text/csv"
                )
            
            elif export_format == "JSON":
                # JSON export with download button
                exporter.export_to_json(result, f"{filename}.json")
                
                with open(f"{filename}.json", 'r', encoding='utf-8') as f:
                    json_content = f.read()
                
                st.download_button(
                    label="Download JSON",
                    data=json_content,
                    file_name=f"{filename}.json",
                    mime="application/json"
                )
            
            elif export_format == "Excel":
                # Excel export with download button
                buffer = io.BytesIO()
                
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    # Assignments sheet
                    assignments_data = []
                    for assignment in result.assignments:
                        operator = next(op for op in st.session_state.operators if op.operator_id == assignment.operator_id)
                        task = next(task for task in st.session_state.tasks if task.task_id == assignment.task_id)
                        
                        assignments_data.append({
                            "Operator ID": assignment.operator_id,
                            "Operator Name": operator.name,
                            "Task ID": assignment.task_id,
                            "Task Name": task.name,
                            "Start Hour": assignment.start_hour,
                            "Duration Hours": assignment.duration_hours
                        })
                    
                    df = pd.DataFrame(assignments_data)
                    df.to_excel(writer, sheet_name='Assignments', index=False)
                
                buffer.seek(0)
                
                st.download_button(
                    label="Download Excel",
                    data=buffer,
                    file_name=f"{filename}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            st.success(f"{export_format} file ready for download!")
            
        except Exception as e:
            st.error(f"Export error: {str(e)}")


def main():
    """Main function"""
    app = JobAllocationApp()
    app.run()


if __name__ == "__main__":
    main()