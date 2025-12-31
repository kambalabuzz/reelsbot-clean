# scheduler.py
"""
Video generation and posting scheduler.
Handles automatic episode generation and posting based on series schedules.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

from config import SeriesConfig, PostFrequency, VideoDuration


@dataclass
class ScheduledJob:
    """A scheduled video generation/posting job."""
    id: str
    series_id: str
    topic: str
    scheduled_time: datetime
    status: str = "pending"  # pending, generating, completed, failed, posted
    video_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class Scheduler:
    """
    Simple file-based scheduler.
    In production, use Celery Beat or APScheduler with Redis.
    """
    
    def __init__(self, schedule_dir: str = "schedules"):
        self.schedule_dir = Path(schedule_dir)
        self.schedule_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_job_path(self, job_id: str) -> Path:
        return self.schedule_dir / f"{job_id}.json"
    
    def _save_job(self, job: ScheduledJob):
        path = self._get_job_path(job.id)
        data = asdict(job)
        data["scheduled_time"] = job.scheduled_time.isoformat()
        data["created_at"] = job.created_at.isoformat()
        path.write_text(json.dumps(data, indent=2))
    
    def _load_job(self, job_id: str) -> Optional[ScheduledJob]:
        path = self._get_job_path(job_id)
        if not path.exists():
            return None
        
        data = json.loads(path.read_text())
        data["scheduled_time"] = datetime.fromisoformat(data["scheduled_time"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return ScheduledJob(**data)
    
    def schedule_job(
        self,
        series_id: str,
        topic: str,
        scheduled_time: datetime,
    ) -> ScheduledJob:
        """Schedule a new video generation job."""
        job_id = f"{series_id}_{scheduled_time.strftime('%Y%m%d_%H%M%S')}"
        
        job = ScheduledJob(
            id=job_id,
            series_id=series_id,
            topic=topic,
            scheduled_time=scheduled_time,
        )
        
        self._save_job(job)
        print(f"[scheduler] Scheduled job {job_id} for {scheduled_time}")
        return job
    
    def get_pending_jobs(self) -> List[ScheduledJob]:
        """Get all pending jobs that are due."""
        now = datetime.utcnow()
        pending = []
        
        for path in self.schedule_dir.glob("*.json"):
            job = self._load_job(path.stem)
            if job and job.status == "pending" and job.scheduled_time <= now:
                pending.append(job)
        
        return sorted(pending, key=lambda j: j.scheduled_time)
    
    def get_upcoming_jobs(self, hours: int = 24) -> List[ScheduledJob]:
        """Get jobs scheduled in the next N hours."""
        now = datetime.utcnow()
        cutoff = now + timedelta(hours=hours)
        upcoming = []
        
        for path in self.schedule_dir.glob("*.json"):
            job = self._load_job(path.stem)
            if job and job.status == "pending" and now < job.scheduled_time <= cutoff:
                upcoming.append(job)
        
        return sorted(upcoming, key=lambda j: j.scheduled_time)
    
    def update_job_status(
        self,
        job_id: str,
        status: str,
        video_path: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        """Update job status."""
        job = self._load_job(job_id)
        if job:
            job.status = status
            job.video_path = video_path
            job.error_message = error_message
            self._save_job(job)
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job."""
        path = self._get_job_path(job_id)
        if path.exists():
            job = self._load_job(job_id)
            if job and job.status == "pending":
                job.status = "cancelled"
                self._save_job(job)
                return True
        return False
    
    def generate_schedule(
        self,
        series_id: str,
        config: SeriesConfig,
        topics: List[str],
        start_date: Optional[datetime] = None,
    ) -> List[ScheduledJob]:
        """
        Generate scheduled jobs based on series config.
        
        Args:
            series_id: Series identifier
            config: Series configuration
            topics: List of topics to schedule
            start_date: When to start scheduling (default: now)
        
        Returns:
            List of scheduled jobs
        """
        if start_date is None:
            start_date = datetime.utcnow()
        
        jobs = []
        current_date = start_date
        
        # Parse post time
        hour, minute = map(int, config.post_time.split(":"))
        
        for topic in topics:
            # Set time for current day
            scheduled_time = current_date.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0,
            )
            
            # If time has passed today, start tomorrow
            if scheduled_time <= datetime.utcnow():
                scheduled_time += timedelta(days=1)
            
            job = self.schedule_job(series_id, topic, scheduled_time)
            jobs.append(job)
            
            # Advance to next slot based on frequency
            if config.post_frequency == PostFrequency.DAILY:
                current_date += timedelta(days=1)
            elif config.post_frequency == PostFrequency.TWICE_DAILY:
                current_date += timedelta(hours=12)
            elif config.post_frequency == PostFrequency.THREE_PER_WEEK:
                # Mon, Wed, Fri schedule
                days_until_next = {0: 2, 2: 2, 4: 3, 1: 1, 3: 1, 5: 2, 6: 1}
                current_date += timedelta(days=days_until_next.get(current_date.weekday(), 1))
            elif config.post_frequency == PostFrequency.WEEKLY:
                current_date += timedelta(weeks=1)
            else:
                # Manual - schedule all for same time (user triggers manually)
                pass
        
        return jobs


def run_scheduler_tick():
    """
    Run one tick of the scheduler.
    Call this from a cron job or background worker.
    
    In production, use:
    - Celery Beat for periodic tasks
    - Redis for job queue
    - Worker processes for generation
    """
    from engine import generate_episode
    from social import post_to_all, SocialAccount, Platform
    
    scheduler = Scheduler()
    pending = scheduler.get_pending_jobs()
    
    print(f"[scheduler] Found {len(pending)} pending jobs")
    
    for job in pending:
        print(f"[scheduler] Processing job {job.id}: {job.topic}")
        
        try:
            # Mark as generating
            scheduler.update_job_status(job.id, "generating")
            
            # Generate video
            # Note: In production, load series config from database
            result = generate_episode(topic=job.topic)
            
            video_path = result["final_video"]
            
            # Mark as completed
            scheduler.update_job_status(job.id, "completed", video_path=video_path)
            print(f"[scheduler] Job {job.id} completed: {video_path}")
            
            # TODO: Post to social media
            # accounts = get_accounts_for_series(job.series_id)
            # post_to_all(video_path, job.topic, "", accounts)
            
        except Exception as e:
            scheduler.update_job_status(job.id, "failed", error_message=str(e))
            print(f"[scheduler] Job {job.id} failed: {e}")


# =============================================================================
# CLI
# =============================================================================
if __name__ == "__main__":
    import sys
    
    scheduler = Scheduler()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scheduler.py run          - Process pending jobs")
        print("  python scheduler.py pending      - Show pending jobs")
        print("  python scheduler.py upcoming     - Show upcoming jobs (24h)")
        print("  python scheduler.py schedule <series_id> <topic> <time>")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "run":
        run_scheduler_tick()
    
    elif cmd == "pending":
        jobs = scheduler.get_pending_jobs()
        print(f"\nPending jobs: {len(jobs)}")
        for job in jobs:
            print(f"  [{job.id}] {job.topic} @ {job.scheduled_time}")
    
    elif cmd == "upcoming":
        jobs = scheduler.get_upcoming_jobs(24)
        print(f"\nUpcoming jobs (24h): {len(jobs)}")
        for job in jobs:
            print(f"  [{job.id}] {job.topic} @ {job.scheduled_time}")
    
    elif cmd == "schedule" and len(sys.argv) >= 5:
        series_id = sys.argv[2]
        topic = sys.argv[3]
        time_str = sys.argv[4]
        
        scheduled_time = datetime.fromisoformat(time_str)
        job = scheduler.schedule_job(series_id, topic, scheduled_time)
        print(f"Scheduled: {job.id}")
    
    else:
        print(f"Unknown command: {cmd}")
