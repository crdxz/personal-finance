from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

from app.api.dependencies import get_db
from app.database.base import Base
from app.main import app


test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
Base.metadata.create_all(test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "auth-service"}


def test_register_and_login() -> None:
    email = "test.user@example.com"
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Strong-password1"},
    )

    assert register_response.status_code == 201
    assert register_response.json()["email"] == email
    assert register_response.json()["access_token"]

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Strong-password1"},
    )

    assert login_response.status_code == 200
    assert login_response.json()["token_type"] == "bearer"
    assert login_response.json()["access_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login_response.json()['access_token']}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["email"] == email


def test_protected_endpoint_requires_token() -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_login_rejects_invalid_password() -> None:
    email = "invalid-login@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Strong-password1"},
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Wrong-password1"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_registration_rejects_weak_password() -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "password": "password"},
    )

    assert response.status_code == 422
    assert "uppercase" in response.json()["detail"][0]["msg"]


def test_registration_rejects_duplicate_email() -> None:
    email = "duplicate@example.com"
    payload = {"email": email, "password": "Strong-password1"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "Email is already registered"
