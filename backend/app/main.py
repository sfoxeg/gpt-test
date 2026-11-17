from datetime import date
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session, joinedload
from .database import Base, engine, get_db
from . import models, schemas
from .security import hash_password, verify_password, create_token, current_user

Base.metadata.create_all(bind=engine)
app = FastAPI(title="CatchMe API", version="1.0.0", description="Climbing partner finder API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/auth/register", status_code=201)
def register(data: schemas.RegisterIn, db: Session = Depends(get_db)):
    if data.date_of_birth > date.today():
        raise HTTPException(422, "Date of birth cannot be in the future")
    if db.scalar(select(models.User).where(models.User.email == data.email)):
        raise HTTPException(409, "Email already registered")
    user = models.User(email=data.email, hashed_password=hash_password(data.password), sex=data.sex, date_of_birth=data.date_of_birth)
    user.profile = models.Profile(first_name=data.first_name, last_name=data.last_name, climbing=models.Climbing())
    db.add(user); db.commit()
    return {"access_token": create_token(user.id), "token_type": "bearer"}

@app.post("/api/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(models.User).where(models.User.email == form.username))
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(401, "Incorrect email or password")
    return {"access_token": create_token(user.id), "token_type": "bearer"}

@app.get("/api/me")
def me(user: models.User = Depends(current_user)):
    p = user.profile
    return {"id": user.id, "email": user.email, "sex": user.sex, "date_of_birth": user.date_of_birth, "profile": schemas.ProfileOut.model_validate(p), "climbing": {k: getattr(p.climbing, k) for k in ("leading","where_leading","bouldering","where_bouldering","speed","alpinism","belay","belay_description")}}

@app.put("/api/me/profile")
def update_profile(data: schemas.ProfileUpdate, db: Session = Depends(get_db), user: models.User = Depends(current_user)):
    p = user.profile
    for key in ("goal","first_name","last_name","description","city","height","weight"):
        setattr(p, key, getattr(data, key))
    for key in ("leading","where_leading","bouldering","where_bouldering","speed","alpinism","belay","belay_description"):
        setattr(p.climbing, key, getattr(data, key))
    db.commit()
    return {"status": "updated"}

@app.get("/api/profiles")
def search_profiles(looking_for: str | None = None, goal: int | None = Query(None, ge=0, le=3), age_min: int = Query(18, ge=18, le=100), age_max: int = Query(80, ge=18, le=100), city: str | None = None, leading: int = 0, where_leading: int | None = None, bouldering: int = 0, where_bouldering: int | None = None, belay: int | None = None, speed: bool | None = None, alpinism: bool | None = None, order: str = "recent", skip: int = 0, limit: int = Query(8, ge=1, le=50), db: Session = Depends(get_db), user: models.User = Depends(current_user)):
    today = date.today()
    q = select(models.Profile).join(models.User).join(models.Climbing).options(joinedload(models.Profile.user), joinedload(models.Profile.climbing)).where(models.User.is_active.is_(True), models.User.id != user.id)
    if looking_for == "male": q = q.where(models.User.sex.is_(False))
    if looking_for == "female": q = q.where(models.User.sex.is_(True))
    if goal is not None and goal < 3: q = q.where(models.Profile.goal == goal)
    if city: q = q.where(models.Profile.city.ilike(f"%{city}%"))
    if age_min > age_max: raise HTTPException(422, "age_min must be <= age_max")
    q = q.where(models.User.date_of_birth <= date(today.year-age_min, today.month, min(today.day, 28)), models.User.date_of_birth >= date(today.year-age_max-1, today.month, min(today.day, 28)))
    if leading: q = q.where(models.Climbing.leading >= leading)
    if where_leading is not None and where_leading < 2: q = q.where(or_(models.Climbing.where_leading == where_leading, models.Climbing.where_leading == 2))
    if bouldering: q = q.where(models.Climbing.bouldering >= bouldering)
    if where_bouldering is not None and where_bouldering < 2: q = q.where(or_(models.Climbing.where_bouldering == where_bouldering, models.Climbing.where_bouldering == 2))
    if belay is not None: q = q.where(models.Climbing.belay == belay)
    if speed: q = q.where(models.Climbing.speed.is_(True))
    if alpinism: q = q.where(models.Climbing.alpinism.is_(True))
    q = q.order_by(models.User.date_of_birth.asc() if order == "oldest" else models.User.date_of_birth.desc() if order == "youngest" else models.User.date_joined.desc()).offset(skip).limit(limit)
    rows = db.scalars(q).unique().all()
    return [{"user_id":p.user_id,"first_name":p.first_name,"last_name":p.last_name,"description":p.description,"city":p.city,"goal":p.goal,"date_of_birth":p.user.date_of_birth,"sex":p.user.sex,"avatar":p.avatar,"climbing":{k:getattr(p.climbing,k) for k in ("leading","where_leading","bouldering","where_bouldering","speed","alpinism","belay")}} for p in rows]

@app.post("/api/chats", status_code=201)
def create_chat(other_user_id: int, db: Session = Depends(get_db), user: models.User = Depends(current_user)):
    other = db.get(models.User, other_user_id)
    if not other or other.id == user.id: raise HTTPException(404, "User not found")
    chat = models.Chat()
    chat.members = [models.ChatMember(user_id=user.id), models.ChatMember(user_id=other.id)]
    db.add(chat); db.commit(); db.refresh(chat)
    return {"id": chat.id}

@app.get("/api/chats")
def list_chats(db: Session = Depends(get_db), user: models.User = Depends(current_user)):
    chats = db.scalars(select(models.Chat).join(models.ChatMember).where(models.ChatMember.user_id == user.id).options(joinedload(models.Chat.members))).unique().all()
    return [{"id":c.id,"members":[m.user_id for m in c.members]} for c in chats]

@app.get("/api/chats/{chat_id}/messages")
def list_messages(chat_id: int, db: Session = Depends(get_db), user: models.User = Depends(current_user)):
    member = db.scalar(select(models.ChatMember).where(models.ChatMember.chat_id == chat_id, models.ChatMember.user_id == user.id))
    if not member: raise HTTPException(404, "Chat not found")
    messages = db.scalars(select(models.Message).where(models.Message.chat_id == chat_id).order_by(models.Message.created_at)).all()
    return [schemas.MessageOut.model_validate(m) for m in messages]

@app.post("/api/chats/{chat_id}/messages", status_code=201)
def send_message(chat_id: int, data: schemas.MessageIn, db: Session = Depends(get_db), user: models.User = Depends(current_user)):
    member = db.scalar(select(models.ChatMember).where(models.ChatMember.chat_id == chat_id, models.ChatMember.user_id == user.id))
    if not member: raise HTTPException(404, "Chat not found")
    msg = models.Message(chat_id=chat_id, sender_id=user.id, text=data.text)
    db.add(msg); db.commit(); db.refresh(msg)
    return schemas.MessageOut.model_validate(msg)
