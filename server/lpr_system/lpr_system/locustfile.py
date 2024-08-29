from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)  # Espera entre 1 y 5 segundos entre tareas

    def on_start(self):
        self.client.post("/accounts/login/", {"username": "testuser", "password": "12345"})

    @task
    def load_home(self):
        self.client.get("/")

    @task
    def load_dashboard(self):
        self.client.get("/users/")

    @task
    def load_profile(self):
        self.client.get("/license_plate/")

    @task
    def load_settings(self):
        self.client.get("/cams/")

    # Agrega más tareas para cada URL de tu aplicación
