# Data Format Specification

This document defines the data formats used in the Center Job Allocation system.

## Operator Data Format

**File**: `operators.csv`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| operator_id | string | Unique identifier for operator | "OP001" |
| name | string | Operator's full name | "田中太郎" |
| skill_set | JSON array | List of skill IDs the operator possesses | ["SKILL001", "SKILL002"] |
| available_hours | JSON array | Working hours in [start, end] format | ["09:00", "17:00"] |

**Example Row**:
```csv
OP001,田中太郎,"[""SKILL001"", ""SKILL002""]","[""09:00"", ""17:00""]"
```

## Task Data Format

**File**: `tasks.csv`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| task_id | string | Unique identifier for task | "TASK001" |
| task_name | string | Descriptive name of the task | "Webアプリケーション開発" |
| required_skills | JSON array | List of required skill IDs | ["SKILL007"] |
| estimated_hours | integer | Estimated hours to complete | 8 |
| priority | string | Task priority level | "high", "medium", "low" |
| deadline | date | Task deadline in YYYY-MM-DD format | "2024-01-15" |

**Example Row**:
```csv
TASK001,Webアプリケーション開発,"[""SKILL007""]",8,high,2024-01-15
```

## Skill Master Data Format

**File**: `skillset_master.csv`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| skill_id | string | Unique identifier for skill | "SKILL001" |
| skill_name | string | Human-readable skill name | "Python" |
| category | string | Skill category | "プログラミング言語" |
| description | string | Detailed skill description | "Pythonプログラミング言語" |

**Example Row**:
```csv
SKILL001,Python,プログラミング言語,Pythonプログラミング言語
```

## Data Validation Rules

### Operators
- `operator_id`: Must be unique, format: "OP" + 3-digit number
- `skill_set`: Must contain valid skill IDs from skillset_master
- `available_hours`: Must be valid time format (HH:MM)

### Tasks
- `task_id`: Must be unique, format: "TASK" + 3-digit number
- `required_skills`: Must contain valid skill IDs from skillset_master
- `estimated_hours`: Must be positive integer
- `priority`: Must be one of: "high", "medium", "low"
- `deadline`: Must be valid date in YYYY-MM-DD format

### Skills
- `skill_id`: Must be unique, format: "SKILL" + 3-digit number
- All fields are required and must be non-empty strings

## File Encoding
- All CSV files should use UTF-8 encoding
- JSON arrays within CSV cells must use double quotes for strings
- CSV delimiter: comma (,)
- Text qualifier: double quotes (")

## Supported Input Formats
- CSV (.csv)
- Excel (.xlsx, .xls)
- JSON (.json)

Note: When using Excel or JSON formats, the data structure should match the CSV column specifications above.