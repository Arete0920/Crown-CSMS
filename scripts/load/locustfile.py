from locust import HttpUser, between, task

class CrownUser(HttpUser):
    wait_time = between(1, 2)

    @task(4)
    def health(self):
        self.client.get("/api/health/")

    @task(2)
    def integrity(self):
        self.client.get("/api/integrity/")

    @task(1)
    def docs(self):
        self.client.get("/api/docs/")
