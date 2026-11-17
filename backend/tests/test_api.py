from datetime import date
import pytest
from core.models import UsersOrm, ProfilesOrm, ClimbingOrm
from core.secure import create_access_token

@pytest.mark.asyncio
async def test_register_and_login(client):
    response = await client.post("/api/v1/auth/register", json={
        "email": "api@example.com", "password": "password123",
        "date_of_birth": "1994-02-01", "first_name": "API", "last_name": "User"})
    assert response.status_code == 201
    login = await client.post("/api/v1/auth/login",
        data={"username": "api@example.com", "password": "password123"})
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_current_user_endpoint(client, test_db):
    async with test_db() as session:
        user = UsersOrm(email="me@example.com", hashed_password="x",
            date_of_birth=date(1990, 1, 1),
            profile=ProfilesOrm(first_name="Test", climbing=ClimbingOrm()))
        session.add(user)
        await session.commit()
        user_id = user.id
    response = await client.get("/api/v1/me",
        headers={"Authorization": f"Bearer {create_access_token(user_id)}"})
    assert response.status_code == 200
    assert response.json()["profile"]["first_name"] == "Test"

@pytest.mark.asyncio
async def test_protected_endpoint_requires_auth(client):
    response = await client.get("/api/v1/chats")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_profile_update_api(client, test_db):
    async with test_db() as session:
        user = UsersOrm(email="edit@example.com", hashed_password="x",
            date_of_birth=date(1990, 1, 1),
            profile=ProfilesOrm(first_name="Before", climbing=ClimbingOrm()))
        session.add(user)
        await session.commit()
        user_id = user.id
    response = await client.put("/api/v1/profiles/me",
        headers={"Authorization": f"Bearer {create_access_token(user_id)}"},
        json={"first_name": "After", "leading": 5})
    assert response.status_code == 200
