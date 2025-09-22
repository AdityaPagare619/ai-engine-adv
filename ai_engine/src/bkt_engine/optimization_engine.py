# Enterprise Optimization Engine for Million-User Scale BKT
# Real-time parameter optimization, A/B testing, and performance monitoring

from __future__ import annotations
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import uuid
from collections import defaultdict, deque

@dataclass
class OptimizationMetrics:
    """Metrics for optimization tracking"""
    accuracy: float
    convergence_rate: float
    prediction_variance: float
    calibration_error: float
    student_satisfaction: float
    learning_velocity: float
    retention_rate: float
    engagement_score: float

@dataclass
class ParameterSet:
    """BKT parameter set with metadata"""
    prior_knowledge: float
    learn_rate: float
    slip_rate: float
    guess_rate: float
    decay_rate: float
    version: str
    created_at: datetime
    performance_score: float = 0.0
    total_samples: int = 0
    confidence_interval: Tuple[float, float] = (0.0, 0.0)

class OptimizationStrategy(Enum):
    """Available optimization strategies"""
    BAYESIAN_OPTIMIZATION = "bayesian"
    GENETIC_ALGORITHM = "genetic" 
    GRADIENT_DESCENT = "gradient"
    MULTI_ARMED_BANDIT = "bandit"
    SIMULATED_ANNEALING = "annealing"
    PARTICLE_SWARM = "pso"

@dataclass 
class ABTestConfig:
    """A/B Test configuration"""
    test_id: str
    name: str
    parameter_variants: List[ParameterSet]
    traffic_allocation: List[float]  # Percentage for each variant
    start_time: datetime
    end_time: Optional[datetime]
    minimum_sample_size: int
    significance_level: float = 0.05
    power: float = 0.8
    primary_metric: str = "accuracy"
    secondary_metrics: List[str] = field(default_factory=list)

class RealTimeOptimizer:
    """
    Real-time parameter optimization for enterprise-scale BKT
    Handles millions of concurrent users with minimal performance impact
    """
    
    def __init__(self, optimization_strategy: OptimizationStrategy = OptimizationStrategy.BAYESIAN_OPTIMIZATION):
        self.strategy = optimization_strategy
        self.logger = logging.getLogger(__name__)
        
        # Parameter bounds for optimization
        self.parameter_bounds = {
            'prior_knowledge': (0.1, 0.8),
            'learn_rate': (0.05, 0.6),
            'slip_rate': (0.01, 0.4),
            'guess_rate': (0.05, 0.5),
            'decay_rate': (0.001, 0.2)
        }
        
        # Current best parameters
        self.current_best = ParameterSet(
            prior_knowledge=0.3,
            learn_rate=0.25,
            slip_rate=0.1,
            guess_rate=0.2,
            decay_rate=0.05,
            version="baseline",
            created_at=datetime.now()
        )
        
        # Performance history
        self.performance_history: deque = deque(maxlen=10000)
        self.parameter_history: List[ParameterSet] = []
        
        # Active A/B tests
        self.active_ab_tests: Dict[str, ABTestConfig] = {}
        self.ab_test_results: Dict[str, Dict] = {}
        
        # Optimization state
        self.optimization_iteration = 0
        self.last_optimization = datetime.now()
        self.optimization_lock = threading.Lock()
        
        # Performance tracking
        self.metrics_buffer = defaultdict(list)
        self.sample_counts = defaultdict(int)
        
        # Thread pool for concurrent optimization
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        self.logger.info(f"Initialized RealTimeOptimizer with strategy: {optimization_strategy.value}")
    
    def suggest_parameters(self, context: Dict[str, Any] = None) -> ParameterSet:
        """
        Suggest optimal parameters based on current context
        Thread-safe and optimized for high-frequency calls
        """
        with self.optimization_lock:
            # Check if we have active A/B tests
            active_test = self._get_active_ab_test(context)
            if active_test:
                variant = self._select_ab_variant(active_test, context)
                return variant
            
            # Return current best if no A/B test active
            return self.current_best.copy() if hasattr(self.current_best, 'copy') else ParameterSet(
                prior_knowledge=self.current_best.prior_knowledge,
                learn_rate=self.current_best.learn_rate,
                slip_rate=self.current_best.slip_rate,
                guess_rate=self.current_best.guess_rate,
                decay_rate=self.current_best.decay_rate,
                version=self.current_best.version,
                created_at=self.current_best.created_at,
                performance_score=self.current_best.performance_score
            )
    
    def update_performance(self, parameter_version: str, metrics: OptimizationMetrics, context: Dict[str, Any] = None):
        """
        Update performance metrics for given parameter set
        Batched and async for high-throughput scenarios
        """
        timestamp = datetime.now()
        
        # Buffer metrics for batch processing
        self.metrics_buffer[parameter_version].append({
            'metrics': metrics,
            'context': context or {},
            'timestamp': timestamp
        })
        
        self.sample_counts[parameter_version] += 1
        
        # Process batch if buffer is full
        if len(self.metrics_buffer[parameter_version]) >= 100:
            self.executor.submit(self._process_metrics_batch, parameter_version)
    
    def _process_metrics_batch(self, parameter_version: str):
        """Process batched metrics asynchronously"""
        try:
            with self.optimization_lock:
                batch = self.metrics_buffer[parameter_version].copy()
                self.metrics_buffer[parameter_version].clear()
            
            if not batch:
                return
            
            # Aggregate metrics
            aggregated = self._aggregate_metrics(batch)
            
            # Update parameter performance
            self._update_parameter_performance(parameter_version, aggregated)
            
            # Update A/B test results if applicable
            self._update_ab_test_results(parameter_version, aggregated)
            
            # Trigger optimization if conditions met
            if self._should_trigger_optimization():
                self.executor.submit(self._run_optimization)
                
        except Exception as e:
            self.logger.error(f"Error processing metrics batch: {e}")
    
    def _aggregate_metrics(self, batch: List[Dict]) -> OptimizationMetrics:
        """Aggregate batch of metrics"""
        if not batch:
            return OptimizationMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        
        accuracies = [b['metrics'].accuracy for b in batch]
        convergence_rates = [b['metrics'].convergence_rate for b in batch]
        prediction_variances = [b['metrics'].prediction_variance for b in batch]
        calibration_errors = [b['metrics'].calibration_error for b in batch]
        satisfaction_scores = [b['metrics'].student_satisfaction for b in batch]
        learning_velocities = [b['metrics'].learning_velocity for b in batch]
        retention_rates = [b['metrics'].retention_rate for b in batch]
        engagement_scores = [b['metrics'].engagement_score for b in batch]
        
        return OptimizationMetrics(
            accuracy=np.mean(accuracies),
            convergence_rate=np.mean(convergence_rates),
            prediction_variance=np.mean(prediction_variances),
            calibration_error=np.mean(calibration_errors),
            student_satisfaction=np.mean(satisfaction_scores),
            learning_velocity=np.mean(learning_velocities),
            retention_rate=np.mean(retention_rates),
            engagement_score=np.mean(engagement_scores)
        )
    
    def _update_parameter_performance(self, parameter_version: str, metrics: OptimizationMetrics):
        """Update performance for parameter set"""
        # Calculate composite performance score
        performance_score = self._calculate_performance_score(metrics)
        
        # Update parameter history
        for param_set in self.parameter_history:
            if param_set.version == parameter_version:
                param_set.performance_score = performance_score
                param_set.total_samples = self.sample_counts[parameter_version]
                break
        
        # Update current best if better
        if (parameter_version == self.current_best.version or 
            performance_score > self.current_best.performance_score):
            self.current_best.performance_score = performance_score
            self.current_best.total_samples = self.sample_counts[parameter_version]
        
        # Add to performance history
        self.performance_history.append({
            'version': parameter_version,
            'performance_score': performance_score,
            'metrics': metrics,
            'timestamp': datetime.now()
        })
    
    def _calculate_performance_score(self, metrics: OptimizationMetrics) -> float:
        """Calculate composite performance score"""
        # Weighted combination of metrics
        weights = {
            'accuracy': 0.25,
            'convergence_rate': 0.15,
            'prediction_variance': -0.10,  # Negative because lower is better
            'calibration_error': -0.15,  # Negative because lower is better
            'student_satisfaction': 0.20,
            'learning_velocity': 0.15,
            'retention_rate': 0.10,
            'engagement_score': 0.10
        }
        
        score = (
            weights['accuracy'] * metrics.accuracy +
            weights['convergence_rate'] * metrics.convergence_rate +
            weights['prediction_variance'] * (1.0 - metrics.prediction_variance) +
            weights['calibration_error'] * (1.0 - metrics.calibration_error) +
            weights['student_satisfaction'] * metrics.student_satisfaction +
            weights['learning_velocity'] * metrics.learning_velocity +
            weights['retention_rate'] * metrics.retention_rate +
            weights['engagement_score'] * metrics.engagement_score
        )
        
        return max(0.0, min(1.0, score))
    
    def _should_trigger_optimization(self) -> bool:
        """Determine if optimization should be triggered"""
        # Check time since last optimization
        time_since_last = datetime.now() - self.last_optimization
        if time_since_last < timedelta(hours=1):
            return False
        
        # Check if we have enough samples
        total_samples = sum(self.sample_counts.values())
        if total_samples < 1000:
            return False
        
        # Check performance variance
        if len(self.performance_history) >= 10:
            recent_scores = [h['performance_score'] for h in list(self.performance_history)[-10:]]
            if np.std(recent_scores) > 0.05:  # High variance indicates opportunity
                return True
        
        return False
    
    def _run_optimization(self):
        """Run parameter optimization"""
        try:
            with self.optimization_lock:
                self.optimization_iteration += 1
                self.last_optimization = datetime.now()
            
            self.logger.info(f"Starting optimization iteration {self.optimization_iteration}")
            
            if self.strategy == OptimizationStrategy.BAYESIAN_OPTIMIZATION:
                new_params = self._bayesian_optimization()
            elif self.strategy == OptimizationStrategy.GENETIC_ALGORITHM:
                new_params = self._genetic_algorithm()
            elif self.strategy == OptimizationStrategy.GRADIENT_DESCENT:
                new_params = self._gradient_descent()
            elif self.strategy == OptimizationStrategy.MULTI_ARMED_BANDIT:
                new_params = self._multi_armed_bandit()
            elif self.strategy == OptimizationStrategy.SIMULATED_ANNEALING:
                new_params = self._simulated_annealing()
            elif self.strategy == OptimizationStrategy.PARTICLE_SWARM:
                new_params = self._particle_swarm_optimization()
            else:
                self.logger.warning(f"Unknown optimization strategy: {self.strategy}")
                return
            
            if new_params:
                # Create A/B test for new parameters
                self._create_ab_test_for_optimization(new_params)
                self.logger.info(f"Created A/B test for optimized parameters: {new_params.version}")
            
        except Exception as e:
            self.logger.error(f"Error during optimization: {e}")
    
    def _bayesian_optimization(self) -> Optional[ParameterSet]:
        """Bayesian optimization implementation"""
        try:
            from sklearn.gaussian_process import GaussianProcessRegressor
            from sklearn.gaussian_process.kernels import Matern
            from scipy.optimize import minimize
            
            # Collect training data from history
            if len(self.parameter_history) < 5:
                return None
            
            X = []
            y = []
            
            for param_set in self.parameter_history[-50:]:  # Use recent history
                if param_set.total_samples >= 10:  # Minimum samples for reliability
                    X.append([
                        param_set.prior_knowledge,
                        param_set.learn_rate,
                        param_set.slip_rate,
                        param_set.guess_rate,
                        param_set.decay_rate
                    ])
                    y.append(param_set.performance_score)
            
            if len(X) < 5:
                return None
            
            # Fit Gaussian Process
            kernel = Matern(length_scale=0.1, nu=2.5)
            gp = GaussianProcessRegressor(kernel=kernel, alpha=1e-6, normalize_y=True)
            gp.fit(X, y)
            
            # Acquisition function (Expected Improvement)
            def expected_improvement(x):
                x = x.reshape(1, -1)
                mu, sigma = gp.predict(x, return_std=True)
                
                # Current best
                f_best = max(y)
                
                with np.errstate(divide='warn'):
                    improvement = mu - f_best
                    Z = improvement / sigma
                    ei = improvement * norm.cdf(Z) + sigma * norm.pdf(Z)
                    ei[sigma == 0.0] = 0.0
                
                return -ei[0]  # Negative for minimization
            
            # Optimize acquisition function
            bounds = [
                self.parameter_bounds['prior_knowledge'],
                self.parameter_bounds['learn_rate'],
                self.parameter_bounds['slip_rate'], 
                self.parameter_bounds['guess_rate'],
                self.parameter_bounds['decay_rate']
            ]
            
            best_x = None
            best_ei = float('inf')
            
            # Multiple random starts
            for _ in range(10):
                x0 = np.random.uniform([b[0] for b in bounds], [b[1] for b in bounds])
                
                result = minimize(
                    expected_improvement,
                    x0,
                    bounds=bounds,
                    method='L-BFGS-B'
                )
                
                if result.success and result.fun < best_ei:
                    best_ei = result.fun
                    best_x = result.x
            
            if best_x is not None:
                return ParameterSet(
                    prior_knowledge=float(best_x[0]),
                    learn_rate=float(best_x[1]),
                    slip_rate=float(best_x[2]),
                    guess_rate=float(best_x[3]),
                    decay_rate=float(best_x[4]),
                    version=f"bayesian_opt_{self.optimization_iteration}",
                    created_at=datetime.now()
                )
            
        except ImportError:
            self.logger.warning("Scikit-learn not available for Bayesian optimization")
        except Exception as e:
            self.logger.error(f"Bayesian optimization failed: {e}")
        
        return None
    
    def _genetic_algorithm(self) -> Optional[ParameterSet]:
        """Genetic algorithm implementation"""
        try:
            # Simple GA implementation
            population_size = 20
            generations = 10
            mutation_rate = 0.1
            crossover_rate = 0.8
            
            # Initialize population
            population = []
            for _ in range(population_size):
                individual = {
                    'prior_knowledge': np.random.uniform(*self.parameter_bounds['prior_knowledge']),
                    'learn_rate': np.random.uniform(*self.parameter_bounds['learn_rate']),
                    'slip_rate': np.random.uniform(*self.parameter_bounds['slip_rate']),
                    'guess_rate': np.random.uniform(*self.parameter_bounds['guess_rate']),
                    'decay_rate': np.random.uniform(*self.parameter_bounds['decay_rate']),
                    'fitness': 0.0
                }
                population.append(individual)
            
            # Evolution loop
            for generation in range(generations):
                # Evaluate fitness (simplified - would need actual evaluation)
                for individual in population:
                    # Simplified fitness based on similarity to best known parameters
                    fitness = self._estimate_parameter_fitness(individual)
                    individual['fitness'] = fitness
                
                # Selection
                population.sort(key=lambda x: x['fitness'], reverse=True)
                survivors = population[:population_size//2]
                
                # Crossover and mutation
                new_population = survivors.copy()
                
                while len(new_population) < population_size:
                    if np.random.random() < crossover_rate:
                        parent1, parent2 = np.random.choice(survivors, 2, replace=False)
                        child = self._crossover(parent1, parent2)
                    else:
                        child = np.random.choice(survivors).copy()
                    
                    if np.random.random() < mutation_rate:
                        child = self._mutate(child)
                    
                    new_population.append(child)
                
                population = new_population
            
            # Return best individual
            best = max(population, key=lambda x: x['fitness'])
            
            return ParameterSet(
                prior_knowledge=best['prior_knowledge'],
                learn_rate=best['learn_rate'],
                slip_rate=best['slip_rate'],
                guess_rate=best['guess_rate'],
                decay_rate=best['decay_rate'],
                version=f"genetic_{self.optimization_iteration}",
                created_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Genetic algorithm failed: {e}")
            return None
    
    def _estimate_parameter_fitness(self, individual: Dict) -> float:
        """Estimate fitness of parameter set (simplified)"""
        # This is a simplified fitness estimation
        # In practice, would use surrogate models or historical data
        
        # Penalize extreme values
        penalties = 0
        for param, value in individual.items():
            if param in self.parameter_bounds:
                bounds = self.parameter_bounds[param]
                if value < bounds[0] or value > bounds[1]:
                    penalties += 1
        
        # Reward parameters similar to historically good ones
        similarity_score = 0
        if self.parameter_history:
            best_historical = max(self.parameter_history, key=lambda x: x.performance_score)
            
            param_diffs = [
                abs(individual['prior_knowledge'] - best_historical.prior_knowledge),
                abs(individual['learn_rate'] - best_historical.learn_rate),
                abs(individual['slip_rate'] - best_historical.slip_rate),
                abs(individual['guess_rate'] - best_historical.guess_rate),
                abs(individual['decay_rate'] - best_historical.decay_rate)
            ]
            
            similarity_score = 1.0 - np.mean(param_diffs)
        
        fitness = similarity_score - 0.1 * penalties
        return max(0.0, fitness)
    
    def _crossover(self, parent1: Dict, parent2: Dict) -> Dict:
        """Crossover operation for genetic algorithm"""
        child = {}
        for key in parent1:
            if key != 'fitness':
                # Blend crossover
                alpha = 0.5
                child[key] = alpha * parent1[key] + (1 - alpha) * parent2[key]
        child['fitness'] = 0.0
        return child
    
    def _mutate(self, individual: Dict) -> Dict:
        """Mutation operation for genetic algorithm"""
        mutated = individual.copy()
        
        for param in ['prior_knowledge', 'learn_rate', 'slip_rate', 'guess_rate', 'decay_rate']:
            if np.random.random() < 0.2:  # 20% chance to mutate each parameter
                bounds = self.parameter_bounds[param]
                # Gaussian mutation
                mutation = np.random.normal(0, 0.05)
                mutated[param] = np.clip(mutated[param] + mutation, bounds[0], bounds[1])
        
        return mutated
    
    def _gradient_descent(self) -> Optional[ParameterSet]:
        """Gradient descent optimization (simplified)"""
        # This would require differentiable objective function
        # Placeholder implementation
        return None
    
    def _multi_armed_bandit(self) -> Optional[ParameterSet]:
        """Multi-armed bandit approach"""
        # Upper Confidence Bound (UCB) strategy
        if len(self.parameter_history) < 3:
            return None
        
        # Select parameter set with highest UCB score
        best_ucb_score = -1
        best_params = None
        
        total_samples = sum(p.total_samples for p in self.parameter_history)
        
        for param_set in self.parameter_history:
            if param_set.total_samples > 0:
                # UCB score
                exploitation = param_set.performance_score
                exploration = np.sqrt(2 * np.log(total_samples) / param_set.total_samples)
                ucb_score = exploitation + exploration
                
                if ucb_score > best_ucb_score:
                    best_ucb_score = ucb_score
                    best_params = param_set
        
        if best_params:
            # Create slight variation
            return ParameterSet(
                prior_knowledge=np.clip(best_params.prior_knowledge + np.random.normal(0, 0.02), 
                                      *self.parameter_bounds['prior_knowledge']),
                learn_rate=np.clip(best_params.learn_rate + np.random.normal(0, 0.02),
                                 *self.parameter_bounds['learn_rate']),
                slip_rate=np.clip(best_params.slip_rate + np.random.normal(0, 0.01),
                                *self.parameter_bounds['slip_rate']),
                guess_rate=np.clip(best_params.guess_rate + np.random.normal(0, 0.01),
                                 *self.parameter_bounds['guess_rate']),
                decay_rate=np.clip(best_params.decay_rate + np.random.normal(0, 0.01),
                                 *self.parameter_bounds['decay_rate']),
                version=f"bandit_{self.optimization_iteration}",
                created_at=datetime.now()
            )
        
        return None
    
    def _simulated_annealing(self) -> Optional[ParameterSet]:
        """Simulated annealing optimization"""
        if not self.parameter_history:
            return None
        
        # Start from current best
        current = self.current_best
        best = current
        
        # Annealing parameters
        initial_temp = 1.0
        cooling_rate = 0.95
        min_temp = 0.01
        
        temperature = initial_temp
        
        for iteration in range(100):
            if temperature < min_temp:
                break
            
            # Generate neighbor solution
            neighbor_params = {
                'prior_knowledge': np.clip(current.prior_knowledge + np.random.normal(0, 0.05 * temperature), 
                                         *self.parameter_bounds['prior_knowledge']),
                'learn_rate': np.clip(current.learn_rate + np.random.normal(0, 0.05 * temperature),
                                    *self.parameter_bounds['learn_rate']),
                'slip_rate': np.clip(current.slip_rate + np.random.normal(0, 0.02 * temperature),
                                   *self.parameter_bounds['slip_rate']),
                'guess_rate': np.clip(current.guess_rate + np.random.normal(0, 0.02 * temperature),
                                    *self.parameter_bounds['guess_rate']),
                'decay_rate': np.clip(current.decay_rate + np.random.normal(0, 0.01 * temperature),
                                    *self.parameter_bounds['decay_rate'])
            }
            
            # Estimate fitness
            current_fitness = self._estimate_parameter_fitness({
                'prior_knowledge': current.prior_knowledge,
                'learn_rate': current.learn_rate,
                'slip_rate': current.slip_rate,
                'guess_rate': current.guess_rate,
                'decay_rate': current.decay_rate
            })
            
            neighbor_fitness = self._estimate_parameter_fitness(neighbor_params)
            
            # Accept or reject
            delta = neighbor_fitness - current_fitness
            
            if delta > 0 or np.random.random() < np.exp(delta / temperature):
                current = ParameterSet(
                    prior_knowledge=neighbor_params['prior_knowledge'],
                    learn_rate=neighbor_params['learn_rate'],
                    slip_rate=neighbor_params['slip_rate'],
                    guess_rate=neighbor_params['guess_rate'],
                    decay_rate=neighbor_params['decay_rate'],
                    version=f"annealing_{self.optimization_iteration}_{iteration}",
                    created_at=datetime.now(),
                    performance_score=neighbor_fitness
                )
                
                if neighbor_fitness > best.performance_score:
                    best = current
            
            temperature *= cooling_rate
        
        if best.performance_score > self.current_best.performance_score:
            return best
        
        return None
    
    def _particle_swarm_optimization(self) -> Optional[ParameterSet]:
        """Particle Swarm Optimization"""
        # Simplified PSO implementation
        n_particles = 10
        n_iterations = 20
        w = 0.7  # Inertia weight
        c1 = 1.5  # Cognitive parameter
        c2 = 1.5  # Social parameter
        
        # Initialize particles
        particles = []
        for i in range(n_particles):
            position = np.array([
                np.random.uniform(*self.parameter_bounds['prior_knowledge']),
                np.random.uniform(*self.parameter_bounds['learn_rate']),
                np.random.uniform(*self.parameter_bounds['slip_rate']),
                np.random.uniform(*self.parameter_bounds['guess_rate']),
                np.random.uniform(*self.parameter_bounds['decay_rate'])
            ])
            
            velocity = np.random.uniform(-0.1, 0.1, 5)
            
            particles.append({
                'position': position,
                'velocity': velocity,
                'best_position': position.copy(),
                'best_fitness': 0.0
            })
        
        # Global best
        global_best_position = particles[0]['position'].copy()
        global_best_fitness = 0.0
        
        bounds_min = np.array([self.parameter_bounds[p][0] for p in 
                              ['prior_knowledge', 'learn_rate', 'slip_rate', 'guess_rate', 'decay_rate']])
        bounds_max = np.array([self.parameter_bounds[p][1] for p in 
                              ['prior_knowledge', 'learn_rate', 'slip_rate', 'guess_rate', 'decay_rate']])
        
        # PSO iterations
        for iteration in range(n_iterations):
            for particle in particles:
                # Evaluate fitness
                fitness = self._estimate_parameter_fitness({
                    'prior_knowledge': particle['position'][0],
                    'learn_rate': particle['position'][1],
                    'slip_rate': particle['position'][2],
                    'guess_rate': particle['position'][3],
                    'decay_rate': particle['position'][4]
                })
                
                # Update personal best
                if fitness > particle['best_fitness']:
                    particle['best_fitness'] = fitness
                    particle['best_position'] = particle['position'].copy()
                
                # Update global best
                if fitness > global_best_fitness:
                    global_best_fitness = fitness
                    global_best_position = particle['position'].copy()
            
            # Update velocities and positions
            for particle in particles:
                r1, r2 = np.random.random(5), np.random.random(5)
                
                cognitive = c1 * r1 * (particle['best_position'] - particle['position'])
                social = c2 * r2 * (global_best_position - particle['position'])
                
                particle['velocity'] = w * particle['velocity'] + cognitive + social
                particle['position'] = particle['position'] + particle['velocity']
                
                # Enforce bounds
                particle['position'] = np.clip(particle['position'], bounds_min, bounds_max)
        
        if global_best_fitness > 0:
            return ParameterSet(
                prior_knowledge=global_best_position[0],
                learn_rate=global_best_position[1],
                slip_rate=global_best_position[2],
                guess_rate=global_best_position[3],
                decay_rate=global_best_position[4],
                version=f"pso_{self.optimization_iteration}",
                created_at=datetime.now(),
                performance_score=global_best_fitness
            )
        
        return None
    
    def create_ab_test(self, test_config: ABTestConfig) -> str:
        """Create a new A/B test"""
        test_id = test_config.test_id
        self.active_ab_tests[test_id] = test_config
        self.ab_test_results[test_id] = {
            'variants': {variant.version: {'samples': 0, 'metrics': []} 
                        for variant in test_config.parameter_variants},
            'start_time': test_config.start_time,
            'status': 'active'
        }
        
        self.logger.info(f"Created A/B test: {test_config.name} (ID: {test_id})")
        return test_id
    
    def _create_ab_test_for_optimization(self, new_params: ParameterSet):
        """Create A/B test comparing current best with optimized parameters"""
        test_config = ABTestConfig(
            test_id=f"optimization_{self.optimization_iteration}_{uuid.uuid4().hex[:8]}",
            name=f"Optimization Test {self.optimization_iteration}",
            parameter_variants=[self.current_best, new_params],
            traffic_allocation=[0.8, 0.2],  # 80% control, 20% test
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(days=3),
            minimum_sample_size=1000,
            primary_metric="accuracy"
        )
        
        self.create_ab_test(test_config)
    
    def _get_active_ab_test(self, context: Dict[str, Any]) -> Optional[ABTestConfig]:
        """Get active A/B test for current context"""
        for test_id, config in self.active_ab_tests.items():
            if config.end_time is None or datetime.now() < config.end_time:
                return config
        return None
    
    def _select_ab_variant(self, test_config: ABTestConfig, context: Dict[str, Any]) -> ParameterSet:
        """Select variant for A/B test"""
        # Simple random allocation based on traffic percentages
        rand = np.random.random()
        cumulative = 0.0
        
        for i, allocation in enumerate(test_config.traffic_allocation):
            cumulative += allocation
            if rand <= cumulative:
                return test_config.parameter_variants[i]
        
        # Fallback to first variant
        return test_config.parameter_variants[0]
    
    def _update_ab_test_results(self, parameter_version: str, metrics: OptimizationMetrics):
        """Update A/B test results"""
        for test_id, config in self.active_ab_tests.items():
            for variant in config.parameter_variants:
                if variant.version == parameter_version:
                    results = self.ab_test_results[test_id]
                    variant_results = results['variants'][parameter_version]
                    variant_results['samples'] += 1
                    variant_results['metrics'].append(metrics)
                    
                    # Check if test should conclude
                    if variant_results['samples'] >= config.minimum_sample_size:
                        self._evaluate_ab_test(test_id)
                    break
    
    def _evaluate_ab_test(self, test_id: str):
        """Evaluate A/B test results and make decisions"""
        try:
            from scipy import stats
            
            config = self.active_ab_tests[test_id]
            results = self.ab_test_results[test_id]
            
            # Get metrics for each variant
            variant_metrics = {}
            for variant_version, variant_data in results['variants'].items():
                if variant_data['samples'] >= config.minimum_sample_size:
                    metrics_values = [getattr(m, config.primary_metric) for m in variant_data['metrics']]
                    variant_metrics[variant_version] = metrics_values
            
            if len(variant_metrics) < 2:
                return  # Need at least 2 variants with sufficient data
            
            # Perform statistical test
            variants = list(variant_metrics.keys())
            control_metrics = variant_metrics[variants[0]]
            test_metrics = variant_metrics[variants[1]]
            
            # Two-sample t-test
            t_stat, p_value = stats.ttest_ind(test_metrics, control_metrics)
            
            # Check significance
            is_significant = p_value < config.significance_level
            test_is_better = np.mean(test_metrics) > np.mean(control_metrics)
            
            # Update results
            results['conclusion'] = {
                'is_significant': is_significant,
                'p_value': p_value,
                't_statistic': t_stat,
                'test_is_better': test_is_better,
                'control_mean': np.mean(control_metrics),
                'test_mean': np.mean(test_metrics),
                'concluded_at': datetime.now()
            }
            
            # Update current best if test variant is significantly better
            if is_significant and test_is_better:
                test_variant = None
                for variant in config.parameter_variants:
                    if variant.version == variants[1]:
                        test_variant = variant
                        break
                
                if test_variant:
                    self.current_best = test_variant
                    self.parameter_history.append(test_variant)
                    self.logger.info(f"A/B test {test_id} concluded: Test variant is significantly better. Updated current best.")
            
            # Mark test as completed
            results['status'] = 'completed'
            
        except ImportError:
            self.logger.warning("SciPy not available for statistical testing")
        except Exception as e:
            self.logger.error(f"Error evaluating A/B test {test_id}: {e}")
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        return {
            'current_best_parameters': {
                'version': self.current_best.version,
                'prior_knowledge': self.current_best.prior_knowledge,
                'learn_rate': self.current_best.learn_rate,
                'slip_rate': self.current_best.slip_rate,
                'guess_rate': self.current_best.guess_rate,
                'decay_rate': self.current_best.decay_rate,
                'performance_score': self.current_best.performance_score,
                'total_samples': self.current_best.total_samples,
                'created_at': self.current_best.created_at.isoformat()
            },
            'optimization_stats': {
                'total_iterations': self.optimization_iteration,
                'last_optimization': self.last_optimization.isoformat(),
                'total_parameter_sets_tested': len(self.parameter_history),
                'total_performance_samples': len(self.performance_history)
            },
            'active_ab_tests': {
                test_id: {
                    'name': config.name,
                    'start_time': config.start_time.isoformat(),
                    'end_time': config.end_time.isoformat() if config.end_time else None,
                    'variants_count': len(config.parameter_variants),
                    'traffic_allocation': config.traffic_allocation
                }
                for test_id, config in self.active_ab_tests.items()
            },
            'recent_performance_trend': [
                {
                    'version': entry['version'],
                    'performance_score': entry['performance_score'],
                    'timestamp': entry['timestamp'].isoformat()
                }
                for entry in list(self.performance_history)[-10:]
            ],
            'parameter_bounds': self.parameter_bounds,
            'optimization_strategy': self.strategy.value
        }
    
    def cleanup_completed_tests(self, days_old: int = 7):
        """Clean up completed A/B tests older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        completed_tests = []
        for test_id, results in self.ab_test_results.items():
            if (results.get('status') == 'completed' and 
                'concluded_at' in results.get('conclusion', {}) and
                results['conclusion']['concluded_at'] < cutoff_date):
                completed_tests.append(test_id)
        
        for test_id in completed_tests:
            del self.ab_test_results[test_id]
            if test_id in self.active_ab_tests:
                del self.active_ab_tests[test_id]
        
        if completed_tests:
            self.logger.info(f"Cleaned up {len(completed_tests)} completed A/B tests")

# Import necessary libraries with fallbacks
try:
    from scipy.stats import norm
except ImportError:
    norm = None