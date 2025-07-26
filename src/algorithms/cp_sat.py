#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Dict
from ortools.sat.python import cp_model

from .base import OptimizationAlgorithm
from ..models import AlgorithmType, ScheduleResult


class CPSATOptimizer(OptimizationAlgorithm):
    """CP-SAT（制約プログラミング）を使用した最適化アルゴリズム"""
    
    def __init__(self):
        super().__init__(AlgorithmType.CP_SAT)
        self.model = None
        self.solver = None
        self.assignment_vars = {}
        self.start_vars = {}
        self.end_vars = {}
        self.interval_vars = {}
    
    def _optimize(self) -> ScheduleResult:
        """CP-SATによる最適化を実行"""
        # モデルとソルバーの初期化
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        
        # 変数の作成
        self._create_variables()
        
        # 制約条件の追加
        self._add_constraints()
        
        # 目的関数の設定
        self._set_objective()
        
        # 最適化の実行
        status = self.solver.Solve(self.model)
        
        # 結果の作成
        result = ScheduleResult(algorithm_type=self.algorithm_type)
        
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            # 解から割り当てを抽出
            self._extract_assignments(result)
        
        return result
    
    def _create_variables(self):
        """CP-SAT変数を作成"""
        # 各タスクに対して変数を作成
        for task in self.tasks:
            # 開始時刻変数（時間単位）
            self.start_vars[task.task_id] = self.model.NewIntVar(
                0, 23, f"start_{task.task_id}"
            )
            
            # 終了時刻変数
            self.end_vars[task.task_id] = self.model.NewIntVar(
                0, 24, f"end_{task.task_id}"
            )
            
            # タスクごとのオペレーター割り当て変数と区間変数
            self.interval_vars[task.task_id] = {}
            self.assignment_vars[task.task_id] = {}
            
            for operator in self.operators:
                # 割り当て変数（0 or 1）
                self.assignment_vars[task.task_id][operator.operator_id] = \
                    self.model.NewBoolVar(f"assign_{task.task_id}_{operator.operator_id}")
                
                # オプショナル区間変数（割り当てられた場合のみ有効）
                self.interval_vars[task.task_id][operator.operator_id] = \
                    self.model.NewOptionalIntervalVar(
                        self.start_vars[task.task_id],
                        task.required_hours,
                        self.end_vars[task.task_id],
                        self.assignment_vars[task.task_id][operator.operator_id],
                        f"interval_{task.task_id}_{operator.operator_id}"
                    )
    
    def _add_constraints(self):
        """制約条件を追加"""
        # 1. 各タスクは最大1人のオペレーターに割り当てられる
        for task in self.tasks:
            self.model.Add(
                sum(self.assignment_vars[task.task_id][op.operator_id] 
                    for op in self.operators) <= 1
            )
        
        # 2. スキル制約
        for task in self.tasks:
            for operator in self.operators:
                if not self.can_assign(operator.operator_id, task.task_id):
                    self.model.Add(
                        self.assignment_vars[task.task_id][operator.operator_id] == 0
                    )
        
        # 3. 開始時刻と終了時刻の関係
        for task in self.tasks:
            self.model.Add(
                self.end_vars[task.task_id] == 
                self.start_vars[task.task_id] + task.required_hours
            )
        
        # 4. 勤務時間制約
        for task in self.tasks:
            for operator in self.operators:
                work_start = operator.available_hours[0].hour
                work_end = operator.available_hours[1].hour
                
                # タスクが割り当てられている場合のみ制約を適用
                # 開始時刻は勤務開始時刻以降
                self.model.Add(
                    self.start_vars[task.task_id] >= work_start
                ).OnlyEnforceIf(self.assignment_vars[task.task_id][operator.operator_id])
                
                # 終了時刻は勤務終了時刻以前
                self.model.Add(
                    self.end_vars[task.task_id] <= work_end
                ).OnlyEnforceIf(self.assignment_vars[task.task_id][operator.operator_id])
        
        # 5. オペレーターごとの時間重複防止
        for operator in self.operators:
            # 各オペレーターに割り当てられた区間は重複しない
            intervals = [
                self.interval_vars[task.task_id][operator.operator_id]
                for task in self.tasks
            ]
            self.model.AddNoOverlap(intervals)
        
        # 6. 各オペレーターの総作業時間制約
        for operator in self.operators:
            total_hours = sum(
                self.assignment_vars[task.task_id][operator.operator_id] * task.required_hours
                for task in self.tasks
            )
            max_hours = int(operator.get_available_hours())
            self.model.Add(total_hours <= max_hours)
    
    def _set_objective(self):
        """目的関数を設定"""
        # 目的：割り当てられたタスクの総価値を最大化
        objective = []
        
        for task in self.tasks:
            # 基本価値（タスクが割り当てられたら1点）
            base_value = 10  # CP-SATは整数値を使用するため10倍
            
            # 優先度による追加価値
            priority_value = int(self.calculate_priority_score(task) * 10)
            
            # タスクの総価値
            task_value = base_value + priority_value
            
            # 各オペレーターへの割り当てに対して価値を加算
            for operator in self.operators:
                objective.append(
                    self.assignment_vars[task.task_id][operator.operator_id] * task_value
                )
        
        self.model.Maximize(sum(objective))
    
    def _extract_assignments(self, result: ScheduleResult):
        """ソルバーの解から割り当てを抽出"""
        for task in self.tasks:
            for operator in self.operators:
                # 割り当て変数の値を確認
                if self.solver.Value(self.assignment_vars[task.task_id][operator.operator_id]):
                    # 開始時刻を取得
                    start_hour = self.solver.Value(self.start_vars[task.task_id])
                    
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
            "solver": "OR-Tools CP-SAT",
            "formulation": "Constraint Programming",
            "objective": "Maximize task value with priority weighting"
        }
        
        if self.model:
            params["num_variables"] = len(self.start_vars) + len(self.end_vars) + \
                                    sum(len(v) for v in self.assignment_vars.values())
            params["num_constraints"] = self.model.Proto().constraints.__len__()
            
        if self.solver and hasattr(self.solver, 'StatusName'):
            params["solution_status"] = self.solver.StatusName()
            if hasattr(self.solver, 'ObjectiveValue'):
                params["objective_value"] = self.solver.ObjectiveValue()
        
        return params