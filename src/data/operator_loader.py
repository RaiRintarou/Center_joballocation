#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Union, Optional
from datetime import time

from ..models import Operator


class OperatorLoader:
    """オペレーターデータを各種ファイル形式から読み込むクラス"""

    @staticmethod
    def load_from_file(file_path: Union[str, Path]) -> List[Operator]:
        """ファイルパスから自動的にフォーマットを判定して読み込み"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()

        if suffix == ".csv":
            return OperatorLoader.load_from_csv(file_path)
        elif suffix in [".xlsx", ".xls"]:
            return OperatorLoader.load_from_excel(file_path)
        elif suffix == ".json":
            return OperatorLoader.load_from_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    @staticmethod
    def load_from_uploaded_file(uploaded_file) -> List[Operator]:
        """Streamlitでアップロードされたファイルから読み込み"""
        if uploaded_file is None:
            raise ValueError("No file uploaded")

        file_name = uploaded_file.name
        suffix = Path(file_name).suffix.lower()

        if suffix == ".csv":
            df = pd.read_csv(uploaded_file)
            return OperatorLoader._dataframe_to_operators(df)
        elif suffix in [".xlsx", ".xls"]:
            df = pd.read_excel(uploaded_file)
            return OperatorLoader._dataframe_to_operators(df)
        elif suffix == ".json":
            content = uploaded_file.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            data = json.loads(content)

            if isinstance(data, dict) and "operators" in data:
                data = data["operators"]

            operators = []
            for item in data:
                operator = Operator.from_dict(item)
                operators.append(operator)

            return operators
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    @staticmethod
    def load_from_csv(file_path: Union[str, Path]) -> List[Operator]:
        """CSVファイルからオペレーターデータを読み込み"""
        df = pd.read_csv(file_path)
        return OperatorLoader._dataframe_to_operators(df)

    @staticmethod
    def load_from_excel(
        file_path: Union[str, Path], sheet_name: str = 0
    ) -> List[Operator]:
        """Excelファイルからオペレーターデータを読み込み"""
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        return OperatorLoader._dataframe_to_operators(df)

    @staticmethod
    def load_from_json(file_path: Union[str, Path]) -> List[Operator]:
        """JSONファイルからオペレーターデータを読み込み"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict) and "operators" in data:
            data = data["operators"]

        operators = []
        for item in data:
            operator = Operator.from_dict(item)
            operators.append(operator)

        return operators

    @staticmethod
    def _dataframe_to_operators(df: pd.DataFrame) -> List[Operator]:
        """DataFrameをOperatorオブジェクトのリストに変換"""
        required_columns = ["operator_id", "name"]

        # カラム名の正規化（大文字小文字、スペースを考慮）
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

        # 必須カラムの確認
        missing_columns = []
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        operators = []

        for _, row in df.iterrows():
            operator_data = {
                "operator_id": str(row["operator_id"]),
                "name": str(row["name"]),
            }

            # スキルセットの処理
            if "skill_set" in df.columns and pd.notna(row["skill_set"]):
                skill_str = str(row["skill_set"])
                # JSON配列形式をパース
                try:
                    import ast

                    skills = ast.literal_eval(skill_str)
                    if isinstance(skills, list):
                        operator_data["skill_set"] = skills
                    else:
                        # カンマ区切りまたはセミコロン区切りで分割
                        skills = [
                            s.strip()
                            for s in skill_str.replace(";", ",").split(",")
                            if s.strip()
                        ]
                        operator_data["skill_set"] = skills
                except:
                    # カンマ区切りまたはセミコロン区切りで分割
                    skills = [
                        s.strip()
                        for s in skill_str.replace(";", ",").split(",")
                        if s.strip()
                    ]
                    operator_data["skill_set"] = skills
            elif "skills" in df.columns and pd.notna(row["skills"]):
                skill_str = str(row["skills"])
                try:
                    import ast

                    skills = ast.literal_eval(skill_str)
                    if isinstance(skills, list):
                        operator_data["skill_set"] = skills
                    else:
                        skills = [
                            s.strip()
                            for s in skill_str.replace(";", ",").split(",")
                            if s.strip()
                        ]
                        operator_data["skill_set"] = skills
                except:
                    skills = [
                        s.strip()
                        for s in skill_str.replace(";", ",").split(",")
                        if s.strip()
                    ]
                    operator_data["skill_set"] = skills

            # 勤務可能時間帯の処理
            available_hours = None

            if "available_hours" in df.columns and pd.notna(row["available_hours"]):
                hours_str = str(row["available_hours"])
                # JSON配列形式をパース
                try:
                    import ast

                    hours_list = ast.literal_eval(hours_str)
                    if isinstance(hours_list, list) and len(hours_list) == 2:
                        available_hours = hours_list
                    else:
                        available_hours = OperatorLoader._parse_hours(hours_str)
                except:
                    available_hours = OperatorLoader._parse_hours(hours_str)
            elif "start_time" in df.columns and "end_time" in df.columns:
                if pd.notna(row["start_time"]) and pd.notna(row["end_time"]):
                    start = OperatorLoader._parse_time(str(row["start_time"]))
                    end = OperatorLoader._parse_time(str(row["end_time"]))
                    if start and end:
                        available_hours = [
                            start.strftime("%H:%M"),
                            end.strftime("%H:%M"),
                        ]

            if available_hours:
                operator_data["available_hours"] = available_hours

            operator = Operator.from_dict(operator_data)
            operators.append(operator)

        return operators

    @staticmethod
    def _parse_hours(hours_str: str) -> Optional[List[str]]:
        """時間帯文字列をパース（例: "9:00-17:00" -> ["09:00", "17:00"]）"""
        hours_str = hours_str.strip()

        # ハイフンまたはチルダで分割
        for separator in ["-", "~", "〜"]:
            if separator in hours_str:
                parts = hours_str.split(separator)
                if len(parts) == 2:
                    start = OperatorLoader._parse_time(parts[0].strip())
                    end = OperatorLoader._parse_time(parts[1].strip())
                    if start and end:
                        return [start.strftime("%H:%M"), end.strftime("%H:%M")]

        return None

    @staticmethod
    def _parse_time(time_str: str) -> Optional[time]:
        """時刻文字列をtimeオブジェクトに変換"""
        time_str = time_str.strip()

        # 各種フォーマットを試す
        formats = [
            "%H:%M",
            "%H:%M:%S",
            "%I:%M %p",
            "%I:%M%p",
            "%H時%M分",
            "%H時",
        ]

        for fmt in formats:
            try:
                parsed_time = pd.to_datetime(time_str, format=fmt).time()
                return parsed_time
            except:
                continue

        # 数字のみの場合（例: "9" -> "09:00"）
        try:
            hour = int(time_str)
            if 0 <= hour <= 23:
                return time(hour, 0)
        except:
            pass

        return None

    @staticmethod
    def save_to_csv(operators: List[Operator], file_path: Union[str, Path]):
        """オペレーターリストをCSVファイルに保存"""
        data = []
        for op in operators:
            data.append(
                {
                    "operator_id": op.operator_id,
                    "name": op.name,
                    "skill_set": ", ".join(op.skill_set),
                    "available_hours": f"{op.available_hours[0].strftime('%H:%M')}-{op.available_hours[1].strftime('%H:%M')}",
                }
            )

        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False, encoding="utf-8")

    @staticmethod
    def save_to_json(operators: List[Operator], file_path: Union[str, Path]):
        """オペレーターリストをJSONファイルに保存"""
        data = {"operators": [op.to_dict() for op in operators]}

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
