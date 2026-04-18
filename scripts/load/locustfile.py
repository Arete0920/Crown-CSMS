from locust import HttpUser, between, task

class CrownUser(HttpUser):
    wait_time = between(1, 2)

    @task(3)
    def health(self):
        self.client.get("/api/health/")

    @task(2)
    def roster(self):
        self.client.get("/api/v1/academics/roster/", headers={"X-School-Id": "demo-school"})

    @task(2)
    def billing(self):
        self.client.get("/api/v1/billing/overview/", headers={"X-School-Id": "demo-school"})

    @task(1)
    def attendance(self):
        self.client.get("/api/v1/attendance/summary/", headers={"X-School-Id": "demo-school"})