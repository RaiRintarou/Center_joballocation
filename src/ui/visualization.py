import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, time

from ..models import ScheduleResult, Operator, Task, ScheduleComparison
from ..utils.metrics import MetricsCalculator


class VisualizationComponents:
    """Çü¿ï–³óİüÍóÈnÆ¯é¹"""
    
    @staticmethod
    def schedule_timeline_chart(
        result: ScheduleResult,
        operators: List[Operator],
        tasks: List[Task],
        height: int = 600
    ) -> go.Figure:
        """
        ¹±¸åüë¿¤àé¤óó’\
        
        Args:
            result: ¹±¸åüëPœ
            operators: ªÚìü¿üê¹È
            tasks: ¿¹¯ê¹È
            height: ÁãüÈnØU
        
        Returns:
            PlotlyÕ£®å¢ªÖ¸§¯È
        """
        # Çü¿–™
        task_map = {task.task_id: task for task in tasks}
        operator_map = {op.operator_id: op for op in operators}
        
        # «éüÑìÃÈ
        colors = px.colors.qualitative.Set3
        task_colors = {}
        color_index = 0
        
        # ¿¹¯¿¤×Thkr’rŠSf
        unique_task_types = list(set(task.task_type for task in tasks))
        for task_type in unique_task_types:
            task_colors[task_type] = colors[color_index % len(colors)]
            color_index += 1
        
        # Õ£®å¢\
        fig = go.Figure()
        
        # ªÚìü¿üThnYøMn
        operator_positions = {op.operator_id: i for i, op in enumerate(operators)}
        
        # rŠSfÇü¿’æ
        for assignment in result.assignments:
            operator = operator_map[assignment.operator_id]
            task = task_map[assignment.task_id]
            
            y_pos = operator_positions[assignment.operator_id]
            
            # ¿¹¯ÖíÃ¯’ı 
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
                    f"ªÚìü¿ü: {operator.name}<br>"
                    f"B“: {assignment.start_hour:02d}:00 - {assignment.end_hour:02d}:00<br>"
                    f"@B“: {assignment.duration_hours}B“<br>"
                    f"¿¹¯¿¤×: {task.task_type}<br>"
                    f"*H¦: {task.priority.name}<br>"
                    "<extra></extra>"
                ),
                showlegend=False
            ))
            
            # ¿¹¯’Æ­¹ÈhWfı 
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
        
        # äÙB“nÌo’ı 
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
                name='äÙB“',
                showlegend=i == 0,
                hoverinfo='skip'
            ))
        
        # ì¤¢¦È-š
        fig.update_layout(
            title=dict(
                text=f"¹±¸åüë¿¤àé¤ó - {result.algorithm_type.value}",
                x=0.5,
                font=dict(size=16)
            ),
            xaxis=dict(
                title="B“",
                tickmode='linear',
                tick0=8,
                dtick=1,
                range=[8, 18],
                tickformat='%H:00',
                showgrid=True,
                gridcolor='lightgray'
            ),
            yaxis=dict(
                title="ªÚìü¿ü",
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
        ¢ë´êºàÔÒ°éÕ’\
        
        Args:
            results: ¢ë´êºàŸLPœnø
            operators: ªÚìü¿üê¹È
            tasks: ¿¹¯ê¹È
            metric: ÔY‹áÈê¯¹
        
        Returns:
            PlotlyÕ£®å¢ªÖ¸§¯È
        """
        # áÈê¯¹—
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
        
        # «éüŞÃ×
        colors = px.colors.qualitative.Set1[:len(algorithm_names)]
        
        # Ò°éÕ\
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
        
        # áÈê¯¹n-š
        metric_titles = {
            "assigned_tasks": "rŠSf¿¹¯p",
            "utilization_rate": "hS¹‡",
            "execution_time": "ŸLB“ (Ò)",
            "assignment_rate": "rŠSf‡"
        }
        
        title = metric_titles.get(metric, metric)
        
        fig.update_layout(
            title=dict(
                text=f"¢ë´êºàÔ - {title}",
                x=0.5,
                font=dict(size=16)
            ),
            xaxis_title="¢ë´êºà",
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
        <Í‡ìüÀüÁãüÈ’\
        
        Args:
            results: ¢ë´êºàŸLPœnø
            operators: ªÚìü¿üê¹È
            tasks: ¿¹¯ê¹È
        
        Returns:
            PlotlyÕ£®å¢ªÖ¸§¯È
        """
        metrics_calc = MetricsCalculator(operators, tasks)
        
        # ìüÀüÁãüÈ(nÇü¿–™
        categories = ['rŠSf‡', 'hS¹‡', '\m wĞéó¹', 'ŸL¦', '6uˆ']
        
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set1
        
        for i, (algorithm_name, result) in enumerate(results.items()):
            metrics = metrics_calc.calculate_all_metrics(result)
            
            # «Æ´ên$’0-1nÄòkc
            values = [
                metrics['task_metrics'].assignment_rate,  # rŠSf‡
                metrics['overall_metrics'].overall_efficiency,  # hS¹‡
                metrics['overall_metrics'].workload_balance,  # \m wĞéó¹
                1.0 - min(result.execution_time_seconds / 10.0, 1.0),  # ŸL¦p	
                1.0 - min(metrics['overall_metrics'].constraint_violations / 10.0, 1.0)  # 6uˆ
            ]
            
            fig.add_trace(go.Scatterpolar(
                r=values + [values[0]],  # ‰X_óbkY‹_ n$’ı 
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
                text="¢ë´êºà'ıÔ (ìüÀüÁãüÈ)",
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
        ªÚìü¿ü%<Í‡ÁãüÈ’\
        
        Args:
            result: ¹±¸åüëPœ
            operators: ªÚìü¿üê¹È
            tasks: ¿¹¯ê¹È
        
        Returns:
            PlotlyÕ£®å¢ªÖ¸§¯È
        """
        metrics_calc = MetricsCalculator(operators, tasks)
        operator_metrics = metrics_calc.calculate_operator_metrics(result)
        
        # Çü¿–™
        names = [om.operator_name for om in operator_metrics]
        utilization_rates = [om.utilization_rate for om in operator_metrics]
        assigned_hours = [om.total_assigned_hours for om in operator_metrics]
        available_hours = [om.available_hours for om in operator_metrics]
        
        # Ò°éÕ\
        fig = go.Figure()
        
        # <Í‡nÒ°éÕ
        fig.add_trace(go.Bar(
            name='<Í‡',
            x=names,
            y=utilization_rates,
            marker_color='steelblue',
            text=[f"{rate:.1%}" for rate in utilization_rates],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br><Í‡: %{y:.1%}<extra></extra>'
        ))
        
        # î<Í‡é¤ó‹80%	
        fig.add_hline(
            y=0.8,
            line_dash="dash",
            line_color="red",
            annotation_text="î<Í‡ (80%)"
        )
        
        fig.update_layout(
            title=dict(
                text="ªÚìü¿ü%<Í‡",
                x=0.5,
                font=dict(size=16)
            ),
            xaxis_title="ªÚìü¿ü",
            yaxis_title="<Í‡",
            yaxis=dict(tickformat='.0%', range=[0, 1]),
            plot_bgcolor='white',
            font=dict(size=12),
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def task_priority_distribution_chart(tasks: List[Task]) -> go.Figure:
        """
        ¿¹¯*H¦ÁãüÈ’\
        
        Args:
            tasks: ¿¹¯ê¹È
        
        Returns:
            PlotlyÕ£®å¢ªÖ¸§¯È
        """
        # *H¦%n«¦óÈ
        priority_counts = {}
        for task in tasks:
            priority = task.priority.name
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # †°éÕ\
        labels = list(priority_counts.keys())
        values = list(priority_counts.values())
        colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors[:len(labels)]),
            hovertemplate='<b>%{label}</b><br>¿¹¯p: %{value}<br>r: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title=dict(
                text="¿¹¯*H¦",
                x=0.5,
                font=dict(size=16)
            ),
            font=dict(size=12)
        )
        
        return fig
    
    @staticmethod
    def execution_time_comparison_chart(results: Dict[str, ScheduleResult]) -> go.Figure:
        """
        ŸLB“ÔÁãüÈ’\
        
        Args:
            results: ¢ë´êºàŸLPœnø
        
        Returns:
            PlotlyÕ£®å¢ªÖ¸§¯È
        """
        algorithm_names = [name.replace('_', ' ').title() for name in results.keys()]
        execution_times = [result.execution_time_seconds for result in results.values()]
        
        # *Ò°éÕ\
        fig = go.Figure(data=[
            go.Bar(
                x=execution_times,
                y=algorithm_names,
                orientation='h',
                marker_color='lightcoral',
                text=[f"{time:.2f}s" for time in execution_times],
                textposition='auto',
                hovertemplate='<b>%{y}</b><br>ŸLB“: %{x:.2f}Ò<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title=dict(
                text="¢ë´êºàŸLB“Ô",
                x=0.5,
                font=dict(size=16)
            ),
            xaxis_title="ŸLB“ (Ò)",
            yaxis_title="¢ë´êºà",
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
        Çü¿×ìÓåüÆüÖë’h:
        
        Args:
            data: h:Y‹Çü¿nê¹È
            title: ÆüÖën¿¤Èë
            max_rows: h:Y‹ 'Lp
        """
        st.subheader(title)
        
        if not data:
            st.info("h:Y‹Çü¿LBŠ~[“")
            return
        
        # Çü¿’DataFramek	Û
        if hasattr(data[0], 'to_dict'):
            df = pd.DataFrame([item.to_dict() for item in data[:max_rows]])
        else:
            df = pd.DataFrame(data[:max_rows])
        
        # qÅ1
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Ïöp", len(data))
        with col2:
            st.metric("h:öp", min(max_rows, len(data)))
        with col3:
            if len(data) > max_rows:
                st.metric("^h:öp", len(data) - max_rows)
        
        # ÆüÖëh:
        st.dataframe(df, use_container_width=True)
        
        # s0Å1
        if hasattr(data[0], 'to_dict'):
            with st.expander("«éàÅ1", expanded=False):
                columns_info = []
                for col in df.columns:
                    dtype = str(df[col].dtype)
                    null_count = df[col].isnull().sum()
                    unique_count = df[col].nunique()
                    
                    columns_info.append({
                        "«éà": col,
                        "Çü¿‹": dtype,
                        "NULL$p": null_count,
                        "æËü¯$p": unique_count
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
        ¹±¸åüë¬óÈÁãüÈ’\
        
        Args:
            result: ¹±¸åüëPœ
            operators: ªÚìü¿üê¹È
            tasks: ¿¹¯ê¹È
        
        Returns:
            PlotlyÕ£®å¢ªÖ¸§¯È
        """
        # Çü¿–™
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
            # znÁãüÈ’ÔY
            fig = go.Figure()
            fig.update_layout(
                title="¹±¸åüë¬óÈÁãüÈ - Çü¿jW",
                xaxis_title="B“",
                yaxis_title="¿¹¯"
            )
            return fig
        
        # DataFramek	Û
        df = pd.DataFrame(gantt_data)
        
        # ¬óÈÁãüÈ\
        fig = px.timeline(
            df,
            x_start="Start",
            x_end="Finish",
            y="Task",
            color="Resource",
            title="¹±¸åüë¬óÈÁãüÈ",
            hover_data=["Priority"]
        )
        
        fig.update_layout(
            xaxis_title="B“",
            yaxis_title="¿¹¯",
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
        Yyfnï–’h:Y‹qá½ÃÉ
        
        Args:
            results: ¢ë´êºàŸLPœnø
            operators: ªÚìü¿üê¹È
            tasks: ¿¹¯ê¹È
        """
        if not results:
            st.info("h:Y‹PœLBŠ~[“")
            return
        
        # ¿Ög.ï–’Q‹
        tabs = st.tabs([
            "=Ê ¹±¸åüë¿¤àé¤ó",
            "=È Ô°éÕ", 
            "<¯ <Í‡",
            "=Ë Çü¿×ìÓåü"
        ])
        
        with tabs[0]:
            st.header("¹±¸åüë¿¤àé¤ó")
            
            # ¢ë´êºàx
            selected_algorithm = st.selectbox(
                "h:Y‹¢ë´êºà",
                options=list(results.keys()),
                format_func=lambda x: x.replace('_', ' ').title()
            )
            
            if selected_algorithm in results:
                timeline_fig = VisualizationComponents.schedule_timeline_chart(
                    results[selected_algorithm], operators, tasks
                )
                st.plotly_chart(timeline_fig, use_container_width=True)
        
        with tabs[1]:
            st.header("¢ë´êºàÔ")
            
            if len(results) > 1:
                col1, col2 = st.columns(2)
                
                with col1:
                    # rŠSf¿¹¯pÔ
                    bar_fig = VisualizationComponents.comparison_bar_chart(
                        results, operators, tasks, "assigned_tasks"
                    )
                    st.plotly_chart(bar_fig, use_container_width=True)
                
                with col2:
                    # ŸLB“Ô
                    time_fig = VisualizationComponents.execution_time_comparison_chart(results)
                    st.plotly_chart(time_fig, use_container_width=True)
                
                # ìüÀüÁãüÈ
                radar_fig = VisualizationComponents.utilization_radar_chart(
                    results, operators, tasks
                )
                st.plotly_chart(radar_fig, use_container_width=True)
            else:
                st.info("Ôko2då
n¢ë´êºàPœLÅgY")
        
        with tabs[2]:
            st.header("<Í‡")
            
            # ¢ë´êºàx
            selected_algorithm = st.selectbox(
                "Y‹¢ë´êºà",
                options=list(results.keys()),
                format_func=lambda x: x.replace('_', ' ').title(),
                key="utilization_algo_select"
            )
            
            if selected_algorithm in results:
                col1, col2 = st.columns(2)
                
                with col1:
                    # ªÚìü¿ü%<Í‡
                    util_fig = VisualizationComponents.operator_utilization_chart(
                        results[selected_algorithm], operators, tasks
                    )
                    st.plotly_chart(util_fig, use_container_width=True)
                
                with col2:
                    # ¿¹¯*H¦
                    priority_fig = VisualizationComponents.task_priority_distribution_chart(tasks)
                    st.plotly_chart(priority_fig, use_container_width=True)
        
        with tabs[3]:
            st.header("Çü¿×ìÓåü")
            
            col1, col2 = st.columns(2)
            
            with col1:
                VisualizationComponents.data_preview_table(operators, "ªÚìü¿ü §")
            
            with col2:
                VisualizationComponents.data_preview_table(tasks, "¿¹¯ §")