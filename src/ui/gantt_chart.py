#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gantt chart visualization for staff scheduling"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Streamlit
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import matplotlib.font_manager as fm
import platform
from typing import Optional


def _setup_japanese_font():
    """Setup Japanese font for matplotlib based on operating system"""
    system = platform.system()
    
    # Define font preferences by OS
    font_preferences = {
        'Darwin': [  # macOS
            'Hiragino Sans',
            'Hiragino Maru Gothic Pro',
            'YuGothic',
            'YuMincho',
            'Toppan Bunkyu Gothic'
        ],
        'Windows': [
            'Yu Gothic',
            'MS Gothic',
            'Meiryo',
            'Yu Mincho'
        ],
        'Linux': [
            'Noto Sans CJK JP',
            'Takao Gothic',
            'IPAexGothic',
            'DejaVu Sans'
        ]
    }
    
    # Get available fonts
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    
    # Find first available font from preferences
    preferred_fonts = font_preferences.get(system, font_preferences['Linux'])
    
    for font in preferred_fonts:
        if font in available_fonts:
            plt.rcParams['font.family'] = font
            return
    
    # Fallback to first available Japanese font
    japanese_fonts = [f for f in available_fonts if any(
        keyword in f.lower() for keyword in ['hiragino', 'yu', 'noto', 'takao', 'ipa', 'gothic', 'mincho']
    )]
    
    if japanese_fonts:
        plt.rcParams['font.family'] = japanese_fonts[0]
    else:
        # Last resort: use DejaVu Sans (characters may not display)
        plt.rcParams['font.family'] = 'DejaVu Sans'


def plot_shift_schedule(df: pd.DataFrame, date: str, break_start: float = 12.0, break_end: float = 13.0) -> plt.Figure:
    """
    Staff-by-time Gantt chart with break time visualization.
    
    Args:
        df: DataFrame with columns: staff, task, start, end
            start/end are datetime or pd.Timestamp objects
        date: Date string like "2025-04-26"
        break_start: Break start time in hours (default: 12.0 for 12:00)
        break_end: Break end time in hours (default: 13.0 for 13:00)
    
    Returns:
        matplotlib.Figure object (also saves to ./shift_{date}.png)
    """
    # Set up matplotlib to handle Japanese text
    _setup_japanese_font()
    plt.rcParams['font.size'] = 10
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Get unique staff members and sort them
    staff_list = df['staff'].unique()
    staff_positions = {staff: i for i, staff in enumerate(staff_list)}
    
    # Define default color palette
    default_colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', 
        '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2',
        '#FF9F43', '#70D0E4', '#A29BFE', '#FD79A8',
        '#FDCB6E', '#6C5CE7', '#E17055', '#00B894'
    ]
    
    # Create dynamic color mapping based on actual task names in data
    unique_tasks = df['task'].unique()
    task_colors = {}
    for i, task in enumerate(unique_tasks):
        task_colors[task] = default_colors[i % len(default_colors)]
    
    # First, add break time bars for all staff
    break_color = '#D3D3D3'  # Light gray for break time
    bar_height = 0.8
    
    for i, staff in enumerate(staff_list):
        # Add break time bar
        break_rect = Rectangle(
            (break_start, i - bar_height/2),
            break_end - break_start,
            bar_height,
            facecolor=break_color,
            edgecolor='black',
            linewidth=0.5,
            alpha=0.8
        )
        ax.add_patch(break_rect)
        
        # Add break time label
        break_text_x = break_start + (break_end - break_start) / 2
        ax.text(break_text_x, i, '休憩',
               ha='center', va='center', fontsize=8, weight='bold')
    
    # Plot each shift with break time consideration
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
            
            # Check if task crosses break time
            if start_hour < break_end and end_hour > break_start:
                # Task crosses break time - split into segments
                segments = []
                
                if start_hour < break_start:
                    # Segment before break
                    segments.append((start_hour, min(break_start, end_hour)))
                
                if end_hour > break_end:
                    # Segment after break
                    segments.append((max(break_end, start_hour), end_hour))
                
                # Draw each segment
                for seg_start, seg_end in segments:
                    if seg_end > seg_start:  # Only draw if segment has duration
                        duration = seg_end - seg_start
                        rect = Rectangle(
                            (seg_start, staff_positions[staff] - bar_height/2),
                            duration,
                            bar_height,
                            facecolor=task_colors.get(task, '#CCCCCC'),
                            edgecolor='black',
                            linewidth=0.5
                        )
                        ax.add_patch(rect)
                        
                        # Add text label if segment is wide enough
                        if duration > 0.5:  # Only add text if segment is wide enough
                            text_x = seg_start + duration / 2
                            ax.text(text_x, staff_positions[staff], task,
                                   ha='center', va='center', fontsize=9)
            else:
                # Task doesn't cross break time - normal display
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
    ax.set_xlim(8, 18)
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
    
    # Create legend including break time
    legend_elements = [mpatches.Patch(facecolor=color, edgecolor='black', 
                                    linewidth=0.5, label=task)
                      for task, color in task_colors.items()]
    
    # Add break time to legend
    legend_elements.append(mpatches.Patch(facecolor=break_color, edgecolor='black',
                                        linewidth=0.5, label='休憩時間'))
    
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


# Test code - only runs when file is executed directly
if __name__ == "__main__":
    from datetime import datetime
    
    # Create sample data
    data = {
        'staff': ['田中太郎', '山田花子', '佐藤次郎', '鈴木美咲', '田中太郎'],
        'task': ['受付', '診察補助', '検査', '処置', 'カウンセリング'],
        'start': [
            datetime(2025, 4, 26, 9, 0),
            datetime(2025, 4, 26, 10, 0),
            datetime(2025, 4, 26, 9, 30),
            datetime(2025, 4, 26, 14, 0),
            datetime(2025, 4, 26, 15, 30)
        ],
        'end': [
            datetime(2025, 4, 26, 12, 0),
            datetime(2025, 4, 26, 14, 0),
            datetime(2025, 4, 26, 11, 30),
            datetime(2025, 4, 26, 16, 0),
            datetime(2025, 4, 26, 17, 30)
        ]
    }
    
    df = pd.DataFrame(data)
    date = "2025-04-26"
    
    print(f"Creating Gantt chart for {date}...")
    fig = plot_shift_schedule(df, date)
    print(f"Chart saved to ./shift_{date}.png")
    
    # Display the chart (optional)
    plt.show()