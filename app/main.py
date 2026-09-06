import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from .database import Base, SessionLocal, engine, get_db
from .models import LearningPath, Task, User, UserTask
from .security import hash_password, session_secret, verify_password
from .seed import seed_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)
    yield


app = FastAPI(title=os.getenv("APP_NAME", "LearnFlow AI"), lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=session_secret(), https_only=False)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def current_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    return db.get(User, user_id) if user_id else None


def render(request: Request, name: str, **context):
    context["user"] = context.get("user")
    return templates.TemplateResponse(request, name, context)


@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    paths = db.scalars(select(LearningPath)).all()
    return render(request, "home.html", paths=paths, user=user)


@app.get("/signup")
def signup_page(request: Request, db: Session = Depends(get_db)):
    return render(request, "signup.html", paths=db.scalars(select(LearningPath)).all(), user=current_user(request, db))


@app.post("/signup")
def signup(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), path_id: int = Form(...), db: Session = Depends(get_db)):
    if len(password) < 8:
        return RedirectResponse("/signup?error=Password+must+contain+at+least+8+characters", 303)
    email = email.lower().strip()
    if db.scalar(select(User).where(User.email == email)):
        return RedirectResponse("/signup?error=An+account+already+uses+this+email", 303)
    admin_email = os.getenv("ADMIN_EMAIL", "").lower().strip()
    user = User(
        name=name.strip(),
        email=email,
        password_hash=hash_password(password),
        selected_path_id=path_id,
        is_admin=(email == admin_email),
    )
    db.add(user)
    db.commit()
    request.session["user_id"] = user.id
    return RedirectResponse("/dashboard", 303)


@app.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    return render(request, "login.html", user=current_user(request, db))


@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == email.lower().strip()))
    if not user or not verify_password(password, user.password_hash):
        return RedirectResponse("/login?error=Invalid+email+or+password", 303)
    request.session["user_id"] = user.id
    return RedirectResponse("/dashboard", 303)


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", 303)


@app.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/login", 303)
    path = db.get(LearningPath, user.selected_path_id) if user.selected_path_id else None
    tasks = db.scalars(select(Task).where(Task.path_id == user.selected_path_id).order_by(Task.position)).all() if path else []
    progress = {item.task_id: item.status for item in db.scalars(select(UserTask).where(UserTask.user_id == user.id)).all()}
    completed = sum(status == "done" for status in progress.values())
    percent = round((completed / len(tasks)) * 100) if tasks else 0
    return render(request, "dashboard.html", user=user, path=path, tasks=tasks, progress=progress, percent=percent, completed=completed)


@app.post("/tasks/{task_id}")
def update_task(task_id: int, request: Request, status: str = Form(...), db: Session = Depends(get_db)):
    user = current_user(request, db)
    task = db.get(Task, task_id)
    if not user or not task or task.path_id != user.selected_path_id or status not in {"not_started", "in_progress", "done"}:
        raise HTTPException(400, "Invalid task update")
    entry = db.scalar(select(UserTask).where(UserTask.user_id == user.id, UserTask.task_id == task_id))
    if entry:
        entry.status = status
    else:
        db.add(UserTask(user_id=user.id, task_id=task_id, status=status))
    db.commit()
    return RedirectResponse("/dashboard", 303)


@app.get("/admin")
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user or not user.is_admin:
        raise HTTPException(403, "Administrator access required")
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    rows = []
    for fresher in users:
        total = db.scalar(select(func.count(Task.id)).where(Task.path_id == fresher.selected_path_id)) or 0
        done = db.scalar(select(func.count(UserTask.id)).where(UserTask.user_id == fresher.id, UserTask.status == "done")) or 0
        rows.append({"user": fresher, "percent": round(done * 100 / total) if total else 0})
    return render(request, "admin.html", user=user, rows=rows)
