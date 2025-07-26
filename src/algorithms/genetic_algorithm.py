#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import random
from typing import Dict, List, Tuple
from deap import base, creator, tools, algorithms
import numpy as np

from .base import OptimizationAlgorithm
from ..models import AlgorithmType, ScheduleResult


class GeneticAlgorithmOptimizer(OptimizationAlgorithm):
    """Genetic Algorithm using DEAP library"""
    
    def __init__(self, population_size=50, generations=100, crossover_prob=0.7, mutation_prob=0.2):
        super().__init__(AlgorithmType.GENETIC_ALGORITHM)
        self.population_size = population_size
        self.generations = generations
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
        self.toolbox = None
        self.stats = None
        self.logbook = None
        
    def _optimize(self) -> ScheduleResult:
        """Run genetic algorithm optimization"""
        # Setup DEAP components
        self._setup_deap()
        
        # Initialize population
        population = self.toolbox.population(n=self.population_size)
        
        # Setup statistics
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("min", np.min)
        stats.register("max", np.max)
        
        # Run genetic algorithm
        population, logbook = algorithms.eaSimple(
            population, self.toolbox,
            cxpb=self.crossover_prob,
            mutpb=self.mutation_prob,
            ngen=self.generations,
            stats=stats,
            verbose=False
        )
        
        # Get best solution
        best_individual = tools.selBest(population, 1)[0]
        
        # Create result
        result = ScheduleResult(algorithm_type=self.algorithm_type)
        self._decode_individual(best_individual, result)
        
        self.stats = stats
        self.logbook = logbook
        
        return result
    
    def _setup_deap(self):
        """Setup DEAP genetic algorithm components"""
        # Create fitness and individual classes if they don't exist
        if not hasattr(creator, "FitnessMax"):
            creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        if not hasattr(creator, "Individual"):
            creator.create("Individual", list, fitness=creator.FitnessMax)
        
        # Create toolbox
        self.toolbox = base.Toolbox()
        
        # Register genetic operators
        # Gene structure: (operator_index, start_hour)
        # -1 for operator_index means unassigned task
        self.toolbox.register("gene", self._create_gene)
        self.toolbox.register("individual", tools.initRepeat, creator.Individual, 
                             self.toolbox.gene, len(self.tasks))
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        
        # Register genetic operations
        self.toolbox.register("evaluate", self._evaluate_individual)
        self.toolbox.register("mate", self._crossover)
        self.toolbox.register("mutate", self._mutate)
        self.toolbox.register("select", tools.selTournament, tournsize=3)
    
    def _create_gene(self) -> Tuple[int, int]:
        """Create a random gene for task assignment"""
        # 80% chance to assign, 20% chance to leave unassigned
        if random.random() < 0.8:
            operator_index = random.randint(0, len(self.operators) - 1)
            # Working hours: 9-16 (assuming 8-hour work day)
            start_hour = random.randint(9, 16)
        else:
            operator_index = -1  # Unassigned
            start_hour = 0
        
        return (operator_index, start_hour)
    
    def _evaluate_individual(self, individual: List[Tuple[int, int]]) -> Tuple[float]:
        """Evaluate fitness of an individual"""
        # Initialize penalty and value
        penalty = 0.0
        total_value = 0.0
        
        # Track operator schedules
        operator_schedules = {i: [] for i in range(len(self.operators))}
        
        # Process each task assignment
        for task_idx, (operator_idx, start_hour) in enumerate(individual):
            if operator_idx == -1:  # Unassigned task
                continue
                
            task = self.tasks[task_idx]
            operator = self.operators[operator_idx]
            
            # Check skill compatibility
            if not self.can_assign(operator.operator_id, task.task_id):
                penalty += 100.0
                continue
            
            # Check working hours
            work_start = operator.available_hours[0].hour
            work_end = operator.available_hours[1].hour
            end_hour = start_hour + task.required_hours
            
            if start_hour < work_start or end_hour > work_end:
                penalty += 50.0
                continue
            
            # Check for time conflicts
            conflicts = False
            for existing_start, existing_end in operator_schedules[operator_idx]:
                if not (end_hour <= existing_start or start_hour >= existing_end):
                    conflicts = True
                    break
            
            if conflicts:
                penalty += 75.0
                continue
            
            # Valid assignment
            operator_schedules[operator_idx].append((start_hour, end_hour))
            
            # Calculate task value
            task_value = 10.0 + self.calculate_priority_score(task)
            total_value += task_value
        
        # Check total working hours for each operator
        for operator_idx, schedule in operator_schedules.items():
            total_hours = sum(end - start for start, end in schedule)
            max_hours = self.operators[operator_idx].get_available_hours()
            if total_hours > max_hours:
                penalty += (total_hours - max_hours) * 20.0
        
        # Fitness = value - penalty
        fitness = max(0.0, total_value - penalty)
        return (fitness,)
    
    def _crossover(self, parent1: List[Tuple[int, int]], 
                  parent2: List[Tuple[int, int]]) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """Uniform crossover"""
        child1 = parent1.copy()
        child2 = parent2.copy()
        
        for i in range(len(parent1)):
            if random.random() < 0.5:
                child1[i], child2[i] = child2[i], child1[i]
        
        return child1, child2
    
    def _mutate(self, individual: List[Tuple[int, int]]) -> Tuple[List[Tuple[int, int]]]:
        """Random gene replacement mutation"""
        mutated = individual.copy()
        
        for i in range(len(mutated)):
            if random.random() < 0.1:  # 10% chance to mutate each gene
                # Replace with new random gene
                mutated[i] = self._create_gene()
        
        return (mutated,)
    
    def _decode_individual(self, individual: List[Tuple[int, int]], result: ScheduleResult):
        """Decode individual into valid schedule result"""
        # Track operator schedules to avoid conflicts
        operator_schedules = {i: [] for i in range(len(self.operators))}
        
        for task_idx, (operator_idx, start_hour) in enumerate(individual):
            if operator_idx == -1:  # Unassigned task
                continue
                
            task = self.tasks[task_idx]
            operator = self.operators[operator_idx]
            
            # Validate assignment
            if not self.can_assign(operator.operator_id, task.task_id):
                continue
            
            work_start = operator.available_hours[0].hour
            work_end = operator.available_hours[1].hour
            end_hour = start_hour + task.required_hours
            
            if start_hour < work_start or end_hour > work_end:
                continue
            
            # Check for time conflicts
            conflicts = False
            for existing_start, existing_end in operator_schedules[operator_idx]:
                if not (end_hour <= existing_start or start_hour >= existing_end):
                    conflicts = True
                    break
            
            if conflicts:
                continue
            
            # Add valid assignment
            operator_schedules[operator_idx].append((start_hour, end_hour))
            result.add_assignment(
                operator_id=operator.operator_id,
                task_id=task.task_id,
                start_hour=start_hour,
                duration_hours=task.required_hours
            )
    
    def get_algorithm_parameters(self) -> Dict[str, any]:
        """Get algorithm parameters and statistics"""
        params = {
            "algorithm": "Genetic Algorithm (DEAP)",
            "population_size": self.population_size,
            "generations": self.generations,
            "crossover_probability": self.crossover_prob,
            "mutation_probability": self.mutation_prob,
            "selection": "Tournament Selection (size=3)",
            "crossover": "Uniform Crossover",
            "mutation": "Random Gene Replacement"
        }
        
        if self.logbook:
            final_stats = self.logbook.select("max")[-1] if self.logbook else None
            if final_stats:
                params["final_best_fitness"] = final_stats
        
        return params