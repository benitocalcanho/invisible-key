import unittest
from unittest.mock import patch

from flask import Flask, current_app

from services import calendar_service


class FakeScheduler:
    def __init__(self, timezone=None):
        self.timezone = timezone
        self.jobs = []
        self.running = False

    def add_job(self, func, trigger, args=None, id=None, replace_existing=False):
        self.jobs.append({
            "func": func,
            "trigger": trigger,
            "args": args or [],
            "id": id,
            "replace_existing": replace_existing,
        })

    def start(self):
        self.running = True

    def shutdown(self, wait=False):
        self.running = False

    def get_job(self, job_id):
        class Job:
            next_run_time = None

        return Job() if any(job["id"] == job_id for job in self.jobs) else None


class FakeCronTrigger:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class CalendarSchedulerTest(unittest.TestCase):
    def tearDown(self):
        scheduler = getattr(calendar_service, "_scheduler", None)
        if scheduler and getattr(scheduler, "running", False):
            scheduler.shutdown(wait=False)
        calendar_service._scheduler = None

    def test_start_scheduler_stores_real_app_when_called_with_current_app(self):
        created = []

        def fake_background_scheduler(timezone=None):
            scheduler = FakeScheduler(timezone=timezone)
            created.append(scheduler)
            return scheduler

        app = Flask(__name__)
        app.config["CHECKOUT_TIME"] = "12:00"
        app.config["CHECKIN_TIME"] = "14:00"

        with patch("apscheduler.schedulers.background.BackgroundScheduler", fake_background_scheduler), \
             patch("apscheduler.triggers.cron.CronTrigger", FakeCronTrigger), \
             patch.object(calendar_service, "get_effective_timezone_info", return_value={"name": "UTC", "source": "test"}), \
             patch.object(calendar_service, "get_effective_timezone", return_value="UTC"):
            with app.app_context():
                calendar_service.start_scheduler(current_app)

        self.assertTrue(created)
        scheduler = created[0]
        self.assertTrue(scheduler.running)
        self.assertEqual([job["id"] for job in scheduler.jobs], ["checkout_guests", "checkin_sync"])
        for job in scheduler.jobs:
            self.assertEqual(job["args"], [app])


if __name__ == "__main__":
    unittest.main()
