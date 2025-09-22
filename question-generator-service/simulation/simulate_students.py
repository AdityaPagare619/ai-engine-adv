#!/usr/bin/env python3
"""
simulate_students.py
Large-Scale Student Simulation Framework - Python Implementation
Phase 2.2 Load Testing with asyncio and configurable concurrency
"""

import asyncio
import aiohttp
import argparse
import csv
import json
import logging
import random
import time
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SimulationConfig:
    """Configuration for simulation parameters."""
    api_base_url: str = "http://localhost:8080"
    student_count: int = 1000
    concurrent_users: int = 50
    test_duration: int = 300  # seconds
    requests_per_user: int = 20
    output_file: str = "simulation_results_python.csv"
    verbose: bool = False
    request_timeout: int = 30

@dataclass
class VirtualStudent:
    """Represents a virtual student with realistic characteristics."""
    id: str
    exam_type: str
    subject: str
    format: str
    difficulty: float
    performance: float  # Simulated ability level (0.0-1.0)
    learning_rate: float = field(default_factory=lambda: random.uniform(0.1, 0.3))
    stress_tolerance: float = field(default_factory=lambda: random.uniform(0.4, 0.9))

@dataclass
class RequestMetrics:
    """Metrics for a single request."""
    student_id: str
    request_id: str
    success: bool
    response_time: float
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class StudentSummary:
    """Summary metrics for a single student."""
    student_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    questions_answered: int = 0
    correct_answers: int = 0
    errors: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def avg_response_time(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_response_time / self.total_requests
    
    @property
    def accuracy(self) -> float:
        if self.questions_answered == 0:
            return 0.0
        return (self.correct_answers / self.questions_answered) * 100

class MetricsCollector:
    """Collects and analyzes simulation metrics."""
    
    def __init__(self):
        self.start_time = time.time()
        self.end_time = None
        self.request_metrics: List[RequestMetrics] = []
        self.student_summaries: Dict[str, StudentSummary] = {}
        self._lock = asyncio.Lock()
    
    async def record_request(self, metrics: RequestMetrics):
        """Record metrics for a single request."""
        async with self._lock:
            self.request_metrics.append(metrics)
            
            # Update student summary
            if metrics.student_id not in self.student_summaries:
                self.student_summaries[metrics.student_id] = StudentSummary(
                    student_id=metrics.student_id
                )
            
            summary = self.student_summaries[metrics.student_id]
            summary.total_requests += 1
            summary.total_response_time += metrics.response_time
            
            if metrics.success:
                summary.successful_requests += 1
            else:
                summary.failed_requests += 1
                if metrics.error_message:
                    summary.errors.append(metrics.error_message)
            
            # Update response time stats
            if metrics.response_time < summary.min_response_time:
                summary.min_response_time = metrics.response_time
            if metrics.response_time > summary.max_response_time:
                summary.max_response_time = metrics.response_time
    
    async def record_answer(self, student_id: str, correct: bool):
        """Record answer submission."""
        async with self._lock:
            if student_id in self.student_summaries:
                summary = self.student_summaries[student_id]
                summary.questions_answered += 1
                if correct:
                    summary.correct_answers += 1
    
    def get_summary(self) -> Dict:
        """Generate comprehensive simulation summary."""
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        # Calculate aggregate metrics
        total_requests = len(self.request_metrics)
        successful_requests = sum(1 for m in self.request_metrics if m.success)
        failed_requests = total_requests - successful_requests
        
        response_times = [m.response_time for m in self.request_metrics]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p50_response_time = statistics.median(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        else:
            avg_response_time = p50_response_time = p95_response_time = p99_response_time = 0
        
        return {
            'simulation_duration': duration,
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'success_rate': (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            'requests_per_second': total_requests / duration if duration > 0 else 0,
            'avg_response_time_ms': avg_response_time * 1000,
            'p50_response_time_ms': p50_response_time * 1000,
            'p95_response_time_ms': p95_response_time * 1000,
            'p99_response_time_ms': p99_response_time * 1000,
            'concurrent_users': len(self.student_summaries),
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_time': datetime.fromtimestamp(self.end_time).isoformat(),
        }

def generate_virtual_students(count: int) -> List[VirtualStudent]:
    """Generate realistic virtual student profiles."""
    exam_types = ["JEE_MAIN", "JEE_ADVANCED", "NEET", "FOUNDATION"]
    formats = ["MCQ", "NUMERICAL", "ASSERTION_REASON", "PASSAGE"]
    
    students = []
    
    for i in range(count):
        exam_type = random.choice(exam_types)
        
        # Subject selection based on exam type
        if exam_type == "NEET":
            subjects = ["PHYSICS", "CHEMISTRY", "BIOLOGY"]
        elif exam_type in ["JEE_MAIN", "JEE_ADVANCED"]:
            subjects = ["PHYSICS", "CHEMISTRY", "MATHEMATICS"]
        else:
            subjects = ["PHYSICS", "CHEMISTRY", "MATHEMATICS", "BIOLOGY"]
        
        subject = random.choice(subjects)
        format_type = random.choice(formats)
        
        # Realistic distributions
        difficulty = random.uniform(0.2, 0.8)
        performance = random.normalvariate(0.5, 0.15)  # Normal distribution
        performance = max(0.1, min(0.9, performance))  # Clamp to [0.1, 0.9]
        
        student = VirtualStudent(
            id=f"py_student_{i+1:05d}",
            exam_type=exam_type,
            subject=subject,
            format=format_type,
            difficulty=difficulty,
            performance=performance
        )
        
        students.append(student)
    
    return students

def generate_topic_id(subject: str) -> str:
    """Generate realistic topic ID based on subject."""
    topics = {
        "PHYSICS": [
            "PHY_MECHANICS_KINEMATICS", "PHY_MECHANICS_DYNAMICS", "PHY_THERMODYNAMICS",
            "PHY_ELECTROMAGNETISM", "PHY_OPTICS", "PHY_MODERN_PHYSICS", "PHY_WAVES",
        ],
        "CHEMISTRY": [
            "CHEM_PHYSICAL_CHEMISTRY", "CHEM_ORGANIC_CHEMISTRY", "CHEM_INORGANIC_CHEMISTRY",
            "CHEM_CHEMICAL_BONDING", "CHEM_THERMODYNAMICS", "CHEM_ATOMIC_STRUCTURE",
        ],
        "MATHEMATICS": [
            "MATH_ALGEBRA", "MATH_CALCULUS", "MATH_TRIGONOMETRY",
            "MATH_COORDINATE_GEOMETRY", "MATH_PROBABILITY", "MATH_VECTORS",
        ],
        "BIOLOGY": [
            "BIO_CELL_BIOLOGY", "BIO_GENETICS", "BIO_ECOLOGY",
            "BIO_HUMAN_PHYSIOLOGY", "BIO_PLANT_PHYSIOLOGY", "BIO_EVOLUTION",
        ],
    }
    
    return random.choice(topics[subject])

async def make_question_request(
    session: aiohttp.ClientSession, 
    api_url: str, 
    request_data: Dict
) -> Tuple[bool, Optional[str], Dict]:
    """Make HTTP request to question generation API."""
    try:
        async with session.post(
            f"{api_url}/v1/questions/generate",
            json=request_data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Request-ID": request_data["request_id"]
            }
        ) as response:
            if response.status == 200:
                response_data = await response.json()
                return True, None, response_data
            else:
                error_text = await response.text()
                return False, f"HTTP {response.status}: {error_text}", {}
    
    except asyncio.TimeoutError:
        return False, "Request timeout", {}
    except Exception as e:
        return False, f"Request error: {str(e)}", {}

async def simulate_student(
    student: VirtualStudent,
    config: SimulationConfig,
    metrics: MetricsCollector,
    semaphore: asyncio.Semaphore,
    session: aiohttp.ClientSession
):
    """Simulate a single student's behavior."""
    async with semaphore:  # Limit concurrency
        for request_num in range(config.requests_per_user):
            # Generate request
            request_data = {
                "student_id": student.id,
                "topic_id": generate_topic_id(student.subject),
                "exam_type": student.exam_type,
                "subject": student.subject,
                "format": student.format,
                "requested_difficulty": student.difficulty + random.uniform(-0.1, 0.1),
                "session_id": f"session_{student.id}_{request_num}",
                "request_id": f"req_{student.id}_{request_num}_{int(time.time()*1000)}"
            }
            
            # Measure response time
            start_time = time.time()
            success, error_msg, response_data = await make_question_request(
                session, config.api_base_url, request_data
            )
            response_time = time.time() - start_time
            
            # Record metrics
            request_metrics = RequestMetrics(
                student_id=student.id,
                request_id=request_data["request_id"],
                success=success,
                response_time=response_time,
                error_message=error_msg
            )
            
            await metrics.record_request(request_metrics)
            
            if config.verbose:
                status = "SUCCESS" if success else f"FAILED: {error_msg}"
                logger.info(
                    f"Student {student.id}: Request {request_num+1}/{config.requests_per_user} - "
                    f"{status} ({response_time:.3f}s)"
                )
            
            # Simulate answer submission
            if success and random.random() < 0.8:  # 80% answer questions
                correct = random.random() < student.performance
                await metrics.record_answer(student.id, correct)
            
            # Realistic delay between requests
            await asyncio.sleep(random.uniform(1, 5))

async def run_simulation(config: SimulationConfig) -> MetricsCollector:
    """Run the complete simulation."""
    logger.info(f"Starting simulation with {config.student_count} students, "
                f"{config.concurrent_users} concurrent users")
    
    # Generate virtual students
    students = generate_virtual_students(config.student_count)
    
    # Initialize metrics collector
    metrics = MetricsCollector()
    
    # Create semaphore to limit concurrency
    semaphore = asyncio.Semaphore(config.concurrent_users)
    
    # Create HTTP session with timeout
    timeout = aiohttp.ClientTimeout(total=config.request_timeout)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Create tasks for all students
        tasks = [
            simulate_student(student, config, metrics, semaphore, session)
            for student in students
        ]
        
        # Run simulation with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=config.test_duration
            )
        except asyncio.TimeoutError:
            logger.warning("Simulation timed out - collecting partial results")
    
    return metrics

def export_metrics_to_csv(metrics: MetricsCollector, filename: str):
    """Export detailed metrics to CSV file."""
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'student_id', 'total_requests', 'successful_requests', 'failed_requests',
            'success_rate', 'avg_response_time_ms', 'min_response_time_ms', 'max_response_time_ms',
            'questions_answered', 'correct_answers', 'accuracy', 'error_count'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for summary in metrics.student_summaries.values():
            writer.writerow({
                'student_id': summary.student_id,
                'total_requests': summary.total_requests,
                'successful_requests': summary.successful_requests,
                'failed_requests': summary.failed_requests,
                'success_rate': f"{summary.success_rate:.2f}",
                'avg_response_time_ms': f"{summary.avg_response_time * 1000:.2f}",
                'min_response_time_ms': f"{summary.min_response_time * 1000:.2f}",
                'max_response_time_ms': f"{summary.max_response_time * 1000:.2f}",
                'questions_answered': summary.questions_answered,
                'correct_answers': summary.correct_answers,
                'accuracy': f"{summary.accuracy:.2f}",
                'error_count': len(summary.errors)
            })

async def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(description="Student Load Testing Simulation - Python")
    parser.add_argument('--url', default='http://localhost:8080', help='API base URL')
    parser.add_argument('--students', type=int, default=1000, help='Number of virtual students')
    parser.add_argument('--concurrent', type=int, default=50, help='Concurrent users')
    parser.add_argument('--duration', type=int, default=300, help='Test duration in seconds')
    parser.add_argument('--requests', type=int, default=20, help='Requests per user')
    parser.add_argument('--output', default='simulation_results_python.csv', help='Output CSV file')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create configuration
    config = SimulationConfig(
        api_base_url=args.url,
        student_count=args.students,
        concurrent_users=args.concurrent,
        test_duration=args.duration,
        requests_per_user=args.requests,
        output_file=args.output,
        verbose=args.verbose,
        request_timeout=args.timeout
    )
    
    # Run simulation
    try:
        metrics = await run_simulation(config)
        
        # Generate and display summary
        summary = metrics.get_summary()
        logger.info("\n=== SIMULATION SUMMARY ===")
        for key, value in summary.items():
            logger.info(f"{key}: {value}")
        
        # Export detailed metrics
        export_metrics_to_csv(metrics, config.output_file)
        logger.info(f"Detailed metrics exported to: {config.output_file}")
        
        logger.info("Simulation completed successfully!")
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())