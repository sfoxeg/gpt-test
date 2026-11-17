"""Authenticated WebSocket transport and process-local presence registry.

For multi-worker deployments, replace the in-memory registry with Redis pub/sub.
"""
import asyncio
import json
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy import select

from core.database import new_session
from core.models import ChatMembersOrm, UsersOrm
from core.settings import settings

router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, websocket: WebSocket) -> bool:
        async with self._lock:
            was_offline = not self._connections[user_id]
            self._connections[user_id].add(websocket)
            return was_offline

    async def disconnect(self, user_id: int, websocket: WebSocket) -> bool:
        async with self._lock:
            sockets = self._connections.get(user_id)
            if not sockets:
                return False
            sockets.discard(websocket)
            if sockets:
                return False
            self._connections.pop(user_id, None)
            return True

    async def online(self, user_id: int) -> bool:
        async with self._lock:
            return bool(self._connections.get(user_id))

    async def send_user(self, user_id: int, event: dict[str, Any]) -> None:
        async with self._lock:
            sockets = tuple(self._connections.get(user_id, ()))
        dead = []
        for socket in sockets:
            try:
                await socket.send_json(event)
            except Exception:
                dead.append(socket)
        for socket in dead:
            await self.disconnect(user_id, socket)

    async def send_users(self, user_ids: set[int], event: dict[str, Any]) -> None:
        await asyncio.gather(*(self.send_user(uid, event) for uid in user_ids))


manager = ConnectionManager()


async def chat_member_ids(chat_id: int) -> set[int]:
    async with new_session() as session:
        result = await session.scalars(
            select(ChatMembersOrm.user_id).where(ChatMembersOrm.chat_id == chat_id)
        )
        return set(result.all())


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = ""):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, TypeError, ValueError):
        await websocket.close(code=4401)
        return

    async with new_session() as session:
        user = await session.scalar(
            select(UsersOrm.id).where(UsersOrm.id == user_id, UsersOrm.is_active.is_(True))
        )
    if user is None:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    became_online = await manager.connect(user_id, websocket)
    if became_online:
        await _broadcast_presence(user_id, True)

    try:
        while True:
            event = await websocket.receive_json()
            if not isinstance(event, dict):
                continue
            kind = event.get("type")
            try:
                chat_id = int(event.get("chat_id", 0))
            except (TypeError, ValueError):
                continue
            members = await chat_member_ids(chat_id) if chat_id > 0 else set()
            if user_id not in members:
                continue
            recipients = members - {user_id}
            if kind == "typing":
                await manager.send_users(recipients, {
                    "type": "typing", "chat_id": chat_id, "user_id": user_id,
                    "active": bool(event.get("active", True)),
                })
            elif kind == "read":
                await manager.send_users(recipients, {
                    "type": "messages.read", "chat_id": chat_id, "user_id": user_id,
                })
    except WebSocketDisconnect:
        pass
    finally:
        became_offline = await manager.disconnect(user_id, websocket)
        if became_offline:
            await _broadcast_presence(user_id, False)


async def _broadcast_presence(user_id: int, online: bool) -> None:
    async with new_session() as session:
        result = await session.scalars(
            select(ChatMembersOrm.user_id)
            .join(ChatMembersOrm.__table__.alias("other"), ChatMembersOrm.chat_id == ChatMembersOrm.__table__.c.chat_id)
            .where(ChatMembersOrm.user_id == user_id)
        )
        # Presence is sent to known chat peers; avoid exposing global user activity.
        chat_ids = await session.scalars(
            select(ChatMembersOrm.chat_id).where(ChatMembersOrm.user_id == user_id)
        )
        ids = list(chat_ids.all())
        peers: set[int] = set()
        if ids:
            peer_result = await session.scalars(
                select(ChatMembersOrm.user_id).where(
                    ChatMembersOrm.chat_id.in_(ids), ChatMembersOrm.user_id != user_id
                )
            )
            peers = set(peer_result.all())
    await manager.send_users(peers, {"type": "presence", "user_id": user_id, "online": online})
