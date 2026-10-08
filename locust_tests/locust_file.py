import os
import random
import uuid
from datetime import date, timedelta

from locust import HttpUser, between, task

 
PAGINATED = os.getenv("PAGINATED", "0") == "1"
PER_PAGE = int(os.getenv("PER_PAGE", "50"))
MAX_PAGE = int(os.getenv("MAX_PAGE", "100"))
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "60"))
WAIT_MIN = float(os.getenv("WAIT_MIN", "1"))
WAIT_MAX = float(os.getenv("WAIT_MAX", "3"))


def random_birth_date() -> str:
    # Fecha de nacimiento aleatoria entre 1960 y 2008 (formato YYYY-MM-DD)
    start = date(1960, 1, 1)
    days = (date(2008, 12, 31) - start).days
    return (start + timedelta(days=random.randint(0, days))).isoformat()


def unique_user() -> dict:
    # Funcion que crea un usuario para el post
    uid = uuid.uuid4().hex
    return {
        "name": f"Locust {uid[:8]}",
        "email": f"locust_{uid}@test.com",
        "birth_date": random_birth_date(),
        # Si la API exige password u otros campos, agrégalos aquí:
        # "password": "password123",
    }


class ApiUser(HttpUser):

    wait_time = between(WAIT_MIN, WAIT_MAX)

    def _page_params(self):
        # Funcion que simula que el usuario mande parametros de paginacion
        if not PAGINATED:
            return None
        return {"page": random.randint(1, MAX_PAGE), "per_page": PER_PAGE}

    def _get(self, path: str, name: str):
        # Metodo para reutilizar en las peticiones get
        with self.client.get(
            path,
            params=self._page_params(),
            name=name,
            timeout=REQUEST_TIMEOUT,
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"HTTP {resp.status_code}")
            elif b'"data"' not in resp.content:
                resp.failure("Cuerpo sin clave 'data'")
            else:
                resp.success()

    @task(3)
    def listar_usuarios(self):
        self._get("/api/users", "GET /api/users")

    @task(3)
    def listar_correos(self):
        self._get("/api/users/emails", "GET /api/users/emails")

    @task(3)
    def usuarios_mayores_20(self):
        self._get("/api/users/over-twenty", "GET /api/users/over-twenty")

    @task(1)
    def alta_en_lote(self):
        payload = {"users": [unique_user() for _ in range(3)]}
        with self.client.post(
            "/api/users/bulk",
            json=payload,
            name="POST /api/users/bulk",
            timeout=REQUEST_TIMEOUT,
            catch_response=True,
        ) as resp:
            # Solo 201 es éxito. Un 422 (validación/duplicado) cuenta como fallo.
            if resp.status_code == 201:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}: {resp.text[:120]}")