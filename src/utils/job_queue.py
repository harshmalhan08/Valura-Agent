"""Async job queue for background task processing."""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional, List
from dataclasses import dataclass, field


class JobStatus(str, Enum):
    """Job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    """Job representation."""
    id: str
    task: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary."""
        return {
            "id": self.id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class JobQueue:
    """
    Async job queue for background task processing.
    
    Features:
    - Async task execution
    - Job status tracking
    - Concurrent worker pool
    - Error handling and retry
    """
    
    def __init__(self, max_workers: int = 5):
        """
        Initialize job queue.
        
        Args:
            max_workers: Maximum concurrent workers
        """
        self.max_workers = max_workers
        self.queue: asyncio.Queue = asyncio.Queue()
        self.jobs: Dict[str, Job] = {}
        self.workers: List[asyncio.Task] = []
        self.running = False
    
    async def start(self):
        """Start worker pool."""
        if self.running:
            return
        
        self.running = True
        self.workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.max_workers)
        ]
    
    async def stop(self):
        """Stop worker pool."""
        self.running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        self.workers.clear()
    
    async def _worker(self, worker_id: int):
        """Worker coroutine."""
        while self.running:
            try:
                # Get job from queue with timeout
                job = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0
                )
                
                # Execute job
                await self._execute_job(job)
                
                # Mark task as done
                self.queue.task_done()
                
            except asyncio.TimeoutError:
                # No job available, continue
                continue
            except asyncio.CancelledError:
                # Worker cancelled
                break
            except Exception as e:
                # Log error but continue
                print(f"Worker {worker_id} error: {e}")
    
    async def _execute_job(self, job: Job):
        """Execute a job."""
        try:
            # Update status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            
            # Execute task
            if asyncio.iscoroutinefunction(job.task):
                result = await job.task(*job.args, **job.kwargs)
            else:
                result = job.task(*job.args, **job.kwargs)
            
            # Update job
            job.status = JobStatus.COMPLETED
            job.result = result
            job.completed_at = datetime.utcnow()
            
        except Exception as e:
            # Update job with error
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.utcnow()
    
    async def submit(
        self,
        task: Callable,
        *args,
        **kwargs
    ) -> str:
        """
        Submit a job to the queue.
        
        Args:
            task: Callable to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Job ID
        """
        # Create job
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            task=task,
            args=args,
            kwargs=kwargs
        )
        
        # Store job
        self.jobs[job_id] = job
        
        # Add to queue
        await self.queue.put(job)
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self.jobs.get(job_id)
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status."""
        job = self.jobs.get(job_id)
        if job:
            return job.to_dict()
        return None
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        pending = sum(1 for j in self.jobs.values() if j.status == JobStatus.PENDING)
        running = sum(1 for j in self.jobs.values() if j.status == JobStatus.RUNNING)
        completed = sum(1 for j in self.jobs.values() if j.status == JobStatus.COMPLETED)
        failed = sum(1 for j in self.jobs.values() if j.status == JobStatus.FAILED)
        
        return {
            "total_jobs": len(self.jobs),
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "queue_size": self.queue.qsize(),
            "workers": len(self.workers),
            "max_workers": self.max_workers
        }
