# Job Allocation Optimization System

## Overview

This is a job allocation optimization system that optimizes operator task assignments using multiple algorithms to improve resource allocation efficiency.

### Features

- **Optimization Algorithms**
  - Linear Programming (PuLP)
  - CP-SAT (OR-Tools)  
  - Genetic Algorithm (DEAP)
  - Heuristic Methods
  - Deferred Acceptance (Stable Matching)

- **Data Processing**
  - CSV/Excel/JSON file support
  - Data validation and preprocessing
  - Skill matching functionality

- **Web Interface**
  - Streamlit-based intuitive UI
  - Real-time result display
  - Visualization features

- **Result Output**
  - Detailed report generation
  - Various metrics calculation
  - CSV/Excel/JSON format output

## Setup

### Prerequisites

- Python 3.11 or higher
- Poetry (dependency management)

### Installation Steps

1. Clone the repository
```bash
git clone <repository-url>
cd center-joballocation
```

2. Install dependencies
```bash
poetry install
```

3. Activate virtual environment
```bash
poetry shell
```

## Usage

### Application Launch

1. Start Streamlit app
```bash
poetry run python main.py
```

or

```bash
poetry run streamlit run src/ui/app.py
```

2. Access `http://localhost:8501` in your browser

### Data File Format

#### Operator Data (CSV file)
```csv
operator_id,name,skills,available_hours
OP001,Tanaka Taro,"Python,SQL,Excel",8
OP002,Sato Hanako,"Java,Python,Design",6
```

#### Task Data (CSV file)
```csv
task_id,name,required_skills,workload,priority
T001,Data Analysis,"Python,SQL",4,High
T002,UI Design,"Excel,Design",2,Medium
```

### Sample Data

The project includes sample data:

- `data/sample_operators.csv` - 10 operator records
- `data/sample_tasks.csv` - 30 task records
- `data/skillset_master.csv` - Skill master data

### Basic Workflow

1. Prepare and upload data files
2. Configure algorithm parameters
3. Execute optimization algorithms
4. Review and analyze results
5. Export and download reports

## Project Structure

### Directory Structure

```
center-joballocation/
├── src/
│   ├── algorithms/          # Optimization algorithms
│   │   ├── base.py         # Base class
│   │   ├── linear_programming.py
│   │   ├── cp_sat.py
│   │   ├── genetic_algorithm.py
│   │   ├── heuristic.py
│   │   └── deferred_acceptance.py
│   ├── data/               # Data processing
│   │   ├── operator_loader.py
│   │   ├── task_loader.py
│   │   └── validators.py
│   ├── models/             # Data models
│   │   ├── operator.py
│   │   ├── task.py
│   │   └── schedule.py
│   ├── ui/                 # User interface
│   │   ├── app.py
│   │   ├── components.py
│   │   └── visualization.py
│   └── utils/              # Utilities
│       ├── scheduler.py
│       ├── metrics.py
│       └── export.py
├── data/                   # Sample data
├── tests/                  # Test files
├── main.py                 # Entry point
└── pyproject.toml          # Dependencies
```

### Key Components

#### Algorithm Layer (`src/algorithms/`)
- Implementation of optimization algorithms
- Unified interface through `BaseAlgorithm` class
- Extensible design

#### Data Processing Layer (`src/data/`)
- File loading (CSV/Excel/JSON)
- Data validation and preprocessing
- Skill matching processing

#### UI Layer (`src/ui/`)
- Streamlit-based web interface
- Component-based screen design
- Real-time result display

#### Utility Layer (`src/utils/`)
- Algorithm execution control
- Performance metrics calculation
- Result output functionality

### Design Principles

1. **Modular Design**: Each function implemented as independent modules
2. **Extensibility**: Support for new algorithms and data formats
3. **Usability**: Intuitive web interface
4. **Maintainability**: Structured code and test-driven development

## Development

### Run Tests

```bash
poetry run pytest
```

### Code Quality Checks

```bash
# Format
poetry run black src/ tests/

# Lint
poetry run flake8 src/ tests/

# Type check
poetry run mypy src/

# Sort imports
poetry run isort src/ tests/
```

### Build

```bash
poetry build
```

## License

This project is released under the MIT License.

## Author

Rai Rintarou (ikkmno123@gmail.com)