# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project called "center-joballocation" - a job allocation optimization demo using multiple algorithms. The project uses Poetry for dependency management and implements various optimization algorithms for operator task assignment.

## Development Commands

### Setup and Dependencies
- Install dependencies: `poetry install`
- Add a new dependency: `poetry add <package>`
- Add a dev dependency: `poetry add --group dev <package>`

### Running Code
- Run Python scripts: `poetry run python <script.py>`
- Enter Poetry shell: `poetry shell`
- Launch Streamlit app: `poetry run python main.py`
- Alternative Streamlit launch: `poetry run streamlit run src/ui/app.py`

### Testing
- Run all tests: `poetry run pytest`
- Run tests with coverage: `poetry run pytest --cov=src`
- Run specific test file: `poetry run pytest tests/test_algorithms.py`

### Code Quality
- Format code: `poetry run black src/ tests/`
- Lint code: `poetry run flake8 src/ tests/`
- Type checking: `poetry run mypy src/`
- Sort imports: `poetry run isort src/ tests/`
- Run all quality checks: `poetry run black src/ tests/ && poetry run flake8 src/ tests/ && poetry run mypy src/ && poetry run isort src/ tests/`

### Building and Packaging
- Build the project: `poetry build`

## Project Structure

```
center-joballocation/
├── src/
│   ├── algorithms/          # Optimization algorithms
│   │   ├── base.py         # Base class for all algorithms
│   │   ├── linear_programming.py  # PuLP-based LP solver
│   │   ├── cp_sat.py       # OR-Tools CP-SAT solver
│   │   ├── genetic_algorithm.py   # DEAP-based GA
│   │   ├── heuristic.py    # Greedy heuristic methods
│   │   └── deferred_acceptance.py # Stable matching
│   ├── data/               # Data loading and validation
│   │   ├── operator_loader.py     # Load operator data
│   │   ├── task_loader.py  # Load task data
│   │   └── validators.py   # Data validation
│   ├── models/             # Data models
│   │   ├── operator.py     # Operator data model
│   │   ├── task.py         # Task data model
│   │   └── schedule.py     # Schedule result model
│   ├── ui/                 # Streamlit web interface
│   │   ├── app.py          # Main Streamlit app
│   │   ├── components.py   # UI components
│   │   └── visualization.py # Charts and visualizations
│   └── utils/              # Utility functions
│       ├── scheduler.py    # Algorithm orchestration
│       ├── metrics.py      # Performance metrics
│       └── export.py       # Result export functions
├── data/                   # Sample data files
├── tests/                  # Test files
├── main.py                 # Entry point
└── pyproject.toml          # Dependencies and config
```

## Architecture Details

### Algorithm Framework
- All algorithms inherit from `BaseAlgorithm` class in `src/algorithms/base.py`
- Unified interface for different optimization approaches
- Standardized result format for comparison
- Extensible design for adding new algorithms

### Data Flow
1. Data loading from CSV/Excel/JSON files
2. Validation and preprocessing
3. Algorithm execution with unified parameters
4. Result aggregation and metrics calculation
5. Visualization and export

### Key Components
- **Scheduler**: Orchestrates algorithm execution and manages results
- **Metrics**: Calculates performance indicators (utilization, idle time, etc.)
- **Validators**: Ensures data integrity and consistency
- **Export**: Handles multiple output formats

## Testing Strategy

The project uses pytest for testing with the following structure:
- `test_data_loaders.py`: Tests for data loading and validation
- `test_algorithms.py`: Tests for optimization algorithms
- `test_scheduler.py`: Integration tests for scheduling workflow

## Python Version

The project requires Python 3.11 or higher as specified in pyproject.toml.

## Key Dependencies

- **streamlit**: Web interface framework
- **pandas**: Data manipulation and analysis
- **pulp**: Linear programming solver
- **ortools**: Google's optimization tools (CP-SAT)
- **deap**: Distributed Evolutionary Algorithms
- **matplotlib/plotly**: Visualization libraries
- **openpyxl**: Excel file handling