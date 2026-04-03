import random

from locust import HttpUser, between, events, task

SCHOOL_IDS = [f"school-{index:03d}" for index in range(1, 101)]


class CrownSchoolUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.school_id = random.choice(SCHOOL_IDS)
        self.auth_headers = {"X-School-Id": self.school_id}
        self.student_id = None

        response = self.client.post(
            "/api/auth/token/",
            json={
                "email": f"admin@{self.school_id}.crownschool.com",
                "password": "DemoPass123!",
            },
            catch_response=True,
        )

        if response.status_code == 200:
            token = response.json().get("access")
            if token:
                self.auth_headers["Authorization"] = f"Bearer {token}"
                response.success()
            else:
                response.failure("Login succeeded without access token")
        else:
            response.failure(f"Login failed: {response.status_code}")

    @task(5)
    def health_check(self):
        with self.client.get("/api/health/", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") not in {"healthy", "ok"}:
                    response.failure(f"Unhealthy payload: {data}")
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(4)
    def list_students(self):
        response = self.client.get(
            "/api/v1/students/",
            headers=self.auth_headers,
            name="/api/v1/students/ [list]",
        )
        if response.status_code == 200:
            rows = response.json()
            if isinstance(rows, list) and rows:
                self.student_id = rows[0].get("id")

    @task(3)
    def billing_runs(self):
        self.client.get(
            "/api/v1/billing/runs/",
            headers=self.auth_headers,
            name="/api/v1/billing/runs/",
        )

    @task(3)
    def admissions_summary(self):
        self.client.get(
            "/api/v1/admissions/summary/",
            headers=self.auth_headers,
            name="/api/v1/admissions/summary/",
        )

    @task(2)
    def student_detail(self):
        if self.student_id:
            self.client.get(
                f"/api/v1/students/{self.student_id}/",
                headers=self.auth_headers,
                name="/api/v1/students/[id]/",
            )


@events.quitting.add_listener
def on_stop(environment, **kwargs):
    stats = environment.stats.total
    error_rate = stats.fail_ratio
    p95_response = stats.get_response_time_percentile(0.95)
    passed = error_rate < 0.001 and p95_response < 2000

    print("\n" + "=" * 60)
    print(f"LOAD TEST RESULT: {'PASS' if passed else 'FAIL'}")
    print(f"  Total requests : {stats.num_requests}")
    print(f"  Failures       : {stats.num_failures} ({error_rate * 100:.2f}%)")
    print(f"  p50 response   : {stats.get_response_time_percentile(0.50):.0f}ms")
    print(f"  p95 response   : {p95_response:.0f}ms")
    print(f"  p99 response   : {stats.get_response_time_percentile(0.99):.0f}ms")
    print("=" * 60)

    if not passed:
        environment.process_exit_code = 1