#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Union, Optional
from datetime import datetime

from ..models import Task, Priority


class TaskLoader:
    """タスクデータを各種ファイル形式から読み込むクラス"""

    @staticmethod
    def load_from_file(file_path: Union[str, Path]) -> List[Task]:
        """ファイルパスから自動的にフォーマットを判定して読み込み"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()

        if suffix == ".csv":
            return TaskLoader.load_from_csv(file_path)
        elif suffix in [".xlsx", ".xls"]:
            return TaskLoader.load_from_excel(file_path)
        elif suffix == ".json":
            return TaskLoader.load_from_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    @staticmethod
    def load_from_uploaded_file(uploaded_file) -> List[Task]:
        """Streamlitでアップロードされたファイルから読み込み"""
        if uploaded_file is None:
            raise ValueError("No file uploaded")

        file_name = uploaded_file.name
        suffix = Path(file_name).suffix.lower()

        try:
            # Reset file pointer to beginning
            uploaded_file.seek(0)
            
            if suffix == ".csv":
                df = pd.read_csv(uploaded_file)
                return TaskLoader._dataframe_to_tasks(df)
            elif suffix in [".xlsx", ".xls"]:
                df = pd.read_excel(uploaded_file)
                return TaskLoader._dataframe_to_tasks(df)
            elif suffix == ".json":
                content = uploaded_file.read()
                if isinstance(content, bytes):
                    content = content.decode("utf-8")
                data = json.loads(content)

                if isinstance(data, dict) and "tasks" in data:
                    data = data["tasks"]

                tasks = []
                for item in data:
                    task = Task.from_dict(item)
                    tasks.append(task)

                return tasks
            else:
                raise ValueError(f"Unsupported file format: {suffix}")
        except Exception as e:
            # Reset file pointer on error for potential retry
            try:
                uploaded_file.seek(0)
            except:
                pass
            raise e

    @staticmethod
    def load_from_csv(file_path: Union[str, Path]) -> List[Task]:
        """CSVファイルからタスクデータを読み込み"""
        df = pd.read_csv(file_path)
        return TaskLoader._dataframe_to_tasks(df)

    @staticmethod
    def load_from_excel(file_path: Union[str, Path], sheet_name: str = 0) -> List[Task]:
        """Excelファイルからタスクデータを読み込み"""
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        return TaskLoader._dataframe_to_tasks(df)

    @staticmethod
    def load_from_json(file_path: Union[str, Path]) -> List[Task]:
        """JSONファイルからタスクデータを読み込み"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict) and "tasks" in data:
            data = data["tasks"]

        tasks = []
        for item in data:
            task = Task.from_dict(item)
            tasks.append(task)

        return tasks

    @staticmethod
    def _dataframe_to_tasks(df: pd.DataFrame) -> List[Task]:
        """DataFrameをTaskオブジェクトのリストに変換"""
        required_columns = ["task_id", "task_name", "estimated_hours"]

        # カラム名の正規化（大文字小文字、スペースを考慮）
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

        # 必須カラムの確認と別名のマッピング
        missing_columns = []
        for col in required_columns:
            if col not in df.columns:
                # 別名のチェック
                if col == "task_name" and "name" in df.columns:
                    df["task_name"] = df["name"]
                elif col == "estimated_hours":
                    if "required_hours" in df.columns:
                        df["estimated_hours"] = df["required_hours"]
                    elif "hours" in df.columns:
                        df["estimated_hours"] = df["hours"]
                    elif "duration" in df.columns:
                        df["estimated_hours"] = df["duration"]
                    elif "time" in df.columns:
                        df["estimated_hours"] = df["time"]
                    else:
                        missing_columns.append(col)
                else:
                    missing_columns.append(col)

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        tasks = []

        for _, row in df.iterrows():
            task_data = {
                "task_id": str(row["task_id"]),
                "name": str(row["task_name"]),
                "required_hours": int(row["estimated_hours"]),
            }

            # タスクタイプの処理（オプション、デフォルト値を設定）
            if "task_type" in df.columns and pd.notna(row["task_type"]):
                task_data["task_type"] = str(row["task_type"])
            else:
                task_data["task_type"] = "general"

            # 納期の処理
            deadline = None
            if "deadline" in df.columns and pd.notna(row["deadline"]):
                deadline = TaskLoader._parse_datetime(row["deadline"])
            elif "due_date" in df.columns and pd.notna(row["due_date"]):
                deadline = TaskLoader._parse_datetime(row["due_date"])

            if deadline:
                task_data["deadline"] = deadline.isoformat()

            # 優先度の処理
            if "priority" in df.columns and pd.notna(row["priority"]):
                task_data["priority"] = str(row["priority"])

            # 必要スキルの処理
            if "required_skills" in df.columns and pd.notna(row["required_skills"]):
                skills_str = str(row["required_skills"])
                # JSON配列形式をパース
                try:
                    import ast

                    skills = ast.literal_eval(skills_str)
                    if isinstance(skills, list) and len(skills) > 0:
                        task_data["required_skill"] = skills[0]  # 最初のスキルを使用
                    else:
                        task_data["required_skill"] = skills_str.strip()
                except:
                    task_data["required_skill"] = skills_str.strip()
            elif "required_skill" in df.columns and pd.notna(row["required_skill"]):
                task_data["required_skill"] = str(row["required_skill"]).strip()
            elif "skill" in df.columns and pd.notna(row["skill"]):
                task_data["required_skill"] = str(row["skill"]).strip()

            try:
                task = Task.from_dict(task_data)
                tasks.append(task)
            except ValueError as e:
                print(
                    f"Warning: Skipping task {task_data['task_id']} due to error: {e}"
                )
                continue

        return tasks

    @staticmethod
    def _parse_datetime(value) -> Optional[datetime]:
        """様々な形式の日時データをdatetimeオブジェクトに変換"""
        if isinstance(value, datetime):
            return value

        if isinstance(value, pd.Timestamp):
            return value.to_pydatetime()

        if isinstance(value, str):
            value = value.strip()

            # 各種日付フォーマットを試す
            formats = [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
                "%Y年%m月%d日",
                "%Y年%m月%d日 %H時%M分",
                "%m/%d/%Y",
                "%d/%m/%Y",
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except:
                    continue

            # pandasのto_datetimeを試す
            try:
                return pd.to_datetime(value).to_pydatetime()
            except:
                pass

        return None

    @staticmethod
    def save_to_csv(tasks: List[Task], file_path: Union[str, Path]):
        """タスクリストをCSVファイルに保存"""
        data = []
        for task in tasks:
            data.append(
                {
                    "task_id": task.task_id,
                    "name": task.name,
                    "task_type": task.task_type,
                    "required_hours": task.required_hours,
                    "deadline": (
                        task.deadline.strftime("%Y-%m-%d") if task.deadline else ""
                    ),
                    "priority": task.priority.name,
                    "required_skill": task.required_skill or "",
                }
            )

        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False, encoding="utf-8")

    @staticmethod
    def save_to_json(tasks: List[Task], file_path: Union[str, Path]):
        """タスクリストをJSONファイルに保存"""
        data = {"tasks": [task.to_dict() for task in tasks]}

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def generate_sample_tasks(count: int = 20) -> List[Task]:
        """テスト用のサンプルタスクを生成"""
        import random
        from datetime import timedelta

        task_types = [
            "データ入力",
            "資料作成",
            "電話対応",
            "メール対応",
            "レポート作成",
            "会議準備",
        ]
        skills = ["Excel", "Word", "電話対応", "メール", "データ分析", None]
        priorities = [Priority.LOW, Priority.MEDIUM, Priority.HIGH, Priority.URGENT]

        tasks = []
        base_date = datetime.now()

        for i in range(count):
            task_id = f"TASK_{i+1:03d}"
            name = f"{random.choice(task_types)}_{i+1}"
            task_type = random.choice(task_types)
            required_hours = random.randint(1, 8)

            # 30%の確率で納期を設定
            deadline = None
            if random.random() < 0.3:
                days_ahead = random.randint(1, 14)
                deadline = base_date + timedelta(days=days_ahead)

            priority = random.choice(priorities)
            required_skill = random.choice(skills)

            task = Task(
                task_id=task_id,
                name=name,
                task_type=task_type,
                required_hours=required_hours,
                deadline=deadline,
                priority=priority,
                required_skill=required_skill,
            )

            tasks.append(task)

        return tasks
