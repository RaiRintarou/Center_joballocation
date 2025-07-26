#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Dict, Optional
import pulp

from .base import OptimizationAlgorithm
from ..models import AlgorithmType, ScheduleResult, Operator, Task


class LinearProgrammingOptimizer(OptimizationAlgorithm):
    """線形計画法（PuLP）を使用した最適化アルゴリズム"""
    
    def __init__(self):
        super().__init__(AlgorithmType.LINEAR_PROGRAMMING)
        self.problem = None
        self.assignment_vars = {}
        self.start_time_vars = {}
    
    def _optimize(self) -> ScheduleResult:
        """線形計画法による最適化を実行"""
        # 問題の初期化
        self.problem = pulp.LpProblem("JobAllocation", pulp.LpMaximize)
        
        # 決定変数の作成
        self._create_variables()
        
        # 制約条件の追加
        self._add_constraints()
        
        # 目的関数の設定
        self._set_objective()
        
        # 最適化の実行
        status = self.problem.solve(pulp.PULP_CBC_CMD(msg=0))
        
        # 結果の作成
        result = ScheduleResult(algorithm_type=self.algorithm_type)
        
        if status == pulp.LpStatusOptimal:
            # 最適解から割り当てを抽出
            self._extract_assignments(result)
        
        return result
    
    def _create_variables(self):
        """決定変数を作成"""
        # x_{i,j} = 1 if task j is assigned to operator i, 0 otherwise
        for operator in self.operators:
            for task in self.tasks:
                var_name = f"x_{operator.operator_id}_{task.task_id}"
                self.assignment_vars[(operator.operator_id, task.task_id)] = \
                    pulp.LpVariable(var_name, cat='Binary')
        
        # s_{j} = start time of task j (hour of the day)
        for task in self.tasks:
            var_name = f"s_{task.task_id}"
            # 開始時刻は0-23の範囲
            self.start_time_vars[task.task_id] = \
                pulp.LpVariable(var_name, lowBound=0, upBound=23, cat='Continuous')
    
    def _add_constraints(self):
        """制約条件を追加"""
        # 1. 各タスクは最大1人のオペレーターに割り当てられる
        for task in self.tasks:
            constraint = pulp.lpSum([
                self.assignment_vars[(op.operator_id, task.task_id)]
                for op in self.operators
            ]) <= 1
            self.problem += constraint, f"OneOperatorPerTask_{task.task_id}"
        
        # 2. スキル制約：オペレーターが必要なスキルを持っている場合のみ割り当て可能
        for operator in self.operators:
            for task in self.tasks:
                if not self.can_assign(operator.operator_id, task.task_id):
                    self.problem += self.assignment_vars[(operator.operator_id, task.task_id)] == 0, \
                        f"SkillConstraint_{operator.operator_id}_{task.task_id}"
        
        # 3. 勤務時間制約：タスクはオペレーターの勤務時間内に収まる必要がある
        for operator in self.operators:
            for task in self.tasks:
                work_start = operator.available_hours[0].hour
                work_end = operator.available_hours[1].hour
                
                # タスクが割り当てられている場合、開始時刻が勤務時間内
                self.problem += self.start_time_vars[task.task_id] >= work_start - \
                    (1 - self.assignment_vars[(operator.operator_id, task.task_id)]) * 24, \
                    f"WorkStart_{operator.operator_id}_{task.task_id}"
                
                # タスクが割り当てられている場合、終了時刻が勤務時間内
                self.problem += self.start_time_vars[task.task_id] + task.required_hours <= work_end + \
                    (1 - self.assignment_vars[(operator.operator_id, task.task_id)]) * 24, \
                    f"WorkEnd_{operator.operator_id}_{task.task_id}"
        
        # 4. 時間の重複防止：同じオペレーターに割り当てられたタスクは重複しない
        for operator in self.operators:
            for i, task1 in enumerate(self.tasks):
                for j, task2 in enumerate(self.tasks):
                    if i < j:  # 各ペアを一度だけチェック
                        # 両方のタスクが同じオペレーターに割り当てられている場合
                        both_assigned = self.assignment_vars[(operator.operator_id, task1.task_id)] + \
                                      self.assignment_vars[(operator.operator_id, task2.task_id)]
                        
                        # task1がtask2より前に終わるか、task2がtask1より前に終わる
                        # Big-M methodを使用（M=24は十分大きい値）
                        M = 24
                        
                        # task1_end <= task2_start OR task2_end <= task1_start
                        # これを線形制約として表現するために、追加の二値変数を使用
                        order_var = pulp.LpVariable(
                            f"order_{operator.operator_id}_{task1.task_id}_{task2.task_id}",
                            cat='Binary'
                        )
                        
                        # order_var = 1 なら task1が先、0ならtask2が先
                        self.problem += self.start_time_vars[task1.task_id] + task1.required_hours <= \
                            self.start_time_vars[task2.task_id] + M * (1 - order_var) + \
                            M * (2 - both_assigned), \
                            f"NoOverlap1_{operator.operator_id}_{task1.task_id}_{task2.task_id}"
                        
                        self.problem += self.start_time_vars[task2.task_id] + task2.required_hours <= \
                            self.start_time_vars[task1.task_id] + M * order_var + \
                            M * (2 - both_assigned), \
                            f"NoOverlap2_{operator.operator_id}_{task1.task_id}_{task2.task_id}"
        
        # 5. 各オペレーターの1日の総作業時間は勤務時間を超えない
        for operator in self.operators:
            total_hours = pulp.lpSum([
                self.assignment_vars[(operator.operator_id, task.task_id)] * task.required_hours
                for task in self.tasks
            ])
            max_hours = operator.get_available_hours()
            self.problem += total_hours <= max_hours, f"MaxHours_{operator.operator_id}"
    
    def _set_objective(self):
        """目的関数を設定"""
        # 目的：割り当てられたタスクの総価値を最大化
        # 価値 = 基本点 + 優先度ボーナス + 納期ボーナス
        objective = 0
        
        for operator in self.operators:
            for task in self.tasks:
                # 基本点：タスクが割り当てられたら1点
                base_value = 1.0
                
                # 優先度ボーナス
                priority_bonus = self.calculate_priority_score(task)
                
                # 総価値
                task_value = base_value + priority_bonus
                
                objective += self.assignment_vars[(operator.operator_id, task.task_id)] * task_value
        
        self.problem += objective, "Maximize_TaskValue"
    
    def _extract_assignments(self, result: ScheduleResult):
        """最適解から割り当てを抽出"""
        for operator in self.operators:
            for task in self.tasks:
                # 割り当て変数の値を確認
                if pulp.value(self.assignment_vars[(operator.operator_id, task.task_id)]) == 1:
                    # 開始時刻を取得
                    start_hour = int(round(pulp.value(self.start_time_vars[task.task_id])))
                    
                    # 割り当てを追加
                    result.add_assignment(
                        operator_id=operator.operator_id,
                        task_id=task.task_id,
                        start_hour=start_hour,
                        duration_hours=task.required_hours
                    )
    
    def get_algorithm_parameters(self) -> Dict[str, any]:
        """アルゴリズム固有のパラメータを取得"""
        params = {
            "solver": "CBC",
            "formulation": "Binary Integer Programming",
            "objective": "Maximize task value with priority weighting"
        }
        
        if self.problem:
            params["num_variables"] = self.problem.numVariables()
            params["num_constraints"] = self.problem.numConstraints()
            if self.problem.status:
                params["solution_status"] = pulp.LpStatus[self.problem.status]
        
        return params