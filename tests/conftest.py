import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest

SAMPLE_RESUME = """John Doe
Software Engineer | Python, Java, AWS
Email: john@example.com | Phone: +1-555-0100

SUMMARY
Experienced software engineer with 5+ years of experience in Python, Java, and cloud computing.
Proven track record of delivering scalable microservices.

EXPERIENCE
Senior Software Engineer, TechCorp Inc., San Francisco, CA
2020 - Present
- Led a team of 10 engineers to build a cloud-native platform
- Reduced deployment time by 40% through CI/CD automation
- Architected microservices handling 1M+ daily requests
- mentored 5 junior developers

Software Engineer, StartupXYZ, Remote
2018 - 2020
- Built RESTful APIs using Python and Django
- Migrated legacy systems to AWS cloud infrastructure
- Increased test coverage from 60% to 95%

EDUCATION
Bachelor of Science in Computer Science
University of California, Berkeley
2014 - 2018
GPA: 3.7

SKILLS
Python, Java, JavaScript, Docker, Kubernetes, AWS, PostgreSQL,
Redis, TensorFlow, scikit-learn, CI/CD, Git, Agile, Scrum
"""

SAMPLE_JD = """We are looking for a Senior Software Engineer with strong experience in Python,
cloud computing (AWS preferred), and microservices architecture.
Experience with Docker, Kubernetes, and CI/CD pipelines is a plus.
The ideal candidate has led engineering teams and delivered scalable solutions."""

SHORT_RESUME = "Short text without enough detail for analysis."

EMPTY_RESUME = ""

GENERIC_PHRASE_RESUME = """Highly motivated results-driven go-getter with proven track record of excellence.
Think outside the box team player. Synergized cross-platform solutions.
Results-oriented professional with demonstrated success in leveraging core competencies.
Dynamic self-starter with excellent communication skills."""


@pytest.fixture
def sample_resume():
    return SAMPLE_RESUME


@pytest.fixture
def sample_jd():
    return SAMPLE_JD


@pytest.fixture
def short_resume():
    return SHORT_RESUME


@pytest.fixture
def empty_resume():
    return EMPTY_RESUME


@pytest.fixture
def generic_resume():
    return GENERIC_PHRASE_RESUME


# ── HTTP Client Fixtures ─────────────────────────────────────────────────────
# These fixtures provide pre-configured TestClient instances so individual
# tests don't need to manage session setup themselves.

from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def client():
    """
    Unauthenticated test client.
    Use for login page tests and routes that don't require auth.
    """
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture(scope="session")
def auth_client():
    """
    Pre-authenticated HR (admin) test client.
    Logs in once per test session; session cookie is reused for all requests.
    Required for any route behind the require_auth() middleware.
    """
    with TestClient(app, raise_server_exceptions=True) as c:
        resp = c.post("/login", data={"username": "admin", "password": "hr2026"})
        # Login should redirect or return 200
        assert resp.status_code in (200, 302, 303), (
            f"auth_client login failed: {resp.status_code} — {resp.text[:300]}"
        )
        yield c
