"""
FastAPI Backend for Resume Screening & Authenticity Validation
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ── Load environment variables from .env file ────────────────────────────────
# This MUST be done before any other imports so that database.py and other
# modules can read POSTGRES_PASSWORD, DATABASE_URL, etc. from the .env file.
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import json, os, io, time
import pandas as pd
import numpy as np

# ── Auth Configuration ─────────────────────────────────────────────────────────
# Simple hardcoded credentials for this academic project.
# In production these would come from a database with hashed passwords.
USERS = {
    "admin":     {"password": "hr2026",    "role": "hr"},
    "applicant": {"password": "apply2026", "role": "user"},
}
import secrets
SESSION_SECRET = secrets.token_hex(32)

from app.logger import setup_logger
from app.utils.parser import parse_resume, is_resume_format  # BUG 9: import at top, not inside hot path
from app.utils.file_validator import validate_upload
from app.features.semantic import compute_semantic_similarity, compute_semantic_similarity_async
from app.features.skill_overlap import compute_skill_overlap, get_matched_skills, extract_skills
from app.features.experience import score_experience_relevance
from app.utils.nlp import extract_education_spacy, extract_job_titles_spacy
from app.features.experience_extraction import extract_years_experience, extract_graduation_year
from app.features.validation import compute_all_validation_features
from app.models.classifier import predict, get_model_info
from app.models.database import init_db, async_session, create_user, authenticate_user, _hash_password, User
from app.models.llm_detector import get_llm_detector  # BUG 9: import at top, not inside hot path

logger = setup_logger(__name__)
BASE = Path(__file__).resolve().parent.parent

# Set up Rate Limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    logger.info("Resume Screener API starting up...")
    
    # ── Database Initialization ─────────────────────────────────────────────
    await init_db()

    # ── Seed default admin + applicant accounts into DB ──────────────────────
    # This ensures the hardcoded demo credentials (admin/hr2026, applicant/apply2026)
    # also exist in the database, so the DB-backed auth path always works.
    try:
        from sqlalchemy import select
        async with async_session() as session:
            for username, info in USERS.items():
                result = await session.execute(
                    select(User).where(User.username == username)
                )
                if result.scalar_one_or_none() is None:
                    await create_user(session, username, info["password"], info["role"])
                    logger.info(f"Seeded default account: {username} ({info['role']})")
    except Exception as seed_err:
        logger.warning(f"Could not seed default users: {seed_err}")
    
    # ── Startup model pre-warming ─────────────────────────────────────────────
    from app.models.classifier import load_model
    load_model()
    # Pre-warm spaCy pipeline
    from app.utils.nlp import get_nlp_with_ruler, _ensure_patterns
    nlp = get_nlp_with_ruler()
    if nlp:
        _ensure_patterns(nlp)
        logger.info("spaCy pipeline pre-warmed successfully")
    # Pre-warm SBERT model
    from app.models.embedder import get_model as get_sbert_model
    get_sbert_model()
    logger.info("SBERT model pre-warmed successfully")

    # ── BUG 5: Start TTL cleanup task for batch_jobs to prevent memory leak ──
    async def _cleanup_batch_jobs():
        """Remove completed batch job entries older than 30 minutes to prevent memory leak."""
        BATCH_JOB_TTL_SECONDS = 1800  # 30 minutes
        while True:
            await asyncio.sleep(300)  # Run cleanup every 5 minutes
            now = time.time()
            expired = [
                job_id for job_id, job in list(batch_jobs.items())
                if job.get("status") == "completed" and (now - job.get("created_at", now)) > BATCH_JOB_TTL_SECONDS
            ]
            for job_id in expired:
                del batch_jobs[job_id]
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired batch job(s) from memory.")

    asyncio.create_task(_cleanup_batch_jobs())
    
    yield
    logger.info("Resume Screener API shutting down.")

app = FastAPI(title="Resume Screener API", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, max_age=3600)

templates = Jinja2Templates(directory=str(BASE / 'app' / 'templates'))
app.mount("/static", StaticFiles(directory=str(BASE / 'app' / 'static')), name="static")

class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration:.2f}s)")
        return response

app.add_middleware(RequestLogMiddleware)

# ── Auth Helpers ──────────────────────────────────────────────────────────────
def get_session_role(request: Request) -> str | None:
    """Return the role stored in the session, or None if not logged in."""
    return request.session.get("role")

def require_hr(request: Request):
    """Redirect to login if the session role is not 'hr'."""
    role = get_session_role(request)
    if role != "hr":
        return RedirectResponse(url="/login", status_code=303)
    return None

def require_user(request: Request):
    """Redirect to login if not logged in at all."""
    role = get_session_role(request)
    if role not in ("hr", "user"):
        return RedirectResponse(url="/login", status_code=303)
    return None

# ── Auth Routes ────────────────────────────────────────────────────────────────
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    # If already logged in redirect to the right dashboard
    role = get_session_role(request)
    if role == "hr":
        return RedirectResponse(url="/", status_code=303)
    if role == "user":
        return RedirectResponse(url="/user/upload", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("hr")
):
    """
    Authenticate against the PostgreSQL users table first.
    Falls back to the hardcoded USERS dict (for safety during dev/demo).
    """
    uname = username.strip().lower()

    # ── 1. Check database first (registered users) ────────────────────────────
    db_auth = False
    try:
        async with async_session() as session:
            db_auth = await authenticate_user(session, uname, password, role)
    except Exception as db_e:
        logger.warning(f"DB auth check failed, falling back to hardcoded: {db_e}")

    # ── 2. Fallback: hardcoded USERS dict (demo credentials) ─────────────────
    hardcoded = USERS.get(uname)
    hardcoded_ok = (
        hardcoded is not None
        and hardcoded["password"] == password
        and hardcoded["role"] == role
    )

    if db_auth or hardcoded_ok:
        request.session["username"] = uname
        request.session["role"] = role
        if role == "hr":
            return RedirectResponse(url="/", status_code=303)
        else:
            return RedirectResponse(url="/user/upload", status_code=303)

    # Auth failed — show error on the same page
    error = "Invalid username or password. Please check your credentials and selected role."
    return templates.TemplateResponse(
        request=request, name="login.html",
        context={"request": request, "error": error}
    )


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


# ── Registration Routes ──────────────────────────────────────────────────────────
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Show the registration page. Redirect to dashboard if already logged in."""
    role = get_session_role(request)
    if role == "hr":
        return RedirectResponse(url="/", status_code=303)
    if role == "user":
        return RedirectResponse(url="/user/upload", status_code=303)
    return templates.TemplateResponse(
        request=request, name="register.html",
        context={"request": request, "error": None, "success": None}
    )


@app.post("/register", response_class=HTMLResponse)
async def register_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    role: str = Form("user")
):
    """Handle registration form submission. Writes user to PostgreSQL."""
    uname = username.strip().lower()

    # ── Validation ────────────────────────────────────────────────────────────
    if len(uname) < 3:
        return templates.TemplateResponse(
            request=request, name="register.html",
            context={"request": request, "error": "Username must be at least 3 characters.", "success": None}
        )
    if len(password) < 6:
        return templates.TemplateResponse(
            request=request, name="register.html",
            context={"request": request, "error": "Password must be at least 6 characters.", "success": None}
        )
    if password != confirm_password:
        return templates.TemplateResponse(
            request=request, name="register.html",
            context={"request": request, "error": "Passwords do not match.", "success": None}
        )
    if role not in ("hr", "user"):
        role = "user"  # default to applicant if invalid role supplied

    # ── Create in DB ──────────────────────────────────────────────────────────
    try:
        async with async_session() as session:
            new_user = await create_user(session, uname, password, role)
        if new_user is None:
            return templates.TemplateResponse(
                request=request, name="register.html",
                context={"request": request, "error": f"Username '{uname}' is already taken. Please choose another.", "success": None}
            )
    except Exception as e:
        logger.error(f"Registration failed for '{uname}': {e}")
        return templates.TemplateResponse(
            request=request, name="register.html",
            context={"request": request, "error": "Registration failed due to a server error. Please try again.", "success": None}
        )

    logger.info(f"New user registered: {uname} ({role})")
    # Redirect to login with a success flag in query string
    return RedirectResponse(
        url=f"/login?registered=1&role={role}",
        status_code=303
    )


# ── Applicant Routes ───────────────────────────────────────────────────────────
@app.get("/user/upload", response_class=HTMLResponse)
async def user_upload_page(request: Request):
    redirect = require_user(request)
    if redirect:
        return redirect
    # HR users should use the HR dashboard
    if get_session_role(request) == "hr":
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request=request, name="user_upload.html", context={"request": request})

@app.post("/user/submit")
@limiter.limit("10/minute")
async def user_submit_resume(
    request: Request,
    resume: UploadFile = File(...)
):
    """End-user resume submission endpoint. Validates and saves the file only — no analytics returned."""
    redirect = require_user(request)
    if redirect:
        raise HTTPException(401, "Not authenticated")
    try:
        resume_bytes = await resume.read()
        validate_upload(resume_bytes, resume.filename or "resume.pdf")
        resume_text = parse_resume(resume_bytes, resume.filename or "resume.pdf")
        if not resume_text or len(resume_text.strip()) < 20:
            raise HTTPException(400, "Could not extract readable text from the resume")
        logger.info(f"[USER SUBMIT] {request.session.get('username')} uploaded {resume.filename}")
        # Optionally save to DB as a pending submission (no scoring fields)
        try:
            from app.models.database import async_session, ResumeAnalysis
            async with async_session() as session:
                db_record = ResumeAnalysis(
                    filename=resume.filename,
                    final_match_score=0.0,
                    ai_plausibility_score=0.0,
                    classification="Pending",
                    full_results={"status": "pending", "submitted_by": request.session.get("username")}
                )
                session.add(db_record)
                await session.commit()
        except Exception as db_e:
            logger.warning(f"Could not save user submission to DB: {db_e}")
        return {"status": "success", "message": "Resume submitted successfully."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User submit failed: {e}")
        raise HTTPException(500, "Submission failed. Please try again.")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    redirect = require_hr(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request})

@app.get("/batch", response_class=HTMLResponse)
async def batch_page(request: Request):
    redirect = require_hr(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(request=request, name="batch.html", context={"request": request})

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    redirect = require_hr(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(request=request, name="analytics.html", context={"request": request})

@app.get("/health")
async def health():
    """
    Fix 8: Health endpoint for monitoring.
    """
    from app.models.classifier import _loaded_model
    return {
        "status": "ok", 
        "version": "2.0",
        "model_loaded": _loaded_model is not None
    }

@app.post("/api/predict")
@limiter.limit("25/minute")
async def predict_single(
    request: Request,
    resume: UploadFile = File(...),
    job_title: str = Form(""),
    job_description: str = Form(""),
    job_description_file: UploadFile = File(None)
):
    try:
        # Parse JD from file if provided
        if job_description_file and job_description_file.filename:
            jd_bytes = await job_description_file.read()
            if jd_bytes:
                validate_upload(jd_bytes, job_description_file.filename)
                job_description = parse_resume(jd_bytes, job_description_file.filename)

        # ── Fix 6: Input length sanitization ─────────────────────────────────
        job_title = job_title.strip()[:200]
        job_description = job_description.strip()[:3000]
        
        if not job_description:
            raise HTTPException(400, "Job description must be provided via text or file upload")

        resume_bytes = await resume.read()
        
        # ── Fix 2 & 3: File type and size validation ─────────────────────────
        validate_upload(resume_bytes, resume.filename or "resume.pdf")

        resume_text = parse_resume(resume_bytes, resume.filename or "resume.pdf")
        if not resume_text or len(resume_text.strip()) < 20:
            logger.warning(f"Too short or empty: {resume.filename} ({len(resume_text or '')} chars)")
            raise HTTPException(400, "Could not extract enough text from resume")

        logger.info(f"Predicting: {resume.filename} | JD: {len(job_description)} chars")
        years_exp = extract_years_experience(resume_text)
        grad_year = extract_graduation_year(resume_text)
        logger.debug(f"Extracted: {years_exp} years exp, graduation year {grad_year}")
        sem_sim = await compute_semantic_similarity_async(resume_text, job_description)
        skill_overlap = compute_skill_overlap(resume_text, job_description)
        exp_relevance = score_experience_relevance(resume_text, job_title or job_description)
        final_score = round(0.6 * sem_sim + 0.25 * skill_overlap + 0.15 * exp_relevance, 4)
        extracted_skills = list(extract_skills(resume_text))
        validation = compute_all_validation_features(
            resume_text, job_description,
            semantic_similarity=sem_sim,
            skill_overlap_score=skill_overlap,
            experience_relevance_score=exp_relevance,
            final_match_score=final_score,
            years_experience=years_exp,
            graduation_year=grad_year,
            extracted_skills=extracted_skills
        )
        # BUG 9: is_resume_format imported at top of file, not here
        if not is_resume_format(resume_text):
            classification = {
                'classification': 'Not a Resume',
                'confidence': 1.0,
                'prob_Authentic': 0.0,
                'prob_Suspicious': 0.0,
                'prob_Potentially Fake': 0.0
            }
        else:
            classification = predict([validation])[0]
        
        # Double check with LLM if Suspicious or Fake
        current_class = classification.get('classification', 'Unknown')
        if current_class in ['Suspicious', 'Potentially Fake']:
            # BUG 9: get_llm_detector imported at top of file, not here
            detector = get_llm_detector()
            verification = detector.verify_prediction(resume_text, job_description, current_class)
            if verification:
                classification['llm_verification'] = verification
                if verification.get('consensus') == 'Disagree':
                    classification['classification'] = 'Suspicious'

        skill_details = get_matched_skills(resume_text, job_description)

        # Generate a cleaner, anonymized summary without PII
        edu_list = list(extract_education_spacy(resume_text))
        edu_str = ", ".join([e.title() for e in edu_list[:3]]) + ("..." if len(edu_list) > 3 else "")
        if not edu_str: edu_str = "Not detected"

        job_list = list(extract_job_titles_spacy(resume_text))
        job_str = ", ".join([j.title() for j in job_list[:3]]) + ("..." if len(job_list) > 3 else "")
        if not job_str: job_str = "Not detected"

        skill_str = ", ".join(extracted_skills[:10]) + ("..." if len(extracted_skills) > 10 else "")
        
        summary_preview = (
            f"Experience: ~{years_exp} years\n"
            f"Past Roles: {job_str}\n"
            f"Education: {edu_str} (Class of {grad_year})\n\n"
            f"Top Skills: {skill_str}"
        )

        result_data = {
            "status": "success",
            "filename": resume.filename,
            "resume_preview": summary_preview,
            "scores": {
                "semantic_similarity": sem_sim,
                "skill_overlap_score": skill_overlap,
                "experience_relevance_score": exp_relevance,
                "final_match_score": final_score
            },
            "skills": skill_details,
            "validation": validation,
            "classification": classification
        }
        
        # Async save to DB
        try:
            from app.models.database import async_session, ResumeAnalysis
            async with async_session() as session:
                db_analysis = ResumeAnalysis(
                    filename=resume.filename,
                    final_match_score=final_score,
                    # BUG 6 FIX: ai_plausibility_score was removed as a feature;
                    # default to 0.5 as a neutral placeholder in the DB record
                    ai_plausibility_score=0.5,
                    classification=classification['classification'],
                    full_results=result_data
                )
                session.add(db_analysis)
                await session.commit()
        except Exception as db_e:
            logger.error(f"Failed to save to database: {db_e}")

        logger.info(f"Result: {resume.filename} -> {classification['classification']} ({classification['confidence']*100:.1f}%)")
        return result_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Predict failed for {resume.filename}: {e}")
        raise HTTPException(500, str(e))

# ── Batch job state store ────────────────────────────────────────────────────
# Dictionary to store batch job statuses in memory.
# BUG 5 FIX: TTL cleanup runs every 5 minutes in lifespan to prevent memory leak.
# Each entry has a 'created_at' timestamp for TTL enforcement.
batch_jobs = {}

@app.post("/api/predict_batch")
@limiter.limit("100/minute")
async def predict_batch(
    request: Request,
    background_tasks: BackgroundTasks,
    resumes: list[UploadFile] = File(...),
    job_title: str = Form(""),
    job_description: str = Form(""),
    job_description_file: UploadFile = File(None)
):
    import asyncio
    import uuid
    
    # Parse JD from file if provided
    if job_description_file and job_description_file.filename:
        jd_bytes = await job_description_file.read()
        if jd_bytes:
            validate_upload(jd_bytes, job_description_file.filename)
            job_description = parse_resume(jd_bytes, job_description_file.filename)

    job_title = job_title.strip()[:200]
    job_description = job_description.strip()[:3000]
    
    if not job_description:
        raise HTTPException(400, "Job description must be provided via text or file upload")

    job_id = str(uuid.uuid4())
    batch_jobs[job_id] = {
        "status": "processing",
        "total": len(resumes),
        "completed": 0,
        "results": [],
        "errors": [],
        "created_at": time.time()  # BUG 5 FIX: timestamp for TTL-based cleanup
    }
    
    # We must read the file contents now because UploadFile stream closes after the request ends
    resume_data = []
    for resume in resumes:
        try:
            content = await resume.read()
            resume_data.append((resume.filename, content))
        except Exception as e:
            batch_jobs[job_id]["errors"].append(f"Failed to read {resume.filename}: {e}")
            batch_jobs[job_id]["completed"] += 1

    logger.info(f"Batch predict started: {len(resume_data)} files, Job ID: {job_id}")
    
    async def _process_single_inner(filename: str, resume_bytes: bytes,
                                     job_id: str, job_description: str, job_title: str) -> dict:
        """
        Core processing logic for a single resume in a batch.
        Extracted so it can be wrapped by asyncio.wait_for for timeout support.
        """
        try:
            validate_upload(resume_bytes, filename or "resume.pdf")
        except HTTPException as ve:
            return {"filename": filename, "error": ve.detail}

        # OPTIMIZATION: parse_resume is CPU-heavy and may trigger blocking OCR. 
        # We MUST run it in a thread pool to avoid stalling the async event loop.
        import asyncio
        resume_text = await asyncio.to_thread(parse_resume, resume_bytes, filename or "resume.pdf")
        if not resume_text or len(resume_text.strip()) < 20:
            return {"filename": filename, "error": "Could not extract enough text from file"}

        years_exp = extract_years_experience(resume_text)
        grad_year = extract_graduation_year(resume_text)
        sem_sim = await compute_semantic_similarity_async(resume_text, job_description)
        skill_overlap = compute_skill_overlap(resume_text, job_description)
        exp_relevance = score_experience_relevance(resume_text, job_title or job_description)
        final_score = round(0.6 * sem_sim + 0.25 * skill_overlap + 0.15 * exp_relevance, 4)
        extracted_skills = list(extract_skills(resume_text))
        validation = compute_all_validation_features(
            resume_text, job_description,
            semantic_similarity=sem_sim,
            skill_overlap_score=skill_overlap,
            experience_relevance_score=exp_relevance,
            final_match_score=final_score,
            years_experience=years_exp,
            graduation_year=grad_year,
            extracted_skills=extracted_skills
        )

        # BUG 9: is_resume_format imported at top of file
        if not is_resume_format(resume_text):
            classification = {
                'classification': 'Not a Resume',
                'confidence': 1.0,
                'prob_Authentic': 0.0,
                'prob_Suspicious': 0.0,
                'prob_Potentially Fake': 0.0
            }
        else:
            classification = predict([validation])[0]

        # Double check with LLM if Suspicious or Fake
        current_class = classification.get('classification', 'Unknown')
        if current_class in ['Suspicious', 'Potentially Fake']:
            # BUG 9: get_llm_detector imported at top of file
            detector = get_llm_detector()
            verification = detector.verify_prediction(resume_text, job_description, current_class)
            if verification:
                classification['llm_verification'] = verification
                if verification.get('consensus') == 'Disagree':
                    classification['classification'] = 'Suspicious'

        skill_details = get_matched_skills(resume_text, job_description)
        edu_list = list(extract_education_spacy(resume_text))
        edu_str = ", ".join([e.title() for e in edu_list[:3]]) + ("..." if len(edu_list) > 3 else "")
        if not edu_str: edu_str = "Not detected"

        job_list = list(extract_job_titles_spacy(resume_text))
        job_str = ", ".join([j.title() for j in job_list[:3]]) + ("..." if len(job_list) > 3 else "")
        if not job_str: job_str = "Not detected"

        skill_str = ", ".join(extracted_skills[:10]) + ("..." if len(extracted_skills) > 10 else "")
        summary_preview = (
            f"Experience: ~{years_exp} years\n"
            f"Past Roles: {job_str}\n"
            f"Education: {edu_str} (Class of {grad_year})\n\n"
            f"Top Skills: {skill_str}"
        )

        return {
            "status": "success",
            "filename": filename,
            "resume_preview": summary_preview,
            "scores": {
                "semantic_similarity": sem_sim,
                "skill_overlap_score": skill_overlap,
                "experience_relevance_score": exp_relevance,
                "final_match_score": final_score
            },
            "skills": skill_details,
            "validation": validation,
            "classification": classification["classification"],
            "classification_details": classification,
            "confidence": classification["confidence"],
            "final_match_score": final_score,
            "semantic_similarity": sem_sim,
            "skill_overlap_score": skill_overlap
        }

    # Function to process in background
    async def process_batch_background(job_id: str, resume_data: list, job_title: str, job_description: str):

        semaphore = asyncio.Semaphore(4) # Limit concurrency
        
        async def process_single(filename: str, resume_bytes: bytes) -> dict:
            """Process a single resume file within the batch, with a hard timeout."""
            async with semaphore:
                try:
                    # BUG 11 FIX: Wrap the entire processing in a 60s timeout so one
                    # corrupt/slow file cannot stall the entire batch.
                    return await asyncio.wait_for(
                        _process_single_inner(filename, resume_bytes, job_id, job_description, job_title),
                        timeout=60.0
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"Batch: timeout processing {filename}")
                    return {"filename": filename, "error": "Processing timed out (file may be too large or corrupt)"}
                finally:
                    batch_jobs[job_id]["completed"] += 1

        tasks = [process_single(fname, content) for fname, content in resume_data]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # BUG 4 FIX: Convert any unhandled exceptions from gather to error dicts
        clean_results = []
        for fname_content, result in zip(resume_data, results):
            if isinstance(result, Exception):
                clean_results.append({"filename": fname_content[0], "error": str(result)})
            else:
                clean_results.append(result)

        sorted_results = sorted(clean_results, key=lambda x: (
            0 if x.get("classification") == "Authentic"
            else 1 if x.get("classification") == "Suspicious"
            else 2 if x.get("classification") == "Potentially Fake"
            else 3 if x.get("classification") == "Not a Resume"
            else 4,  # errors go last
            -x.get("final_match_score", 0)
        ))
        batch_jobs[job_id]["results"] = sorted_results
        batch_jobs[job_id]["status"] = "completed"
        logger.info(f"Batch {job_id} complete: {len(sorted_results)} files processed")

    if background_tasks:
        background_tasks.add_task(process_batch_background, job_id, resume_data, job_title, job_description)
    else:
        # Fallback if background_tasks is somehow None (e.g. testing)
        asyncio.create_task(process_batch_background(job_id, resume_data, job_title, job_description))

    return {"status": "processing", "job_id": job_id, "message": "Batch processing started."}

@app.get("/api/batch_status/{job_id}")
async def batch_status(job_id: str):
    if job_id not in batch_jobs:
        raise HTTPException(404, "Job ID not found")
    
    job = batch_jobs[job_id]
    return {
        "status": job["status"],
        "total": job["total"],
        "completed": job["completed"],
        "progress": round((job["completed"] / job["total"]) * 100) if job["total"] > 0 else 0,
        "results": job["results"] if job["status"] == "completed" else []
    }

@app.get("/api/history")
async def get_history(limit: int = 50, offset: int = 0):
    try:
        from app.models.database import async_session, ResumeAnalysis
        from sqlalchemy import select
        async with async_session() as session:
            stmt = select(ResumeAnalysis).order_by(ResumeAnalysis.created_at.desc()).limit(limit).offset(offset)
            result = await session.execute(stmt)
            records = result.scalars().all()
            
            history = []
            for r in records:
                history.append({
                    "id": r.id,
                    "filename": r.filename,
                    "candidate_name": r.candidate_name,
                    "classification": r.classification,
                    "final_match_score": r.final_match_score,
                    "ai_plausibility_score": r.ai_plausibility_score,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                })
            return {"status": "success", "history": history}
    except Exception as e:
        logger.error(f"Failed to fetch history: {e}")
        raise HTTPException(500, "Could not fetch history")

@app.get("/api/export")
async def export_data(format: str = 'csv'):
    try:
        from app.models.database import async_session, ResumeAnalysis
        from sqlalchemy import select
        async with async_session() as session:
            stmt = select(ResumeAnalysis).order_by(ResumeAnalysis.created_at.desc())
            result = await session.execute(stmt)
            records = result.scalars().all()
            
            data = []
            for r in records:
                data.append({
                    "id": r.id,
                    "filename": r.filename,
                    "classification": r.classification,
                    "final_match_score": r.final_match_score,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                })
                
            if format == 'json':
                return JSONResponse(content={"status": "success", "data": data})
            else:
                # Basic CSV generation
                import csv, io
                from fastapi.responses import StreamingResponse
                
                stream = io.StringIO()
                writer = csv.DictWriter(stream, fieldnames=["id", "filename", "classification", "final_match_score", "created_at"])
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
                    
                response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
                response.headers["Content-Disposition"] = "attachment; filename=resume_analysis_export.csv"
                return response
    except Exception as e:
        logger.error(f"Failed to export data: {e}")
        raise HTTPException(500, "Could not export data")

@app.get("/api/model/info")
async def model_info():
    try:
        info = get_model_info()
        return {"status": "success", **info}
    except Exception as e:
        logger.error(f"Model info failed: {e}")
        raise HTTPException(500, str(e))

@app.get("/api/class_distribution")
async def class_distribution():
    df_path = BASE / 'data' / 'processed' / 'combined_dataset.csv'
    if not df_path.exists():
        raise HTTPException(404, "Dataset not found")
    df = pd.read_csv(df_path)
    dist = df['classification'].value_counts().to_dict()
    risk = df['risk_level'].value_counts().to_dict()
    return {"status": "success", "class_distribution": dist, "risk_distribution": risk}

@app.get("/api/dataset/stats")
async def dataset_stats():
    df_path = BASE / 'data' / 'processed' / 'combined_dataset.csv'
    if not df_path.exists():
        raise HTTPException(404, "Dataset not found")
    df = pd.read_csv(df_path)
    # BUG 7 FIX: Updated feature list to match the current 17-feature model
    # (has_previous_job and ai_plausibility_score were removed from the model)
    feature_cols = [
        'semantic_similarity', 'skill_overlap_score', 'experience_relevance_score',
        'final_match_score', 'overlapping_jobs', 'promotion_speed',
        'experience_graduation_gap', 'skill_density', 'achievement_count',
        'generic_phrase_score', 'gap_years', 'keyword_stuffing_score',
        'years_experience', 'num_certifications', 'num_skills',
        'education_level_encoded', 'skill_experience_alignment',
    ]
    stats = {}
    for col in feature_cols:
        if col in df.columns:
            stats[col] = {
                'mean': round(float(df[col].mean()), 4),
                'std': round(float(df[col].std()), 4),
                'min': round(float(df[col].min()), 4),
                'max': round(float(df[col].max()), 4)
            }
    return {"status": "success", "total_samples": len(df), "feature_stats": stats}


@app.get("/api/export/analytics")
async def export_analytics():
    """
    Export model performance metrics as a downloadable CSV file.
    Includes accuracy, F1-score, and the feature importance values from
    the trained XGBoost model.
    Called by the 'Export Metrics CSV' button on the analytics page.
    """
    try:
        info = get_model_info()

        # get_model_info() returns flat keys (not nested under 'metrics')
        # Build CSV content in two clear sections
        lines = [
            "# ClearHire – Model Performance Export",
            f"# Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## SECTION 1: Model Performance Metrics",
            "Metric,Value",
            f"Accuracy,{info.get('test_accuracy', 'N/A')}",
            f"F1-Score (Weighted),{info.get('test_f1', 'N/A')}",
            f"Precision,{info.get('test_precision', 'N/A')}",
            f"Recall,{info.get('test_recall', 'N/A')}",
        ]

        # Per-class metrics if present (some model versions include these)
        per_class = info.get("per_class_metrics", info.get("per_class", {}))
        if isinstance(per_class, dict) and per_class:
            lines += ["", "## SECTION 1b: Per-Class Metrics", "Class,Precision,Recall,F1"]
            for cls_name, cls_m in per_class.items():
                lines.append(
                    f"{cls_name},{cls_m.get('precision','')},{cls_m.get('recall','')},{cls_m.get('f1','')}"
                )

        # Feature importance — can be a dict {name: score} or list [[name, score], ...]
        feature_importance = info.get("feature_importance", [])
        if feature_importance:
            lines += ["", "## SECTION 2: Feature Importance", "Feature,Importance"]
            if isinstance(feature_importance, dict):
                # Dict format: {feature_name: importance_score}
                for feat, imp in sorted(feature_importance.items(), key=lambda x: -float(x[1])):
                    lines.append(f"{feat},{float(imp):.6f}")
            elif isinstance(feature_importance, list):
                # List format: [[name, score], ...] or [{"feature":..., "importance":...}, ...]
                for entry in feature_importance:
                    if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                        lines.append(f"{entry[0]},{float(entry[1]):.6f}")
                    elif isinstance(entry, dict):
                        feat = entry.get("feature", entry.get("name", ""))
                        imp  = entry.get("importance", entry.get("score", 0))
                        lines.append(f"{feat},{float(imp):.6f}")

        csv_data = "\n".join(lines)
        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=clearhire_analytics.csv"}
        )
    except Exception as e:
        logger.error(f"Analytics export failed: {e}")
        raise HTTPException(500, f"Export failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
