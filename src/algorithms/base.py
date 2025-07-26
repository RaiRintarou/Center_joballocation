#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
import time

from ..models import Operator, Task, ScheduleResult, AlgorithmType


class OptimizationAlgorithm(ABC):
    """最適化アルゴリズムの基底クラス"""
    
    def __init__(self, algorithm_type: AlgorithmType):
        self.algorithm_type = algorithm_type
        self.operators: List[Operator] = []
        self.tasks: List[Task] = []
        self.result: Optional[ScheduleResult] = None
        
    def setup(self, operators: List[Operator], tasks: List[Task]) -> None:
        """アルゴリズムの初期設定"""
        self.operators = operators
        self.tasks = tasks
        self.result = None
        
        # オペレーターとタスクのインデックスマップを作成
        self.operator_map = {op.operator_id: op for op in operators}
        self.task_map = {task.task_id: task for task in tasks}
        
        # スキルマッチングテーブルを事前計算
        self.skill_matching = self._compute_skill_matching()
    
    def run(self) -> ScheduleResult:
        """アルゴリズムを実行してスケジュール結果を返す"""
        if not self.operators or not self.tasks:
            raise ValueError("Operators and tasks must be set before running the algorithm")
        
        # 実行時間の計測開始
        start_time = time.time()
        
        # アルゴリズム固有の最適化処理を実行
        self.result = self._optimize()
        
        # 実行時間を記録
        execution_time = time.time() - start_time
        self.result.execution_time_seconds = execution_time
        
        return self.result
    
    @abstractmethod
    def _optimize(self) -> ScheduleResult:
        """アルゴリズム固有の最適化処理を実装"""
        pass
    
    def _compute_skill_matching(self) -> Dict[str, List[str]]:
        """タスクに対して適格なオペレーターのIDリストを事前計算"""
        skill_matching = {}
        
        for task in self.tasks:
            eligible_operators = []
            
            for operator in self.operators:
                # タスクに必要スキルが指定されていない場合は全員が適格
                if not task.required_skill:
                    eligible_operators.append(operator.operator_id)
                # 必要スキルを持っているオペレーターのみ適格
                elif operator.has_skill(task.required_skill):
                    eligible_operators.append(operator.operator_id)
            
            skill_matching[task.task_id] = eligible_operators
        
        return skill_matching
    
    def can_assign(self, operator_id: str, task_id: str) -> bool:
        """オペレーターがタスクに割り当て可能かチェック"""
        # スキルマッチングチェック
        if task_id not in self.skill_matching:
            return False
        
        if operator_id not in self.skill_matching[task_id]:
            return False
        
        return True
    
    def get_operator_available_slots(self, operator_id: str, 
                                   existing_assignments: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        オペレーターの利用可能な時間スロットを取得
        
        Args:
            operator_id: オペレーターID
            existing_assignments: 既存の割り当て [(start_hour, end_hour), ...]
        
        Returns:
            利用可能な時間スロットのリスト [(start_hour, end_hour), ...]
        """
        operator = self.operator_map.get(operator_id)
        if not operator:
            return []
        
        # 勤務時間を取得
        work_start = operator.available_hours[0].hour
        work_end = operator.available_hours[1].hour
        
        if not existing_assignments:
            return [(work_start, work_end)]
        
        # 既存の割り当てをソート
        sorted_assignments = sorted(existing_assignments, key=lambda x: x[0])
        
        available_slots = []
        current_time = work_start
        
        for start, end in sorted_assignments:
            if current_time < start:
                available_slots.append((current_time, start))
            current_time = max(current_time, end)
        
        # 最後の割り当て後に空き時間があれば追加
        if current_time < work_end:
            available_slots.append((current_time, work_end))
        
        return available_slots
    
    def can_fit_task(self, task_hours: int, available_slots: List[Tuple[int, int]]) -> Optional[int]:
        """
        タスクが利用可能なスロットに収まるかチェックし、可能なら開始時間を返す
        
        Args:
            task_hours: タスクの必要時間
            available_slots: 利用可能な時間スロット
        
        Returns:
            割り当て可能な開始時間、不可能な場合はNone
        """
        for start, end in available_slots:
            if end - start >= task_hours:
                return start
        
        return None
    
    def calculate_priority_score(self, task: Task) -> float:
        """タスクの優先度スコアを計算"""
        score = 0.0
        
        # 優先度による基本スコア
        priority_scores = {
            "LOW": 1.0,
            "MEDIUM": 2.0,
            "HIGH": 3.0,
            "URGENT": 4.0
        }
        score += priority_scores.get(task.priority.name, 2.0)
        
        # 納期による追加スコア
        if task.deadline:
            days_until = task.days_until_deadline()
            if days_until is not None:
                if days_until <= 1:
                    score += 3.0
                elif days_until <= 3:
                    score += 2.0
                elif days_until <= 7:
                    score += 1.0
        
        # 工数による調整（短いタスクを優先）
        if task.required_hours <= 2:
            score += 0.5
        
        return score
    
    def get_algorithm_parameters(self) -> Dict[str, any]:
        """アルゴリズム固有のパラメータを取得（オーバーライド可能）"""
        return {}
    
    def validate_result(self, result: ScheduleResult) -> Tuple[bool, List[str]]:
        """
        スケジュール結果の妥当性を検証
        
        Returns:
            (検証成功フラグ, エラーメッセージのリスト)
        """
        errors = []
        
        # オペレーターごとの割り当てをチェック
        operator_assignments = {}
        for assignment in result.assignments:
            if assignment.operator_id not in operator_assignments:
                operator_assignments[assignment.operator_id] = []
            operator_assignments[assignment.operator_id].append(assignment)
        
        # 各オペレーターの制約チェック
        for operator_id, assignments in operator_assignments.items():
            operator = self.operator_map.get(operator_id)
            if not operator:
                errors.append(f"Unknown operator ID: {operator_id}")
                continue
            
            # 時間の重複チェック
            sorted_assignments = sorted(assignments, key=lambda a: a.start_hour)
            for i in range(len(sorted_assignments) - 1):
                if sorted_assignments[i].end_hour > sorted_assignments[i + 1].start_hour:
                    errors.append(
                        f"Time overlap for operator {operator_id}: "
                        f"Task {sorted_assignments[i].task_id} and {sorted_assignments[i + 1].task_id}"
                    )
            
            # 勤務時間内チェック
            work_start = operator.available_hours[0].hour
            work_end = operator.available_hours[1].hour
            
            for assignment in assignments:
                if assignment.start_hour < work_start or assignment.end_hour > work_end:
                    errors.append(
                        f"Assignment outside working hours for operator {operator_id}: "
                        f"Task {assignment.task_id} ({assignment.start_hour}-{assignment.end_hour})"
                    )
        
        # タスクの重複割り当てチェック
        assigned_tasks = {}
        for assignment in result.assignments:
            if assignment.task_id in assigned_tasks:
                errors.append(f"Task {assignment.task_id} is assigned multiple times")
            assigned_tasks[assignment.task_id] = assignment
        
        return len(errors) == 0, errors