"""
DocSetu AI - Load Testing with Locust

Simulates realistic user behavior including:
- User registration and login
- Document listing and uploads
- Compliance rule checks
- Profile views

Run: locust -f tests/load/locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between, events
import json
import os
import uuid
import time


# Minimal valid PDF bytes (single blank page)
MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
    b"xref\n0 4\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"trailer\n<< /Size 4 /Root 1 0 R >>\n"
    b"startxref\n190\n%%EOF\n"
)


class DocSetuUser(HttpUser):
    """
    Simulates a typical DocSetu AI user performing various actions
    with realistic wait times between requests.
    """

    wait_time = between(1, 5)
    host = os.getenv("TARGET_HOST", "http://localhost:8000")

    def on_start(self):
        """Register a new user and login to obtain auth token."""
        self.headers = {}
        self.user_id = str(uuid.uuid4())[:8]
        self.email = f"loadtest_{self.user_id}@test.docsetu.ai"
        self.password = f"LoadTest@{self.user_id}"

        # Attempt registration
        register_payload = {
            "email": self.email,
            "password": self.password,
            "name": f"Load Test User {self.user_id}",
        }

        try:
            with self.client.post(
                "/api/auth/register",
                json=register_payload,
                catch_response=True,
                name="/api/auth/register",
            ) as response:
                if response.status_code in (200, 201):
                    response.success()
                elif response.status_code == 409:
                    # User already exists, proceed to login
                    response.success()
                else:
                    response.failure(
                        f"Registration failed: {response.status_code} - {response.text}"
                    )
        except Exception as e:
            print(f"[{self.email}] Registration error: {e}")

        # Login to get auth token
        self._login()

    def _login(self):
        """Authenticate and store the access token."""
        login_payload = {
            "email": self.email,
            "password": self.password,
        }

        try:
            with self.client.post(
                "/api/auth/login",
                json=login_payload,
                catch_response=True,
                name="/api/auth/login",
            ) as response:
                if response.status_code == 200:
                    data = response.json()
                    token = data.get("access_token") or data.get("token", "")
                    self.headers = {
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    }
                    response.success()
                else:
                    response.failure(
                        f"Login failed: {response.status_code} - {response.text}"
                    )
                    self.headers = {}
        except Exception as e:
            print(f"[{self.email}] Login error: {e}")
            self.headers = {}

    @task(3)
    def health_check(self):
        """Lightweight health check endpoint."""
        with self.client.get(
            "/health", catch_response=True, name="/health"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(5)
    def list_documents(self):
        """List user's documents - most common operation."""
        if not self.headers:
            return

        with self.client.get(
            "/api/documents/",
            headers=self.headers,
            catch_response=True,
            name="/api/documents/",
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                # Token expired, re-login
                self._login()
                response.failure("Token expired, re-authenticating")
            else:
                response.failure(
                    f"List documents failed: {response.status_code}"
                )

    @task(2)
    def upload_document(self):
        """Upload a small test PDF document."""
        if not self.headers:
            return

        # Remove Content-Type for multipart upload
        upload_headers = {
            k: v for k, v in self.headers.items() if k != "Content-Type"
        }

        filename = f"loadtest_{self.user_id}_{int(time.time())}.pdf"

        try:
            with self.client.post(
                "/api/documents/upload",
                headers=upload_headers,
                files={"file": (filename, MINIMAL_PDF, "application/pdf")},
                catch_response=True,
                name="/api/documents/upload",
            ) as response:
                if response.status_code in (200, 201):
                    response.success()
                elif response.status_code == 401:
                    self._login()
                    response.failure("Token expired during upload")
                else:
                    response.failure(
                        f"Upload failed: {response.status_code} - {response.text[:200]}"
                    )
        except Exception as e:
            print(f"[{self.email}] Upload error: {e}")

    @task(3)
    def get_compliance_rules(self):
        """Fetch compliance rules - frequent read operation."""
        if not self.headers:
            return

        with self.client.get(
            "/api/compliance/rules",
            headers=self.headers,
            catch_response=True,
            name="/api/compliance/rules",
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                self._login()
                response.failure("Token expired")
            else:
                response.failure(
                    f"Compliance rules failed: {response.status_code}"
                )

    @task(1)
    def view_profile(self):
        """View user profile - least frequent operation."""
        if not self.headers:
            return

        with self.client.get(
            "/api/auth/me",
            headers=self.headers,
            catch_response=True,
            name="/api/auth/me",
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                self._login()
                response.failure("Token expired")
            else:
                response.failure(
                    f"View profile failed: {response.status_code}"
                )

    def on_stop(self):
        """Cleanup on user stop (optional logout)."""
        if self.headers:
            self.client.post(
                "/api/auth/logout",
                headers=self.headers,
                name="/api/auth/logout",
            )
