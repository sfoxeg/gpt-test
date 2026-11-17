from datetime import date
import pytest
from sqlalchemy import select
from core.models import UsersOrm, ProfilesOrm, ClimbingOrm
from core.repositories.auth import AuthRepository
from core.repositories.profiles import ProfilesRepository
from core.repositories.chats import ChatsRepository
from core.schemas import SUserReg, SProfileUpdate, SMessageIn

@pytest.mark.asyncio
async def test_register_persists_user_profile_and_climbing(test_db):
    await AuthRepository.register(SUserReg(email="a@example.com", password="password123",
        date_of_birth=date(1990, 1, 1), first_name="Alex", last_name="A"))
    async with test_db() as session:
        user = await session.scalar(select(UsersOrm).where(UsersOrm.email == "a@example.com"))
        assert user is not None
        assert (await session.get(ProfilesOrm, user.id)).first_name == "Alex"
        assert await session.get(ClimbingOrm, user.id) is not None

@pytest.mark.asyncio
async def test_profile_update_and_search(test_db):
    async with test_db() as session:
        users = [
            UsersOrm(email=f"{n}@example.com", hashed_password="x", date_of_birth=date(1990, 1, 1),
                profile=ProfilesOrm(first_name=n, city="Berlin", climbing=ClimbingOrm(leading=grade)))
            for n, grade in (("a", 6), ("b", 8))
        ]
        session.add_all(users)
        await session.commit()
        first_id, second_id = users[0].id, users[1].id
    await ProfilesRepository.update(first_id, SProfileUpdate(first_name="Updated", leading=7))
    results = await ProfilesRepository.search(user_id=first_id, looking_for=None, goal=None,
        age_min=18, age_max=80, city="Berlin", leading=7, where_leading=None,
        bouldering=0, where_bouldering=None, belay=None, speed=None, alpinism=None,
        order="recent", skip=0, limit=10)
    assert [row["user_id"] for row in results] == [second_id]

@pytest.mark.asyncio
async def test_chat_message_flow_and_membership(test_db):
    async with test_db() as session:
        users = [UsersOrm(email=f"u{i}@example.com", hashed_password="x",
            date_of_birth=date(1990, 1, 1),
            profile=ProfilesOrm(climbing=ClimbingOrm())) for i in range(2)]
        session.add_all(users)
        await session.commit()
        first, second = users[0].id, users[1].id
    chat = await ChatsRepository.create(first, second)
    sent = await ChatsRepository.send_message(chat["id"], first, SMessageIn(text="Hello"))
    history = await ChatsRepository.messages(chat["id"], second)
    assert sent.text == "Hello"
    assert len(history) == 1 and history[0].sender_id == first
    assert (await ChatsRepository.list_for_user(first))[0]["id"] == chat["id"]
