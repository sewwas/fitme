"""
Fit Me — LiveU Cloud-Managed Access Control & Attendance Client
Reference: LiveU Attendance API Version 1.0 (March 23, 2026)
Base URL: https://attapi.liveucloud.com/api/v1
Header: x-api-key: <BRANCH_API_KEY>
"""
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone
from urllib.parse import urlencode

from django.conf import settings
from django.utils import timezone as dj_timezone

logger = logging.getLogger('wger')


class LiveUClient:
    """REST API Client for LiveU Cloud-Managed Access Control & Attendance."""

    def __init__(self, api_url=None, api_key=None):
        self.api_url = (api_url or getattr(settings, 'LIVEU_API_URL', 'https://attapi.liveucloud.com/api/v1')).rstrip('/')
        self.api_key = api_key or getattr(settings, 'LIVEU_BRANCH_API_KEY', '')

    @property
    def is_configured(self):
        """Returns True if branch API key is configured."""
        return bool(self.api_key and self.api_key.strip())

    def _request(self, method, endpoint, data=None, params=None):
        """Internal HTTP request helper supporting GET, POST, PATCH, DELETE."""
        if not self.is_configured:
            logger.warning("[LiveU API] LIVEU_BRANCH_API_KEY is not configured in settings/env.")
            return None

        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        if params:
            clean_params = {k: v for k, v in params.items() if v is not None}
            if clean_params:
                url = f"{url}?{urlencode(clean_params)}"

        headers = {
            'x-api-key': self.api_key.strip(),
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        body_bytes = None
        if data is not None:
            body_bytes = json.dumps(data).encode('utf-8')

        req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method.upper())

        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                resp_text = response.read().decode('utf-8')
                return json.loads(resp_text) if resp_text else {'success': True}
        except urllib.error.HTTPError as ex:
            error_text = ex.read().decode('utf-8', errors='ignore')
            try:
                err_json = json.loads(error_text)
                msg = err_json.get('message', error_text)
            except Exception:
                msg = error_text
            logger.error(f"[LiveU API Error] {method} {url} returned HTTP {ex.code}: {msg}")
            return {'success': False, 'error': msg, 'status_code': ex.code}
        except Exception as ex:
            logger.error(f"[LiveU API Error] Request {method} {url} failed: {ex}")
            return {'success': False, 'error': str(ex)}

    # ─────────────────────────────────────────────
    # 1. Member Management Endpoints (/members)
    # ─────────────────────────────────────────────

    def create_member(self, member_id, name, uid=None, status="Active"):
        """
        POST /members — Register new member to LiveU Cloud and connected hardware.
        status: 'Active' or 'Inactive'
        """
        payload = {
            'memberId': str(member_id).strip(),
            'name': name.strip(),
            'status': status,
        }
        if uid:
            payload['uid'] = str(uid).strip()

        resp = self._request('POST', '/members', data=payload)
        if resp and resp.get('success'):
            data = resp.get('data', {})
            logger.info(f"[LiveU API] Registered member {member_id} ('{name}') -> LiveU ID {data.get('_id')}")
            return data
        return None

    def list_members(self):
        """GET /members — Returns all registered branch members."""
        resp = self._request('GET', '/members')
        if resp and resp.get('success'):
            return resp.get('data', [])
        return []

    def get_member(self, liveu_id):
        """GET /members/:id — Retrieve single member by MongoDB _id."""
        if not liveu_id:
            return None
        resp = self._request('GET', f"/members/{liveu_id}")
        if resp and resp.get('success'):
            return resp.get('data')
        return None

    def update_member(self, liveu_id, status=None, name=None, uid=None):
        """
        PATCH /members/:id — Update member on LiveU Cloud and hardware.
        Setting status='Inactive' instantly blocks access on all devices.
        Setting status='Active' instantly restores access.
        """
        if not liveu_id:
            return None

        payload = {}
        if status:
            payload['status'] = status
        if name:
            payload['name'] = name.strip()
        if uid is not None:
            payload['uid'] = str(uid).strip()

        if not payload:
            return None

        resp = self._request('PATCH', f"/members/{liveu_id}", data=payload)
        if resp and resp.get('success'):
            data = resp.get('data', {})
            logger.info(f"[LiveU API] Updated LiveU member {liveu_id} -> {payload}")
            return data
        return None

    def delete_member(self, liveu_id):
        """
        DELETE /members/:id — Permanently removes member from branch and hardware.
        """
        if not liveu_id:
            return False
        resp = self._request('DELETE', f"/members/{liveu_id}")
        return bool(resp and resp.get('success'))

    # ─────────────────────────────────────────────
    # 2. Attendance Endpoints (/attendances)
    # ─────────────────────────────────────────────

    def get_attendances(self, from_date=None, to_date=None, member_id=None, status=None, access=None):
        """
        GET /attendances — List real-time attendance records.
        from_date / to_date: 'YYYY-MM-DD'
        status: 'In', 'Out', 'Attend'
        access: 'Granted', 'Denied'
        """
        params = {}
        if from_date:
            params['from'] = str(from_date)
        if to_date:
            params['to'] = str(to_date)
        if member_id:
            params['memberId'] = str(member_id)
        if status:
            params['status'] = status
        if access:
            params['access'] = access

        resp = self._request('GET', '/attendances', params=params)
        if resp and resp.get('success'):
            return resp.get('data', [])
        return []

    # ─────────────────────────────────────────────
    # 3. Synchronize Cloud Records into Fit Me DB
    # ─────────────────────────────────────────────

    def sync_cloud_attendances(self, from_date=None, to_date=None):
        """
        Polls LiveU cloud attendance endpoint, persists new events into DoorAccessLog,
        and automatically triggers streak updates and staff shift tracking.
        """
        if not self.is_configured:
            return {'synced': 0, 'skipped': 0, 'status': 'unconfigured'}

        if not from_date:
            from_date = dj_timezone.now().date().isoformat()

        records = self.get_attendances(from_date=from_date, to_date=to_date)
        if not records:
            return {'synced': 0, 'skipped': 0, 'status': 'no_new_records'}

        from django.contrib.auth import get_user_model
        from wger.zkbio_integration.models import BiometricProfile, DoorAccessLog
        from wger.membership.models import MemberProfile
        User = get_user_model()

        synced_count = 0
        skipped_count = 0

        for r in records:
            liveu_att_id = r.get('_id')
            if not liveu_att_id:
                continue

            if DoorAccessLog.objects.filter(liveu_attendance_id=liveu_att_id).exists():
                skipped_count += 1
                continue

            pin = str(r.get('memberId', '')).strip()
            date_time_raw = r.get('dateTime')
            punch_time = dj_timezone.now()
            if date_time_raw:
                try:
                    punch_time = datetime.fromisoformat(date_time_raw.replace('Z', '+00:00'))
                except Exception:
                    pass

            access_str = r.get('access', 'Granted')
            raw_status = r.get('status', 'In')

            if access_str == 'Denied':
                event_type = 'DENIED'
            elif raw_status == 'Out':
                event_type = 'EXIT'
            else:
                event_type = 'ENTRY'

            # Match User
            bio_prof = BiometricProfile.objects.filter(zk_pin=pin).select_related('user').first()
            user = bio_prof.user if bio_prof else None
            if not user:
                mp = MemberProfile.objects.filter(biometric_pin=pin).select_related('user').first()
                if mp:
                    user = mp.user

            device_info = r.get('device', {}) or {}
            terminal_name = device_info.get('name') or 'LiveU Cloud Reader'

            log = DoorAccessLog.objects.create(
                user=user,
                zk_pin=pin,
                punch_time=punch_time,
                event_type=event_type,
                verify_mode='FACE_ID',
                device_ip='cloud',
                terminal_name=terminal_name,
                liveu_attendance_id=liveu_att_id,
                raw_payload=r,
            )
            synced_count += 1

            # Update workout streak on ENTRY
            if user and event_type == 'ENTRY':
                try:
                    from wger.habit.models import WorkoutStreak
                    streak, _ = WorkoutStreak.objects.get_or_create(member=user)
                    streak.record_checkin()
                except Exception as ex:
                    logger.error(f"[LiveU Sync] Error updating workout streak for {pin}: {ex}")

            # Update staff attendance on floor
            if user and user.is_staff:
                try:
                    from wger.gym_operations_payroll.models import StaffShift
                    shift_date = punch_time.date()
                    shift = StaffShift.objects.filter(staff_user=user, shift_date=shift_date).first()
                    if shift:
                        if event_type == 'ENTRY':
                            if not shift.actual_first_in:
                                shift.actual_first_in = punch_time
                            shift.status = 'ON_FLOOR'
                            shift.is_off_floor = False
                            shift.save(update_fields=['actual_first_in', 'status', 'is_off_floor'])
                        elif event_type == 'EXIT':
                            shift.actual_last_out = punch_time
                            shift.save(update_fields=['actual_last_out'])
                except Exception as ex:
                    logger.error(f"[LiveU Sync] Error updating staff shift for {pin}: {ex}")

        return {
            'status': 'success',
            'synced': synced_count,
            'skipped': skipped_count,
            'total_fetched': len(records),
        }
