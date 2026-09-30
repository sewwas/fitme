#  wger Workout Manager is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  wger Workout Manager is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
See https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html
"""

# Standard Library
import os

# Third Party
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.main')
app = Celery('wger')

# read config from Django settings, the CELERY namespace would make celery
# config keys has `CELERY` prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# discover and load tasks.py from all registered Django apps
app.autodiscover_tasks()

# ─────────────────────────────────────────────
# Fit Me — Celery Beat Scheduled Tasks
# ─────────────────────────────────────────────
from celery.schedules import crontab  # noqa: E402

app.conf.beat_schedule = {
    # Sudden staff absence detection: runs every 5 minutes during gym hours
    'inspect-staff-punch-continuity': {
        'task': 'gym_operations_payroll.tasks.inspect_staff_punch_continuity',
        'schedule': 300.0,  # every 5 minutes (300 seconds)
    },

    # Monthly payroll consolidation: runs at 00:05 on the 1st of every month
    'calculate-monthly-payroll': {
        'task': 'gym_operations_payroll.tasks.calculate_monthly_payroll',
        'schedule': crontab(hour=0, minute=5, day_of_month=1),
    },

    # Auto-expire subscriptions: runs daily at 01:00
    'expire-subscriptions-daily': {
        'task': 'wger.core.tasks.expire_subscriptions',
        'schedule': crontab(hour=1, minute=0),
    },
    # LiveU Cloud attendance sync: runs every 60 seconds to fetch turnstile punches
    'sync-liveu-cloud-attendance': {
        'task': 'wger.core.tasks.sync_liveu_attendance',
        'schedule': 60.0,
    },
}
app.conf.timezone = 'Asia/Colombo'

