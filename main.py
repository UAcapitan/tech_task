
import asyncio
from fastapi import FastAPI, Header, Depends, HTTPException, status, Query, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Dict, List, Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from ai import query_to_ai


app = FastAPI()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
COMMENT_STATUS_ACTIVE = "active"
COMMENT_STATUS_BLOCKED = "blocked"


fake_users_db: Dict[str, dict] = {}
fake_posts_db: Dict[str, dict] = {}
fake_comments_db: Dict[str, dict] = {}


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class PostCreate(BaseModel):
    title: str
    content: str
    auto_reply_enabled: bool = False
    auto_reply_delay: Optional[float] = None

class PostUpdate(BaseModel):
    title: str
    content: str

class CommentCreate(BaseModel):
    content: str

class CommentUpdate(BaseModel):
    content: str

class DailyCommentBreakdown(BaseModel):
    date: str
    created_count: int
    blocked_count: int


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def check_status_comment(comment):
    result_from_ai = query_to_ai('''Imagine that you are a filter of foul language and insults.
If there is something here that falls under bad words, please write 'Blocked', if not, write 'Active'.

Comment to check:\n''' + comment)
    
    if "Active" in result_from_ai: status = COMMENT_STATUS_ACTIVE
    else: status = COMMENT_STATUS_BLOCKED
    return status

async def auto_reply_to_comment(post_id: int, comment_id: int):
    post = fake_posts_db.get(post_id)
    comment = next((c for c in fake_comments_db.get(post_id, []) if c["id"] == comment_id), None)
    
    if not post or not comment:
        return

    reply_content = generate_relevant_reply(post["content"], comment["content"])
    new_comment_id = len(fake_comments_db[post_id]) + 1
    fake_comments_db[post_id].append({
        "id": new_comment_id,
        "content": reply_content,
        "owner": "auto_reply_bot",
        "created_at": datetime.utcnow(),
        "status": COMMENT_STATUS_ACTIVE,
    })

def generate_relevant_reply(post_content: str, comment_content: str) -> str:
    return query_to_ai(
        f'''Create and return only one comment, using context of post and previous user comment.

Post:
{post_content}

Previous user comment:
{comment_content}
''')

def get_current_user(token: str = Header(..., alias="Authorization")):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Remove the "Bearer " prefix from the token if present
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
            
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        user = fake_users_db.get(username)
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

async def auto_reply_task(post_id: int, comment_id: int, delay_seconds: int):
    await asyncio.sleep(delay_seconds)
    await auto_reply_to_comment(post_id, comment_id)


@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    fake_users_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password,
    }
    return {"message": "User registered successfully"}

@app.post("/login", response_model=Token)
async def login(user: UserLogin):
    db_user = fake_users_db.get(user.username)
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/posts/", status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate, token: dict = Depends(get_current_user)):
    post_id = len(fake_posts_db) + 1
    fake_posts_db[post_id] = {
        "id": post_id,
        "title": post.title,
        "content": post.content,
        "owner": token["username"],
        "created_at": datetime.utcnow(),
        "auto_reply_enabled": post.auto_reply_enabled,
        "auto_reply_delay": post.auto_reply_delay
    }
    return fake_posts_db[post_id]

@app.get("/posts/", response_model=list)
async def get_posts():
    return list(fake_posts_db.values())

@app.get("/posts/{post_id}", response_model=dict)
async def get_post(post_id: int):
    post = fake_posts_db.get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@app.put("/posts/{post_id}", response_model=dict)
async def update_post(post_id: int, post_update: PostUpdate, token: str = Depends(get_current_user)):
    post = fake_posts_db.get(post_id)
    if not post or post["owner"] != token["username"]:
        raise HTTPException(status_code=404, detail="Post not found or not authorized")
    post.update(post_update.dict(exclude_unset=True))
    return post

@app.delete("/posts/{post_id}")
async def delete_post(post_id: int, token: str = Depends(get_current_user)):
    post = fake_posts_db.get(post_id)
    if not post or post["owner"] != token["username"]:
        raise HTTPException(status_code=404, detail="Post not found or not authorized")
    del fake_posts_db[post_id]
    return {"detail": "Post deleted"}

@app.post("/posts/{post_id}/comments", status_code=status.HTTP_201_CREATED)
async def create_comment(post_id: int, comment: CommentCreate, background_tasks: BackgroundTasks, token: str = Depends(get_current_user)):
    if post_id not in fake_posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    comment_id = len(fake_comments_db.get(post_id, [])) + 1
    status = check_status_comment(comment.content)

    new_comment = {
        "id": comment_id,
        "content": comment.content,
        "owner": token["username"],
        "created_at": datetime.utcnow(),
        "status": status,
    }
    fake_comments_db.setdefault(post_id, []).append(new_comment)

    if status == "active":
        post = fake_posts_db[post_id]
        if post.get("auto_reply_enabled") and post.get("auto_reply_delay") is not None:
            delay_seconds = int(post["auto_reply_delay"] * 60)
            background_tasks.add_task(auto_reply_task, post_id, comment_id, delay_seconds)
    
    return new_comment

@app.get("/api/posts/comments", response_model=list)
async def get_all_comments():
    return [fake_comments_db,]

@app.get("/posts/{post_id}/comments", response_model=list)
async def get_comments(post_id: int):
    if post_id not in fake_posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    return fake_comments_db.get(post_id, [])

@app.put("/posts/{post_id}/comments/{comment_id}", response_model=dict)
async def update_comment(post_id: int, comment_id: int, comment_update: CommentUpdate, token: str = Depends(get_current_user)):
    comments = fake_comments_db.get(post_id)
    if not comments or comment_id > len(comments) or comments[comment_id - 1]["owner"] != token["username"]:
        raise HTTPException(status_code=404, detail="Comment not found or not authorized")
    comment = comments[comment_id - 1]
    if check_status_comment(comment_update.content) == "Active":
        comment.update(comment_update.dict(exclude_unset=True))
        return comment
    else:
        raise HTTPException(status_code=403, detail="Comment blocked due to inappropriate language.")

@app.delete("/posts/{post_id}/comments/{comment_id}")
async def delete_comment(post_id: int, comment_id: int, token: str = Depends(get_current_user)):
    comments = fake_comments_db.get(post_id)
    if not comments or comment_id > len(comments) or comments[comment_id - 1]["owner"] != token["username"]:
        raise HTTPException(status_code=404, detail="Comment not found or not authorized")
    i = 0
    while i < len(comments):
        if comments[i].get("id") == str(post_id):
            del comments[i]
        else:
            i += 1
    return {"detail": "Comment deleted"}

@app.get("/api/comments-daily-breakdown", response_model=List[DailyCommentBreakdown])
async def comments_daily_breakdown(
    date_from: str = Query(..., description="Start date in YYYY-MM-DD format"),
    date_to: str = Query(..., description="End date in YYYY-MM-DD format"),
):
    try:
        start_date = datetime.strptime(date_from, "%Y-%m-%d")
        end_date = datetime.strptime(date_to, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date.")

    date_counts = {}

    for post_id, comments in fake_comments_db.items():
        for comment in comments:
            comment_date = comment["created_at"].date()
            if start_date.date() <= comment_date <= end_date.date():
                date_str = comment_date.isoformat()
                if date_str not in date_counts:
                    date_counts[date_str] = {"created_count": 0, "blocked_count": 0}
                if comment["status"] == COMMENT_STATUS_ACTIVE:
                    date_counts[date_str]["created_count"] += 1
                elif comment["status"] == COMMENT_STATUS_BLOCKED:
                    date_counts[date_str]["blocked_count"] += 1

    response_data = [
        DailyCommentBreakdown(date=date, created_count=data["created_count"], blocked_count=data["blocked_count"])
        for date, data in sorted(date_counts.items())
    ]

    return response_data
