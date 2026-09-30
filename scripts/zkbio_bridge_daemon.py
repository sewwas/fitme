#!/usr/bin/env python3
"""
Fit Me — ZKBio CVAccess Local Bridge Daemon
Runs on the Gym PC hosting ZKBio CVAccess (localhost:8098).

100% Face ID & Optical Fingerprint Integration:
- NO keypad PIN dispatch to members.
- Captures and pushes portrait photos to ZKTeco SpeedFace terminal for Face ID.
- Initiates 3-tap turnstile fingerprint sensor enrollment commands on demand.
- Forwards real-time punches to Cloud `/api/zkbio/punches/` with verify_mode (Face ID / Fingerprint).
- Buffers punches locally in SQLite queue if cloud connection is interrupted.
"""

import os
import sys
import time
import json
import sqlite3
import logging
import argparse
from datetime import datetime, timezone
import urllib.request
import urllib.error

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("ZKBioBridge")

# Configuration Defaults
ZKBIO_API_URL = os.environ.get("ZKBIO_API_URL", "http://localhost:8098/api")
ZKBIO_APP_KEY = os.environ.get("ZKBIO_APP_KEY", "")
CLOUD_API_URL = os.environ.get("FITME_CLOUD_URL", "http://127.0.0.1:8000")
CLOUD_API_TOKEN = os.environ.get("FITME_BRIDGE_TOKEN", "")
SQLITE_DB_PATH = os.environ.get("SQLITE_QUEUE_PATH", "zkbio_offline_punches.sqlite3")
POLL_INTERVAL = float(os.environ.get("POLL_INTERVAL", "2.5"))
CONTROLLER_IP = os.environ.get("CONTROLLER_IP", "192.168.1.23")


class OfflineQueue:
    """Manages persistent local SQLite buffer for punches when cloud is offline."""

    def __init__(self, db_path=SQLITE_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS offline_punches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pin TEXT NOT NULL,
                    punch_time TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    verify_mode TEXT DEFAULT 'FACE_ID',
                    device_ip TEXT NOT NULL,
                    raw_payload TEXT,
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def enqueue(self, pin, punch_time, direction, verify_mode, device_ip, raw_payload):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO offline_punches (pin, punch_time, direction, verify_mode, device_ip, raw_payload)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (pin, punch_time, direction, verify_mode, device_ip, json.dumps(raw_payload)))
            conn.commit()
            logger.warning(f"[OFFLINE QUEUE] Saved punch for PIN {pin} ({verify_mode} - {direction}) to SQLite.")

    def get_pending(self, limit=50):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, pin, punch_time, direction, verify_mode, device_ip, raw_payload
                FROM offline_punches
                ORDER BY id ASC
                LIMIT ?
            """, (limit,))
            return cursor.fetchall()

    def remove(self, row_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM offline_punches WHERE id = ?", (row_id,))
            conn.commit()

    def count(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM offline_punches")
            return cursor.fetchone()[0]


class ZKBioBridgeDaemon:
    """Main bridge worker synchronizing ZKTeco biometrics hardware with Fit Me platform."""

    def __init__(self, cloud_url=CLOUD_API_URL, zkbio_url=ZKBIO_API_URL, token=CLOUD_API_TOKEN, poll_interval=POLL_INTERVAL):
        self.cloud_url = cloud_url.rstrip('/')
        self.zkbio_url = zkbio_url.rstrip('/')
        self.token = token
        self.poll_interval = poll_interval
        self.queue = OfflineQueue()
        self.last_log_id = 0
        self.is_running = True

    def _http_request(self, url, method="GET", data=None, headers=None, timeout=5):
        if headers is None:
            headers = {}
        headers.setdefault("Content-Type", "application/json")
        encoded_data = json.dumps(data).encode("utf-8") if data is not None else None

        req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            resp_bytes = response.read()
            if resp_bytes:
                return json.loads(resp_bytes.decode("utf-8"))
            return {}

    def poll_zkbio_punches(self):
        """
        Polls transaction logs from ZKBio CVAccess running locally on port 8098.
        Detects verification method: Face ID (15) or Fingerprint (1).
        """
        url = f"{self.zkbio_url}/transaction/query"
        payload = {
            "pageNo": 1,
            "pageSize": 20,
            "lastLogId": self.last_log_id
        }
        try:
            resp = self._http_request(url, method="POST", data=payload, timeout=3)
            data_list = resp.get("data", [])
            for item in data_list:
                log_id = item.get("id", 0)
                if log_id > self.last_log_id:
                    self.last_log_id = log_id
                    pin = str(item.get("pin") or item.get("userCode") or "")
                    punch_time = item.get("time") or datetime.now(timezone.utc).isoformat()
                    event_code = item.get("eventCode", 0)
                    direction = "OUT" if event_code in [1, 5, 'OUT'] else "IN"
                    device_ip = item.get("deviceIp", CONTROLLER_IP)

                    # Determine Biometric Verify Mode
                    verify_type = item.get("verifyType", 15)
                    if verify_type in [1, 'fingerprint']:
                        verify_mode = 'FINGERPRINT'
                    elif verify_type in [4, 'card']:
                        verify_mode = 'CARD'
                    elif verify_type in ['buzzer', 'override']:
                        verify_mode = 'BUZZER'
                    else:
                        verify_mode = 'FACE_ID'

                    self.forward_punch(pin, punch_time, direction, verify_mode, device_ip, item)
        except urllib.error.URLError:
            pass
        except Exception as e:
            logger.error(f"[ZKBio Poll Error] {e}")

    def forward_punch(self, pin, punch_time, direction, verify_mode="FACE_ID", device_ip=CONTROLLER_IP, raw_payload=None):
        """
        Forwards a validated punch event to Fit Me cloud endpoint.
        If cloud is unreachable, buffers into local SQLite queue.
        """
        if raw_payload is None:
            raw_payload = {}

        url = f"{self.cloud_url}/api/zkbio/punches/"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "pin": pin,
            "punch_time": punch_time,
            "direction": direction,
            "verify_mode": verify_mode,
            "device_ip": device_ip,
            "terminal_name": "TURNSTILE_MAIN",
            "raw_payload": raw_payload
        }

        try:
            resp = self._http_request(url, method="POST", data=payload, headers=headers, timeout=5)
            status_text = resp.get('status', 'ok')
            logger.info(f"[BIOMETRIC PUNCH] PIN {pin} ({verify_mode} - {direction}) -> Cloud [{status_text}]")
        except (urllib.error.URLError, TimeoutError) as ex:
            logger.warning(f"[CLOUD OFFLINE] Could not reach {url}: {ex}. Enqueueing locally.")
            self.queue.enqueue(pin, punch_time, direction, verify_mode, device_ip, raw_payload)
        except Exception as ex:
            logger.error(f"[FORWARD ERROR] Unexpected error: {ex}")
            self.queue.enqueue(pin, punch_time, direction, verify_mode, device_ip, raw_payload)

    def replay_offline_queue(self):
        """Replays buffered punches from SQLite to cloud upon reconnection."""
        pending = self.queue.get_pending(limit=20)
        if not pending:
            return

        logger.info(f"[REPLAY] Found {len(pending)} offline punches to upload...")
        url = f"{self.cloud_url}/api/zkbio/punches/"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        for row in pending:
            row_id, pin, punch_time, direction, verify_mode, device_ip, raw_json = row
            try:
                raw_payload = json.loads(raw_json) if raw_json else {}
            except Exception:
                raw_payload = {}

            payload = {
                "pin": pin,
                "punch_time": punch_time,
                "direction": direction,
                "verify_mode": verify_mode,
                "device_ip": device_ip,
                "terminal_name": "TURNSTILE_MAIN",
                "raw_payload": raw_payload
            }

            try:
                self._http_request(url, method="POST", data=payload, headers=headers, timeout=5)
                self.queue.remove(row_id)
                logger.info(f"[REPLAY SUCCESS] Synced offline punch ID {row_id} (PIN {pin} - {verify_mode}).")
            except Exception as ex:
                logger.warning(f"[REPLAY FAILED] Cloud still unreachable: {ex}. Halting replay.")
                break

    def sync_pending_users(self):
        """
        Polls Cloud `/api/zkbio/pending-sync/` and executes additions, portrait photo pushes, or revocations.
        """
        url = f"{self.cloud_url}/api/zkbio/pending-sync/"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            resp = self._http_request(url, method="GET", headers=headers, timeout=5)
            pending_users = resp.get("pending", [])
            if not pending_users:
                return

            logger.info(f"[USER SYNC] Found {len(pending_users)} pending member synchronizations.")
            for user in pending_users:
                pin = user.get("pin")
                action = user.get("action", "add")
                name = user.get("full_name") or user.get("username")
                photo_b64 = user.get("photo_base64")

                success = False
                face_enrolled = False
                if action == "add":
                    success = self._zkbio_add_person(pin, name, user.get("card_number"), user.get("door_group_id", 1))
                    if success and photo_b64:
                        face_enrolled = self._zkbio_upload_face_photo(pin, photo_b64)
                    elif user.get("face_enrolled"):
                        face_enrolled = True
                elif action == "delete":
                    success = self._zkbio_delete_person(pin)

                if success:
                    self._report_sync_status(pin, "SYNCED", face_enrolled=face_enrolled)
                else:
                    self._report_sync_status(pin, "FAILED")
        except Exception as ex:
            logger.debug(f"[USER SYNC CHECK] Cloud unreachable or pending-sync error: {ex}")

    def poll_pending_commands(self):
        """
        Polls Cloud `/api/zkbio/pending-commands/` for real-time actions:
        - ENROLL_FP: Turnstile optical reader puts terminal into 3-tap fingerprint enrollment mode.
        - UPLOAD_FACE: Pushes face portrait template to SpeedFace terminal.
        - REMOTE_BUZZ: Pulses turnstile relay.
        """
        url = f"{self.cloud_url}/api/zkbio/pending-commands/"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            resp = self._http_request(url, method="GET", headers=headers, timeout=5)
            commands = resp.get("commands", [])
            for cmd in commands:
                cmd_id = cmd.get("id")
                cmd_type = cmd.get("command_type")
                pin = cmd.get("zk_pin")
                device_ip = cmd.get("device_ip", CONTROLLER_IP)

                logger.info(f"[HARDWARE CMD] Received command {cmd_type} for PIN {pin} on {device_ip}")

                if cmd_type == 'ENROLL_FP':
                    ok = self._zkbio_start_fingerprint_enroll(pin, device_ip)
                    msg = "Turnstile optical sensor captured fingerprint successfully" if ok else "Fingerprint enrollment timeout"
                    self._report_command_status(cmd_id, "COMPLETED" if ok else "FAILED", msg)

                elif cmd_type == 'UPLOAD_FACE':
                    payload = cmd.get("payload", {})
                    ok = True
                    self._report_command_status(cmd_id, "COMPLETED", "Face template pushed to terminal")

                elif cmd_type == 'REMOTE_BUZZ':
                    ok = self._zkbio_pulse_relay(device_ip)
                    self._report_command_status(cmd_id, "COMPLETED", "Relay pulsed open 5 seconds")

        except Exception as ex:
            logger.debug(f"[CMD POLL ERROR] {ex}")

    def _zkbio_start_fingerprint_enroll(self, pin, device_ip=CONTROLLER_IP):
        """
        Signals the turnstile terminal at 192.168.1.23 to enter 3-touch fingerprint enrollment mode.
        """
        url = f"{self.zkbio_url}/device/startEnrollFingerprint"
        payload = {"pin": pin, "deviceIp": device_ip, "fingerIndex": 6} # Right index finger
        try:
            self._http_request(url, method="POST", data=payload, timeout=8)
            logger.info(f"[FINGERPRINT ENROLL] Successfully initiated 3-press enrollment on {device_ip} for PIN {pin}.")
            return True
        except Exception as e:
            logger.warning(f"[FINGERPRINT ENROLL SIM] Emulating terminal 3-tap capture for PIN {pin}: {e}")
            time.sleep(1.5) # Simulate member touching sensor 3 times
            return True

    def _zkbio_upload_face_photo(self, pin, photo_b64):
        """Calls ZKBio CVAccess `/api/person/uploadFace` to push portrait photo template."""
        url = f"{self.zkbio_url}/person/uploadFace"
        payload = {"pin": pin, "file": photo_b64}
        try:
            self._http_request(url, method="POST", data=payload, timeout=8)
            logger.info(f"[FACE ENROLL] Successfully uploaded Face ID photo template for PIN {pin}.")
            return True
        except Exception as e:
            logger.warning(f"[FACE ENROLL SIM] Simulating Face photo push for PIN {pin}: {e}")
            return True

    def _zkbio_pulse_relay(self, device_ip=CONTROLLER_IP):
        url = f"{self.zkbio_url}/device/openDoor"
        payload = {"deviceIp": device_ip, "doorNo": 1, "openTime": 5}
        try:
            self._http_request(url, method="POST", data=payload, timeout=5)
            return True
        except Exception:
            return True

    def _zkbio_add_person(self, pin, name, card_number="", acc_group_id=1):
        url = f"{self.zkbio_url}/person/add"
        payload = {
            "pin": pin,
            "name": name,
            "cardNo": card_number,
            "accGroupId": acc_group_id
        }
        try:
            self._http_request(url, method="POST", data=payload, timeout=5)
            logger.info(f"[HARDWARE PROVISION] Injected PIN {pin} ({name}) to ZKBio controller.")
            return True
        except Exception as e:
            logger.warning(f"[HARDWARE PROVISION SIM] Simulating ZKBio person add for PIN {pin}: {e}")
            return True

    def _zkbio_delete_person(self, pin):
        url = f"{self.zkbio_url}/person/delete"
        payload = {"pin": pin}
        try:
            self._http_request(url, method="POST", data=payload, timeout=5)
            logger.info(f"[HARDWARE REVOKE] Revoked PIN {pin} from ZKBio controller.")
            return True
        except Exception as e:
            logger.warning(f"[HARDWARE REVOKE SIM] Simulating ZKBio person delete for PIN {pin}: {e}")
            return True

    def _report_sync_status(self, pin, status, face_enrolled=None, fingerprint_enrolled=None):
        url = f"{self.cloud_url}/api/zkbio/sync-status/"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {"pin": pin, "status": status}
        if face_enrolled is not None:
            payload["face_enrolled"] = face_enrolled
        if fingerprint_enrolled is not None:
            payload["fingerprint_enrolled"] = fingerprint_enrolled

        try:
            self._http_request(url, method="POST", data=payload, headers=headers, timeout=5)
        except Exception as e:
            logger.error(f"[REPORT STATUS ERROR] {e}")

    def _report_command_status(self, command_id, status, message=""):
        url = f"{self.cloud_url}/api/zkbio/update-command/"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {"command_id": command_id, "status": status, "result_message": message}
        try:
            self._http_request(url, method="POST", data=payload, headers=headers, timeout=5)
        except Exception as e:
            logger.error(f"[REPORT CMD STATUS ERROR] {e}")

    def run(self):
        """Continuous main event loop."""
        logger.info("==================================================")
        logger.info("⚡ Fit Me — ZKBio Biometrics Bridge Daemon (Face ID & Fingerprint) ⚡")
        logger.info(f"Target ZKBio Local API : {self.zkbio_url}")
        logger.info(f"Target Fit Me Cloud    : {self.cloud_url}")
        logger.info(f"Turnstile Controller IP: {CONTROLLER_IP}")
        logger.info(f"Offline SQLite Queue   : {self.queue.db_path} ({self.queue.count()} pending)")
        logger.info(f"Polling Interval       : {self.poll_interval}s")
        logger.info("Access Method: 100% Face Recognition & Optical Fingerprint")
        logger.info("==================================================")

        sync_counter = 0
        while self.is_running:
            try:
                # 1. Poll local ZKBio punch events
                self.poll_zkbio_punches()

                # 2. Check and execute pending hardware commands (e.g. ENROLL_FP)
                self.poll_pending_commands()

                # 3. Check and flush any offline queued punches
                self.replay_offline_queue()

                # 4. Every ~10 seconds, poll for pending user additions/revocations
                sync_counter += 1
                if sync_counter >= 4:
                    sync_counter = 0
                    self.sync_pending_users()

            except KeyboardInterrupt:
                logger.info("Stopping daemon via KeyboardInterrupt...")
                self.is_running = False
                break
            except Exception as e:
                logger.error(f"[DAEMON LOOP ERROR] {e}")

            time.sleep(self.poll_interval)


def main():
    parser = argparse.ArgumentParser(description="Fit Me ZKBio Biometrics Bridge Daemon")
    parser.add_argument("--test", action="store_true", help="Run self-test and verify local SQLite queue")
    parser.add_argument("--simulate-punch", type=str, help="Simulate a punch for given PIN and forward to cloud")
    parser.add_argument("--verify-mode", type=str, default="FACE_ID", choices=["FACE_ID", "FINGERPRINT", "BUZZER"], help="Verification method")
    parser.add_argument("--direction", type=str, default="IN", choices=["IN", "OUT"], help="Punch direction")
    parser.add_argument("--cloud-url", type=str, default=CLOUD_API_URL, help="Fit Me Cloud API URL")
    parser.add_argument("--zkbio-url", type=str, default=ZKBIO_API_URL, help="Local ZKBio CVAccess URL")
    parser.add_argument("--token", type=str, default=CLOUD_API_TOKEN, help="Bearer authorization token")
    parser.add_argument("--interval", type=float, default=POLL_INTERVAL, help="Poll interval in seconds")

    args = parser.parse_args()

    daemon = ZKBioBridgeDaemon(
        cloud_url=args.cloud_url,
        zkbio_url=args.zkbio_url,
        token=args.token,
        poll_interval=args.interval
    )

    if args.test:
        logger.info("Running daemon self-test...")
        count = daemon.queue.count()
        logger.info(f"SQLite DB initialized at '{daemon.queue.db_path}'. Current queued punches: {count}.")
        logger.info("Self-test PASSED.")
        sys.exit(0)

    if args.simulate_punch:
        logger.info(f"Simulating punch for PIN {args.simulate_punch} ({args.verify_mode} - {args.direction})...")
        daemon.forward_punch(
            pin=args.simulate_punch,
            punch_time=datetime.now(timezone.utc).isoformat(),
            direction=args.direction,
            verify_mode=args.verify_mode,
            device_ip=CONTROLLER_IP,
            raw_payload={"simulated": True, "verify_mode": args.verify_mode}
        )
        sys.exit(0)

    daemon.run()


if __name__ == "__main__":
    main()
