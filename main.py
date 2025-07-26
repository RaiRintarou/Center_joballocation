#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Job Allocation Optimization Demo - Main Entry Point

This script launches the Streamlit application and handles
command line arguments and configuration file loading.
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Load configuration file
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    default_config = {
        "app": {
            "title": "Job Allocation Optimization Demo",
            "port": 8501,
            "host": "localhost"
        },
        "data": {
            "default_operators_file": "data/sample_operators.csv",
            "default_tasks_file": "data/sample_tasks.csv",
            "skillset_master_file": "data/skillset_master.csv"
        },
        "algorithms": {
            "enabled": ["linear_programming", "cp_sat", "genetic_algorithm", "heuristic", "deferred_acceptance"],
            "default": "linear_programming"
        },
        "ui": {
            "theme": "light",
            "sidebar_expanded": True,
            "show_metrics": True
        }
    }
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with default configuration
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                    elif isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if sub_key not in config[key]:
                                config[key][sub_key] = sub_value
                return config
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Configuration file loading error: {e}")
            print("Using default configuration.")
    
    return default_config


def create_default_config(config_path: str = "config.json"):
    """Create default configuration file
    
    Args:
        config_path: Path to create configuration file
    """
    default_config = load_config()
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, ensure_ascii=False, indent=2)
    
    print(f"Default configuration file created: {config_path}")


def check_dependencies():
    """Check required dependencies"""
    required_packages = [
        "streamlit",
        "pandas",
        "pulp",
        "ortools",
        "deap",
        "matplotlib",
        "plotly",
        "openpyxl"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("The following packages are not installed:")
        for package in missing_packages:
            print(f"  - {package}")
        print(f"\nInstall them with: poetry add {' '.join(missing_packages)}")
        return False
    
    return True


def setup_environment():
    """Setup environment"""
    # Get project root directory
    project_root = Path(__file__).parent
    
    # Add to Python path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Create required directories
    directories = [
        project_root / "data",
        project_root / "logs",
        project_root / "exports"
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True)


def run_streamlit_app(config: Dict[str, Any], debug: bool = False):
    """Launch Streamlit application
    
    Args:
        config: Configuration dictionary
        debug: Debug mode flag
    """
    app_path = "src/ui/app.py"
    
    if not os.path.exists(app_path):
        print(f"Error: Application file not found: {app_path}")
        sys.exit(1)
    
    # Build Streamlit command
    cmd = [
        "streamlit", "run", app_path,
        "--server.port", str(config["app"]["port"]),
        "--server.address", config["app"]["host"]
    ]
    
    if debug:
        cmd.extend(["--logger.level", "debug"])
    
    # Pass configuration as environment variable
    env = os.environ.copy()
    env["JOB_ALLOCATION_CONFIG"] = json.dumps(config)
    
    print(f"Starting Streamlit application...")
    print(f"URL: http://{config['app']['host']}:{config['app']['port']}")
    
    try:
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        print("\nShutting down application.")
    except FileNotFoundError:
        print("Error: Streamlit is not installed.")
        print("Install it with: poetry add streamlit")
        sys.exit(1)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Job Allocation Optimization Demo Application"
    )
    
    parser.add_argument(
        "--config", "-c",
        default="config.json",
        help="Configuration file path (default: config.json)"
    )
    
    parser.add_argument(
        "--create-config",
        action="store_true",
        help="Create default configuration file and exit"
    )
    
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check dependencies and exit"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Launch in debug mode"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        help="Specify port number (overrides config file)"
    )
    
    parser.add_argument(
        "--host",
        help="Specify host address (overrides config file)"
    )
    
    args = parser.parse_args()
    
    # Create configuration file only
    if args.create_config:
        create_default_config(args.config)
        return
    
    # Check dependencies only
    if args.check_deps:
        if check_dependencies():
            print("All dependencies are satisfied.")
        sys.exit(0)
    
    # Setup environment
    setup_environment()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Load configuration file
    config = load_config(args.config)
    
    # Override configuration with command line arguments
    if args.port:
        config["app"]["port"] = args.port
    
    if args.host:
        config["app"]["host"] = args.host
    
    # Launch Streamlit app
    run_streamlit_app(config, args.debug)


if __name__ == "__main__":
    main()