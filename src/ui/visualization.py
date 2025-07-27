import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, time
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import matplotlib.font_manager as fm

from ..models import ScheduleResult, Operator, Task, ScheduleComparison
from ..utils.metrics import MetricsCalculator


class VisualizationComponents:
    """�����������n���"""
    
    @staticmethod
    def schedule_timeline_chart(
        result: ScheduleResult,
        operators: List[Operator],
        tasks: List[Task],
        height: int = 600
    ) -> go.Figure:
        """
        �����뿤����\
        
        Args:
            result: ������P�
            operators: ��������
            tasks: �����
            height: ����n�U
        
        Returns:
            Plotlyգ�墪ָ���
        """
        # �����
        task_map = {task.task_id: task for task in tasks}
        operator_map = {op.operator_id: op for op in operators}
        
        # �������
        colors = px.colors.qualitative.Set3
        task_colors = {}
        color_index = 0
        
        # ������Thkr�r�Sf
        unique_task_types = list(set(task.task_type for task in tasks))
        for task_type in unique_task_types:
            task_colors[task_type] = colors[color_index % len(colors)]
            color_index += 1
        
        # գ��\
        fig = go.Figure()
        
        # ������ThnY�Mn
        operator_positions = {op.operator_id: i for i, op in enumerate(operators)}
        
        # r�Sf�����
        for assignment in result.assignments:
            operator = operator_map[assignment.operator_id]
            task = task_map[assignment.task_id]
            
            y_pos = operator_positions[assignment.operator_id]
            
            # �����ï���
            fig.add_trace(go.Scatter(
                x=[assignment.start_hour, assignment.end_hour, assignment.end_hour, assignment.start_hour, assignment.start_hour],
                y=[y_pos - 0.4, y_pos - 0.4, y_pos + 0.4, y_pos + 0.4, y_pos - 0.4],
                fill='toself',
                fillcolor=task_colors.get(task.task_type, colors[0]),
                line=dict(color='black', width=1),
                mode='lines',
                name=f"{task.name}",
                hovertemplate=(
                    f"<b>{task.name}</b><br>"
                    f"������: {operator.name}<br>"
                    f"B�: {assignment.start_hour:02d}:00 - {assignment.end_hour:02d}:00<br>"
                    f"@�B�: {assignment.duration_hours}B�<br>"
                    f"������: {task.task_type}<br>"
                    f"*H�: {task.priority.name}<br>"
                    "<extra></extra>"
                ),
                showlegend=False
            ))
            
            # ����ƭ��hWf��
            fig.add_trace(go.Scatter(
                x=[(assignment.start_hour + assignment.end_hour) / 2],
                y=[y_pos],
                mode='text',
                text=[f"{task.name}"],
                textposition='middle center',
                textfont=dict(size=10, color='black'),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # ��B�n�o���
        for i, operator in enumerate(operators):
            work_start = operator.available_hours[0].hour
            work_end = operator.available_hours[1].hour
            
            fig.add_trace(go.Scatter(
                x=[work_start, work_end, work_end, work_start, work_start],
                y=[i - 0.45, i - 0.45, i + 0.45, i + 0.45, i - 0.45],
                fill='toself',
                fillcolor='rgba(200, 200, 200, 0.3)',
                line=dict(color='gray', width=1, dash='dot'),
                mode='lines',
                name='��B�',
                showlegend=i == 0,
                hoverinfo='skip'
            ))
        
        # 줢��-�
        fig.update_layout(
            title=dict(
                text=f"�����뿤��� - {result.algorithm_type.value}",
                x=0.5,
                font=dict(size=16)
            ),
            xaxis=dict(
                title="B�",
                tickmode='linear',
                tick0=8,
                dtick=1,
                range=[8, 18],
                tickformat='%H:00',
                showgrid=True,
                gridcolor='lightgray'
            ),
            yaxis=dict(
                title="������",
                tickmode='array',
                tickvals=list(range(len(operators))),
                ticktext=[op.name for op in operators],
                showgrid=True,
                gridcolor='lightgray'
            ),
            height=height,
            hovermode='closest',
            plot_bgcolor='white',
            font=dict(size=12)
        )
        
        return fig
    
    @staticmethod
    def comparison_bar_chart(
        results: Dict[str, ScheduleResult],
        operators: List[Operator],
        tasks: List[Task],
        metric: str = "assigned_tasks"
    ) -> go.Figure:
        """
        �����Ұ�Ւ\
        
        Args:
            results: �����LP�n��
            operators: ��������
            tasks: �����
            metric: �Y���꯹
        
        Returns:
            Plotlyգ�墪ָ���
        """
        # ��꯹�
        algorithm_names = []
        values = []
        
        metrics_calc = MetricsCalculator(operators, tasks)
        
        for algorithm_name, result in results.items():
            metrics = metrics_calc.calculate_all_metrics(result)
            algorithm_names.append(algorithm_name.replace('_', ' ').title())
            
            if metric == "assigned_tasks":
                values.append(len(result.assignments))
            elif metric == "utilization_rate":
                values.append(metrics['overall_metrics'].overall_efficiency)
            elif metric == "execution_time":
                values.append(result.execution_time_seconds)
            elif metric == "assignment_rate":
                values.append(metrics['task_metrics'].assignment_rate)
            else:
                values.append(0)
        
        # ������
        colors = px.colors.qualitative.Set1[:len(algorithm_names)]
        
        # Ұ��\
        fig = go.Figure(data=[
            go.Bar(
                x=algorithm_names,
                y=values,
                marker_color=colors,
                text=[f"{v:.2f}" if isinstance(v, float) else str(v) for v in values],
                textposition='auto',
                hovertemplate='<b>%{x}</b><br>$: %{y}<extra></extra>'
            )
        ])
        
        # ��꯹n-�
        metric_titles = {
            "assigned_tasks": "r�Sf���p",
            "utilization_rate": "hS��",
            "execution_time": "�LB� (�)",
            "assignment_rate": "r�Sf�"
        }
        
        title = metric_titles.get(metric, metric)
        
        fig.update_layout(
            title=dict(
                text=f"����� - {title}",
                x=0.5,
                font=dict(size=16)
            ),
            xaxis_title="����",
            yaxis_title=title,
            plot_bgcolor='white',
            font=dict(size=12),
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def utilization_radar_chart(
        results: Dict[str, ScheduleResult],
        operators: List[Operator],
        tasks: List[Task]
    ) -> go.Figure:
        """
        <͇�������Ȓ\
        
        Args:
            results: �����LP�n��
            operators: ��������
            tasks: �����
        
        Returns:
            Plotlyգ�墪ָ���
        """
        metrics_calc = MetricsCalculator(operators, tasks)
        
        # ��������(n�����
        categories = ['r�Sf�', 'hS��', '\m�w���', '�L�', '6u�']
        
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set1
        
        for i, (algorithm_name, result) in enumerate(results.items()):
            metrics = metrics_calc.calculate_all_metrics(result)
            
            # �ƴ�n$�0-1n��kc�
            values = [
                metrics['task_metrics'].assignment_rate,  # r�Sf�
                metrics['overall_metrics'].overall_efficiency,  # hS��
                metrics['overall_metrics'].workload_balance,  # \m�w���
                1.0 - min(result.execution_time_seconds / 10.0, 1.0),  # �L�p	
                1.0 - min(metrics['overall_metrics'].constraint_violations / 10.0, 1.0)  # 6u�
            ]
            
            fig.add_trace(go.Scatterpolar(
                r=values + [values[0]],  # �X_�bkY�_�n$���
                theta=categories + [categories[0]],
                fill='toself',
                fillcolor=f"rgba{(*px.colors.hex_to_rgb(colors[i % len(colors)]), 0.3)}",
                line=dict(color=colors[i % len(colors)], width=2),
                name=algorithm_name.replace('_', ' ').title(),
                hovertemplate='<b>%{theta}</b><br>$: %{r:.2f}<extra></extra>'
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1],
                    tickformat='.1%'
                )
            ),
            title=dict(
                text="����'�� (��������)",
                x=0.5,
                font=dict(size=16)
            ),
            font=dict(size=12),
            showlegend=True
        )
        
        return fig
    
    @staticmethod
    def operator_utilization_chart(
        result: ScheduleResult,
        operators: List[Operator],
        tasks: List[Task]
    ) -> go.Figure:
        """
        ������%<͇���Ȓ\
        
        Args:
            result: ������P�
            operators: ��������
            tasks: �����
        
        Returns:
            Plotlyգ�墪ָ���
        """
        metrics_calc = MetricsCalculator(operators, tasks)
        operator_metrics = metrics_calc.calculate_operator_metrics(result)
        
        # �����
        names = [om.operator_name for om in operator_metrics]
        utilization_rates = [om.utilization_rate for om in operator_metrics]
        assigned_hours = [om.total_assigned_hours for om in operator_metrics]
        available_hours = [om.available_hours for om in operator_metrics]
        
        # Ұ��\
        fig = go.Figure()
        
        # <͇nҰ��
        fig.add_trace(go.Bar(
            name='<͇',
            x=names,
            y=utilization_rates,
            marker_color='steelblue',
            text=[f"{rate:.1%}" for rate in utilization_rates],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br><͇: %{y:.1%}<extra></extra>'
        ))
        
        # �<͇���80%	
        fig.add_hline(
            y=0.8,
            line_dash="dash",
            line_color="red",
            annotation_text="�<͇ (80%)"
        )
        
        fig.update_layout(
            title=dict(
                text="������%<͇",
                x=0.5,
                font=dict(size=16)
            ),
            xaxis_title="������",
            yaxis_title="<͇",
            yaxis=dict(tickformat='.0%', range=[0, 1]),
            plot_bgcolor='white',
            font=dict(size=12),
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def task_priority_distribution_chart(tasks: List[Task]) -> go.Figure:
        """
        ���*H����Ȓ\
        
        Args:
            tasks: �����
        
        Returns:
            Plotlyգ�墪ָ���
        """
        # *H�%n����
        priority_counts = {}
        for task in tasks:
            priority = task.priority.name
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # ����\
        labels = list(priority_counts.keys())
        values = list(priority_counts.values())
        colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors[:len(labels)]),
            hovertemplate='<b>%{label}</b><br>���p: %{value}<br>r: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title=dict(
                text="���*H�",
                x=0.5,
                font=dict(size=16)
            ),
            font=dict(size=12)
        )
        
        return fig
    
    @staticmethod
    def execution_time_comparison_chart(results: Dict[str, ScheduleResult]) -> go.Figure:
        """
        �LB�����Ȓ\
        
        Args:
            results: �����LP�n��
        
        Returns:
            Plotlyգ�墪ָ���
        """
        algorithm_names = [name.replace('_', ' ').title() for name in results.keys()]
        execution_times = [result.execution_time_seconds for result in results.values()]
        
        # *Ұ��\
        fig = go.Figure(data=[
            go.Bar(
                x=execution_times,
                y=algorithm_names,
                orientation='h',
                marker_color='lightcoral',
                text=[f"{time:.2f}s" for time in execution_times],
                textposition='auto',
                hovertemplate='<b>%{y}</b><br>�LB�: %{x:.2f}�<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title=dict(
                text="�����LB��",
                x=0.5,
                font=dict(size=16)
            ),
            xaxis_title="�LB� (�)",
            yaxis_title="����",
            plot_bgcolor='white',
            font=dict(size=12),
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def data_preview_table(
        data: List[Any],
        title: str,
        max_rows: int = 10
    ) -> None:
        """
        ������������h:
        
        Args:
            data: h:Y����n��
            title: ����n����
            max_rows: h:Y�'Lp
        """
        st.subheader(title)
        
        if not data:
            st.info("h:Y����LB�~[�")
            return
        
        # ����DataFramek	�
        if hasattr(data[0], 'to_dict'):
            df = pd.DataFrame([item.to_dict() for item in data[:max_rows]])
        else:
            df = pd.DataFrame(data[:max_rows])
        
        # q�1
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("��p", len(data))
        with col2:
            st.metric("h:�p", min(max_rows, len(data)))
        with col3:
            if len(data) > max_rows:
                st.metric("^h:�p", len(data) - max_rows)
        
        # ����h:
        st.dataframe(df, use_container_width=True)
        
        # s0�1
        if hasattr(data[0], 'to_dict'):
            with st.expander("����1", expanded=False):
                columns_info = []
                for col in df.columns:
                    dtype = str(df[col].dtype)
                    null_count = df[col].isnull().sum()
                    unique_count = df[col].nunique()
                    
                    columns_info.append({
                        "���": col,
                        "����": dtype,
                        "NULL$p": null_count,
                        "����$p": unique_count
                    })
                
                info_df = pd.DataFrame(columns_info)
                st.dataframe(info_df, use_container_width=True)
    
    @staticmethod
    def schedule_gantt_chart(
        result: ScheduleResult,
        operators: List[Operator],
        tasks: List[Task]
    ) -> go.Figure:
        """
        �����������Ȓ\
        
        Args:
            result: ������P�
            operators: ��������
            tasks: �����
        
        Returns:
            Plotlyգ�墪ָ���
        """
        # �����
        task_map = {task.task_id: task for task in tasks}
        operator_map = {op.operator_id: op for op in operators}
        
        gantt_data = []
        
        for assignment in result.assignments:
            operator = operator_map[assignment.operator_id]
            task = task_map[assignment.task_id]
            
            gantt_data.append({
                'Task': f"{task.name} ({task.task_id})",
                'Start': f"2024-01-01 {assignment.start_hour:02d}:00:00",
                'Finish': f"2024-01-01 {assignment.end_hour:02d}:00:00",
                'Resource': operator.name,
                'Priority': task.priority.name
            })
        
        if not gantt_data:
            # zn���Ȓ�Y
            fig = go.Figure()
            fig.update_layout(
                title="������������ - ���jW",
                xaxis_title="B�",
                yaxis_title="���"
            )
            return fig
        
        # DataFramek	�
        df = pd.DataFrame(gantt_data)
        
        # �������\
        fig = px.timeline(
            df,
            x_start="Start",
            x_end="Finish",
            y="Task",
            color="Resource",
            title="������������",
            hover_data=["Priority"]
        )
        
        fig.update_layout(
            xaxis_title="B�",
            yaxis_title="���",
            font=dict(size=12),
            height=max(400, len(gantt_data) * 30)
        )
        
        return fig
    
    @staticmethod
    def display_all_visualizations(
        results: Dict[str, ScheduleResult],
        operators: List[Operator],
        tasks: List[Task]
    ) -> None:
        """
        Yyfn��h:Y�q���
        
        Args:
            results: �����LP�n��
            operators: ��������
            tasks: �����
        """
        if not results:
            st.info("h:Y�P�LB�~[�")
            return
        
        # ��g.��Q�
        tabs = st.tabs([
            "=� �����뿤���",
            "=� ����", 
            "<� <͇�",
            "=� ��������"
        ])
        
        with tabs[0]:
            st.header("�����뿤���")
            
            # ����x�
            selected_algorithm = st.selectbox(
                "h:Y�����",
                options=list(results.keys()),
                format_func=lambda x: x.replace('_', ' ').title()
            )
            
            if selected_algorithm in results:
                timeline_fig = VisualizationComponents.schedule_timeline_chart(
                    results[selected_algorithm], operators, tasks
                )
                st.plotly_chart(timeline_fig, use_container_width=True)
        
        with tabs[1]:
            st.header("�����")
            
            if len(results) > 1:
                col1, col2 = st.columns(2)
                
                with col1:
                    # r�Sf���p�
                    bar_fig = VisualizationComponents.comparison_bar_chart(
                        results, operators, tasks, "assigned_tasks"
                    )
                    st.plotly_chart(bar_fig, use_container_width=True)
                
                with col2:
                    # �LB��
                    time_fig = VisualizationComponents.execution_time_comparison_chart(results)
                    st.plotly_chart(time_fig, use_container_width=True)
                
                # ��������
                radar_fig = VisualizationComponents.utilization_radar_chart(
                    results, operators, tasks
                )
                st.plotly_chart(radar_fig, use_container_width=True)
            else:
                st.info("�ko2d�
n����P�LŁgY")
        
        with tabs[2]:
            st.header("<͇�")
            
            # ����x�
            selected_algorithm = st.selectbox(
                "�Y�����",
                options=list(results.keys()),
                format_func=lambda x: x.replace('_', ' ').title(),
                key="utilization_algo_select"
            )
            
            if selected_algorithm in results:
                col1, col2 = st.columns(2)
                
                with col1:
                    # ������%<͇
                    util_fig = VisualizationComponents.operator_utilization_chart(
                        results[selected_algorithm], operators, tasks
                    )
                    st.plotly_chart(util_fig, use_container_width=True)
                
                with col2:
                    # ���*H�
                    priority_fig = VisualizationComponents.task_priority_distribution_chart(tasks)
                    st.plotly_chart(priority_fig, use_container_width=True)
        
        with tabs[3]:
            st.header("��������")
            
            col1, col2 = st.columns(2)
            
            with col1:
                VisualizationComponents.data_preview_table(operators, "�������")
            
            with col2:
                VisualizationComponents.data_preview_table(tasks, "����")    
    @staticmethod
    def plot_shift_schedule(df: pd.DataFrame, date: str) -> plt.Figure:
        """
        Staff-by-time Gantt chart matching Optamo screenshot specifications.
        
        Args:
            df: DataFrame with columns: staff, task, start, end
                start/end are datetime or pd.Timestamp objects
            date: Date string like "2025-04-26"
        
        Returns:
            matplotlib.Figure object (also saves to ./shift_{date}.png)
        """
        # Set up matplotlib to handle Japanese text
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['font.size'] = 10
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Get unique staff members and sort them
        staff_list = df['staff'].unique()
        staff_positions = {staff: i for i, staff in enumerate(staff_list)}
        
        # Define color mapping for tasks
        task_colors = {
            '受付': '#FF6B6B',
            '診察補助': '#4ECDC4',
            '検査': '#45B7D1',
            '処置': '#FFA07A',
            '書類作成': '#98D8C8',
            'カウンセリング': '#F7DC6F',
            '在庫管理': '#BB8FCE',
            '清掃': '#85C1E2'
        }
        
        # Plot each shift
        bar_height = 0.8
        for _, row in df.iterrows():
            staff = row['staff']
            task = row['task']
            start_time = pd.to_datetime(row['start'])
            end_time = pd.to_datetime(row['end'])
            
            # Handle midnight crossing
            if end_time < start_time:
                # First part: from start to midnight (24:00)
                start_hour = start_time.hour + start_time.minute / 60
                rect1 = Rectangle(
                    (start_hour, staff_positions[staff] - bar_height/2),
                    24 - start_hour,
                    bar_height,
                    facecolor=task_colors.get(task, '#CCCCCC'),
                    edgecolor='black',
                    linewidth=0.5
                )
                ax.add_patch(rect1)
                
                # Add text label in the middle of first part
                text_x1 = start_hour + (24 - start_hour) / 2
                ax.text(text_x1, staff_positions[staff], task,
                       ha='center', va='center', fontsize=9)
                
                # Second part: from midnight (0:00) to end
                end_hour = end_time.hour + end_time.minute / 60
                rect2 = Rectangle(
                    (0, staff_positions[staff] - bar_height/2),
                    end_hour,
                    bar_height,
                    facecolor=task_colors.get(task, '#CCCCCC'),
                    edgecolor='black',
                    linewidth=0.5
                )
                ax.add_patch(rect2)
                
                # Add text label in the middle of second part if there's space
                if end_hour > 1:
                    text_x2 = end_hour / 2
                    ax.text(text_x2, staff_positions[staff], task,
                           ha='center', va='center', fontsize=9)
            else:
                # Normal case: no midnight crossing
                start_hour = start_time.hour + start_time.minute / 60
                end_hour = end_time.hour + end_time.minute / 60
                duration = end_hour - start_hour
                
                rect = Rectangle(
                    (start_hour, staff_positions[staff] - bar_height/2),
                    duration,
                    bar_height,
                    facecolor=task_colors.get(task, '#CCCCCC'),
                    edgecolor='black',
                    linewidth=0.5
                )
                ax.add_patch(rect)
                
                # Add text label in the middle of the bar
                text_x = start_hour + duration / 2
                ax.text(text_x, staff_positions[staff], task,
                       ha='center', va='center', fontsize=9)
        
        # Set up axes
        ax.set_xlim(9, 18)
        ax.set_ylim(-0.5, len(staff_list) - 0.5)
        
        # X-axis: hours
        ax.set_xticks(range(9, 19))
        ax.set_xticklabels([f'{h}:00' for h in range(9, 19)])
        ax.set_xlabel('Time', fontsize=11)
        
        # Y-axis: staff names
        ax.set_yticks(range(len(staff_list)))
        ax.set_yticklabels(staff_list)
        ax.set_ylabel('Staff', fontsize=11)
        
        # Add grid
        ax.grid(True, axis='x', color='lightgray', linewidth=0.5, alpha=0.7)
        ax.set_axisbelow(True)
        
        # Add title with date
        ax.set_title(date, fontsize=14, pad=20)
        
        # Create legend
        legend_elements = [mpatches.Patch(facecolor=color, edgecolor='black', 
                                        linewidth=0.5, label=task)
                          for task, color in task_colors.items()]
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1),
                 fontsize=9, frameon=True, fancybox=True, shadow=True)
        
        # Style the plot
        ax.spines['top'].set_visible(True)
        ax.spines['right'].set_visible(True)
        ax.spines['bottom'].set_visible(True)
        ax.spines['left'].set_visible(True)
        for spine in ax.spines.values():
            spine.set_edgecolor('black')
            spine.set_linewidth(1)
        
        # Set background color
        ax.set_facecolor('white')
        fig.patch.set_facecolor('white')
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Save the figure
        output_path = f'./shift_{date}.png'
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        
        return fig
EOF < /dev/null