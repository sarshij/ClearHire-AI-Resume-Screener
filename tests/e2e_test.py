"""
Complete End-to-End API Test Suite for ClearHire Resume Screener
Runs against live server at http://127.0.0.1:8000
"""
import urllib.request
import urllib.parse
import json
import http.cookiejar
import io
import sys

BASE = 'http://127.0.0.1:8000'
results = []


def make_opener():
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def record(name, status, detail):
    results.append((name, status, str(detail)))


def post_form(opener, url, fields):
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(BASE + url, data=data, method='POST')
    return opener.open(req)


# ---------------------------------------------------------------------------
# TEST 1: Health check
# ---------------------------------------------------------------------------
try:
    opener = make_opener()
    r = opener.open(BASE + '/health')
    body = json.loads(r.read().decode())
    model_ok = body.get('model_loaded', False)
    record('TEST 01 - /health endpoint', 'PASS', f"status={body.get('status')}, model_loaded={model_ok}")
except Exception as e:
    record('TEST 01 - /health endpoint', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 2: Root / redirects to /login when unauthenticated
# ---------------------------------------------------------------------------
try:
    opener = make_opener()
    r = opener.open(BASE + '/')
    url = r.geturl()
    status = 'PASS' if 'login' in url else 'FAIL'
    record('TEST 02 - / unauthenticated redirect', status, f'Landed at: {url}')
except Exception as e:
    record('TEST 02 - / unauthenticated redirect', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 3: /batch redirects to /login
# ---------------------------------------------------------------------------
try:
    opener = make_opener()
    r = opener.open(BASE + '/batch')
    url = r.geturl()
    status = 'PASS' if 'login' in url else 'FAIL'
    record('TEST 03 - /batch unauthenticated redirect', status, f'Landed at: {url}')
except Exception as e:
    record('TEST 03 - /batch unauthenticated redirect', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 4: /analytics redirects to /login
# ---------------------------------------------------------------------------
try:
    opener = make_opener()
    r = opener.open(BASE + '/analytics')
    url = r.geturl()
    status = 'PASS' if 'login' in url else 'FAIL'
    record('TEST 04 - /analytics unauthenticated redirect', status, f'Landed at: {url}')
except Exception as e:
    record('TEST 04 - /analytics unauthenticated redirect', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 5: /user/upload redirects to /login
# ---------------------------------------------------------------------------
try:
    opener = make_opener()
    r = opener.open(BASE + '/user/upload')
    url = r.geturl()
    status = 'PASS' if 'login' in url else 'FAIL'
    record('TEST 05 - /user/upload unauthenticated redirect', status, f'Landed at: {url}')
except Exception as e:
    record('TEST 05 - /user/upload unauthenticated redirect', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 6: Invalid login is rejected
# ---------------------------------------------------------------------------
try:
    opener = make_opener()
    r = post_form(opener, '/login', {'username': 'hacker', 'password': 'wrongpass', 'role': 'hr'})
    body = r.read().decode()
    has_error = 'Invalid' in body or 'invalid' in body or 'error' in body.lower()
    status = 'PASS' if has_error else 'FAIL'
    record('TEST 06 - Invalid login rejected', status, 'Error message shown' if has_error else 'BUG: No error shown, might be logged in!')
except Exception as e:
    record('TEST 06 - Invalid login rejected', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 7: Valid HR login lands on /
# ---------------------------------------------------------------------------
hr_opener = make_opener()
try:
    r = post_form(hr_opener, '/login', {'username': 'admin', 'password': 'hr2026', 'role': 'hr'})
    url = r.geturl()
    status = 'PASS' if url.rstrip('/') == BASE else 'PARTIAL'
    record('TEST 07 - Valid HR login', status, f'Landed at: {url}')
except Exception as e:
    record('TEST 07 - Valid HR login', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 8: HR can access / after login
# ---------------------------------------------------------------------------
try:
    r = hr_opener.open(BASE + '/')
    url = r.geturl()
    body = r.read().decode()
    # Should NOT be redirected to login anymore
    is_dashboard = 'login' not in url and ('Resume' in body or 'ClearHire' in body or 'dashboard' in body.lower() or 'upload' in body.lower())
    status = 'PASS' if is_dashboard else 'FAIL'
    record('TEST 08 - HR dashboard accessible after login', status, f'URL: {url}')
except Exception as e:
    record('TEST 08 - HR dashboard accessible after login', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 9: Model info API
# ---------------------------------------------------------------------------
try:
    r = hr_opener.open(BASE + '/api/model/info')
    body = json.loads(r.read().decode())
    acc = body.get('test_accuracy', 0)
    f1 = body.get('test_f1', 0)
    feat_count = len(body.get('feature_names', []))
    record('TEST 09 - /api/model/info', 'PASS', f'Accuracy={acc}, F1={f1}, Features={feat_count}')
except Exception as e:
    record('TEST 09 - /api/model/info', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 10: History API returns records
# ---------------------------------------------------------------------------
try:
    r = hr_opener.open(BASE + '/api/history?limit=10')
    body = json.loads(r.read().decode())
    count = len(body.get('history', []))
    record('TEST 10 - /api/history', 'PASS', f'{count} records in DB history')
except Exception as e:
    record('TEST 10 - /api/history', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 11: Export CSV
# ---------------------------------------------------------------------------
try:
    r = hr_opener.open(BASE + '/api/export?format=csv')
    content_type = r.headers.get('Content-Type', '')
    body = r.read().decode()
    has_header = 'id' in body and 'filename' in body
    status = 'PASS' if has_header else 'FAIL'
    record('TEST 11 - Export CSV', status, f'Content-Type={content_type}, Has CSV header={has_header}')
except Exception as e:
    record('TEST 11 - Export CSV', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 12: Export JSON
# ---------------------------------------------------------------------------
try:
    r = hr_opener.open(BASE + '/api/export?format=json')
    body = json.loads(r.read().decode())
    count = len(body.get('data', []))
    record('TEST 12 - Export JSON', 'PASS', f'{count} records in JSON export')
except Exception as e:
    record('TEST 12 - Export JSON', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 13: Upload resume with EMPTY job description (should return 400)
# ---------------------------------------------------------------------------
try:
    boundary = 'boundary12345'
    resume_content = b'John Doe\nSoftware Engineer\nPython, FastAPI, PostgreSQL'
    body_parts = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="resume"; filename="test_resume.txt"\r\nContent-Type: text/plain\r\n\r\n'.encode()
        + resume_content
        + f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="job_title"\r\n\r\n\r\n'.encode()
        + f'--{boundary}\r\nContent-Disposition: form-data; name="job_description"\r\n\r\n\r\n'.encode()
        + f'--{boundary}--\r\n'.encode()
    )
    req = urllib.request.Request(
        BASE + '/api/predict',
        data=body_parts,
        method='POST',
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )
    try:
        r = hr_opener.open(req)
        resp_body = r.read().decode()
        record('TEST 13 - Predict with empty JD', 'FAIL', f'BUG: Should have returned 400, got 200. Body: {resp_body[:100]}')
    except urllib.error.HTTPError as http_err:
        if http_err.code == 400:
            record('TEST 13 - Predict with empty JD', 'PASS', f'Correctly returned HTTP 400: {http_err.read().decode()[:80]}')
        else:
            record('TEST 13 - Predict with empty JD', 'FAIL', f'Expected 400, got {http_err.code}')
except Exception as e:
    record('TEST 13 - Predict with empty JD', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 14: Upload non-resume file (plain text that is NOT a resume)
# ---------------------------------------------------------------------------
try:
    boundary = 'boundary99999'
    junk_content = b'Chapter 1: Introduction\nThis research paper explores the methodology of...\nTable of contents, Figure 1, Abstract, Hypothesis'
    jd_content = b'Python developer with FastAPI experience'
    body_parts = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="resume"; filename="paper.txt"\r\nContent-Type: text/plain\r\n\r\n'.encode()
        + junk_content
        + f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="job_title"\r\n\r\nSoftware Engineer\r\n'.encode()
        + f'--{boundary}\r\nContent-Disposition: form-data; name="job_description"\r\n\r\n'.encode()
        + jd_content
        + f'\r\n--{boundary}--\r\n'.encode()
    )
    req = urllib.request.Request(
        BASE + '/api/predict',
        data=body_parts,
        method='POST',
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )
    r = hr_opener.open(req)
    body = json.loads(r.read().decode())
    classification = body.get('classification', {}).get('classification', '')
    record('TEST 14 - Non-resume file detection', 
           'PASS' if classification == 'Not a Resume' else 'PARTIAL',
           f'Classification: {classification}')
except Exception as e:
    record('TEST 14 - Non-resume file detection', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 15: Full single resume analysis (real resume content)
# ---------------------------------------------------------------------------
try:
    boundary = 'boundary77777'
    resume_content = b"""Jane Smith
jane.smith@email.com | +1 (555) 234-5678 | github.com/janesmith | linkedin.com/in/janesmith

EXPERIENCE
Senior Software Engineer | TechCorp Inc | 2020 - Present
- Developed RESTful APIs using FastAPI and Python
- Designed PostgreSQL database schemas and optimized queries
- Deployed applications using Docker and AWS
- Led a team of 4 engineers on ML pipeline development

Junior Developer | StartupXYZ Ltd | 2018 - 2020
- Built web applications with Python and Flask
- Integrated third-party APIs and payment gateways

EDUCATION
Bachelor of Science in Computer Science | State University | 2018
GPA: 3.8/4.0

SKILLS
Python, FastAPI, Flask, PostgreSQL, MySQL, Docker, AWS, Git, REST APIs,
Machine Learning, scikit-learn, pandas, TensorFlow, Linux, CI/CD

CERTIFICATIONS
AWS Certified Solutions Architect
"""
    jd_content = b'We need a Python developer with FastAPI, PostgreSQL, Docker, REST APIs, and cloud experience (AWS). ML knowledge is a plus.'
    body_parts = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="resume"; filename="jane_smith.txt"\r\nContent-Type: text/plain\r\n\r\n'.encode()
        + resume_content
        + f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="job_title"\r\n\r\nSenior Software Engineer\r\n'.encode()
        + f'--{boundary}\r\nContent-Disposition: form-data; name="job_description"\r\n\r\n'.encode()
        + jd_content
        + f'\r\n--{boundary}--\r\n'.encode()
    )
    req = urllib.request.Request(
        BASE + '/api/predict',
        data=body_parts,
        method='POST',
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )
    r = hr_opener.open(req)
    body = json.loads(r.read().decode())
    scores = body.get('scores', {})
    classification = body.get('classification', {})
    record('TEST 15 - Full resume analysis', 'PASS',
           f"Classification={classification.get('classification')}, "
           f"MatchScore={scores.get('final_match_score')}, "
           f"SemanticSim={scores.get('semantic_similarity')}, "
           f"SkillOverlap={scores.get('skill_overlap_score')}")
except Exception as e:
    record('TEST 15 - Full resume analysis', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 16: Register with too-short username
# ---------------------------------------------------------------------------
try:
    opener = make_opener()
    r = post_form(opener, '/register', {'username': 'ab', 'password': 'pass123', 'confirm_password': 'pass123', 'role': 'user'})
    body = r.read().decode()
    has_error = 'least 3' in body or 'Username must' in body
    record('TEST 16 - Register short username blocked', 'PASS' if has_error else 'FAIL',
           'Validation error shown' if has_error else 'BUG: No error, was allowed!')
except Exception as e:
    record('TEST 16 - Register short username blocked', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 17: Register with short password
# ---------------------------------------------------------------------------
try:
    opener = make_opener()
    r = post_form(opener, '/register', {'username': 'validuser', 'password': 'abc', 'confirm_password': 'abc', 'role': 'user'})
    body = r.read().decode()
    has_error = 'least 6' in body or 'Password must' in body
    record('TEST 17 - Register short password blocked', 'PASS' if has_error else 'FAIL',
           'Validation error shown' if has_error else 'BUG: No error, was allowed!')
except Exception as e:
    record('TEST 17 - Register short password blocked', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 18: Register with mismatched passwords
# ---------------------------------------------------------------------------
try:
    opener = make_opener()
    r = post_form(opener, '/register', {'username': 'validuser', 'password': 'pass123', 'confirm_password': 'pass999', 'role': 'user'})
    body = r.read().decode()
    has_error = 'not match' in body.lower() or 'Passwords' in body
    record('TEST 18 - Register password mismatch blocked', 'PASS' if has_error else 'FAIL',
           'Validation error shown' if has_error else 'BUG: No error, was allowed!')
except Exception as e:
    record('TEST 18 - Register password mismatch blocked', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 19: Register duplicate username
# ---------------------------------------------------------------------------
try:
    opener = make_opener()
    r = post_form(opener, '/register', {'username': 'admin', 'password': 'something123', 'confirm_password': 'something123', 'role': 'hr'})
    body = r.read().decode()
    has_error = 'already taken' in body or 'taken' in body.lower()
    record('TEST 19 - Register duplicate username blocked', 'PASS' if has_error else 'FAIL',
           'Duplicate blocked' if has_error else 'BUG: Duplicate allowed!')
except Exception as e:
    record('TEST 19 - Register duplicate username blocked', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 20: Valid new user registration
# ---------------------------------------------------------------------------
try:
    opener = make_opener()
    r = post_form(opener, '/register', {'username': 'testuser_audit_2026', 'password': 'testpass123', 'confirm_password': 'testpass123', 'role': 'user'})
    url = r.geturl()
    # Should redirect to /login?registered=1
    status = 'PASS' if 'login' in url and 'registered' in url else 'FAIL'
    record('TEST 20 - Valid new user registration', status, f'Redirected to: {url}')
except Exception as e:
    record('TEST 20 - Valid new user registration', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 21: New user can log in with their just-registered credentials
# ---------------------------------------------------------------------------
try:
    opener = make_opener()
    r = post_form(opener, '/login', {'username': 'testuser_audit_2026', 'password': 'testpass123', 'role': 'user'})
    url = r.geturl()
    status = 'PASS' if 'user/upload' in url else 'FAIL'
    record('TEST 21 - New user can login after register', status, f'Landed at: {url}')
except Exception as e:
    record('TEST 21 - New user can login after register', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 22: Logout clears session
# ---------------------------------------------------------------------------
try:
    r = hr_opener.open(BASE + '/logout')
    url = r.geturl()
    # After logout, accessing / should redirect to login
    r2 = hr_opener.open(BASE + '/')
    url2 = r2.geturl()
    status = 'PASS' if 'login' in url2 else 'FAIL'
    record('TEST 22 - Logout clears session', status, f'After logout, / redirected to: {url2}')
except Exception as e:
    record('TEST 22 - Logout clears session', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 23: Batch status with invalid job ID
# ---------------------------------------------------------------------------
try:
    opener = make_opener()
    try:
        r = opener.open(BASE + '/api/batch_status/nonexistent-job-id-12345')
        record('TEST 23 - Invalid batch job ID', 'FAIL', 'BUG: Should return 404 but returned 200')
    except urllib.error.HTTPError as he:
        status = 'PASS' if he.code == 404 else 'FAIL'
        record('TEST 23 - Invalid batch job ID returns 404', status, f'Got HTTP {he.code}')
except Exception as e:
    record('TEST 23 - Invalid batch job ID returns 404', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 24: /api/class_distribution endpoint
# ---------------------------------------------------------------------------
try:
    opener = make_opener()
    r = opener.open(BASE + '/api/class_distribution')
    body = json.loads(r.read().decode())
    dist = body.get('class_distribution', {})
    record('TEST 24 - Class distribution API', 'PASS', f'Distribution: {dist}')
except Exception as e:
    record('TEST 24 - Class distribution API', 'FAIL', e)

# ---------------------------------------------------------------------------
# TEST 25: /api/dataset/stats endpoint
# ---------------------------------------------------------------------------
try:
    opener = make_opener()
    r = opener.open(BASE + '/api/dataset/stats')
    body = json.loads(r.read().decode())
    n = body.get('total_samples', 0)
    record('TEST 25 - Dataset stats API', 'PASS', f'Total samples: {n}')
except Exception as e:
    record('TEST 25 - Dataset stats API', 'FAIL', e)

# ---------------------------------------------------------------------------
# PRINT RESULTS
# ---------------------------------------------------------------------------
print()
print('=' * 75)
print('  CLEARHIRE RESUME SCREENER - COMPLETE E2E TEST REPORT')
print('=' * 75)
pass_c = fail_c = partial_c = 0
for name, status, detail in results:
    icon = '[PASS]   ' if status == 'PASS' else '[FAIL]   ' if status == 'FAIL' else '[PARTIAL]'
    print(f'{icon} {name}')
    print(f'          Detail: {detail}')
    print()
    if status == 'PASS': pass_c += 1
    elif status == 'FAIL': fail_c += 1
    else: partial_c += 1

print('=' * 75)
print(f'SUMMARY: {pass_c} PASSED | {fail_c} FAILED | {partial_c} PARTIAL out of {len(results)} tests')
print('=' * 75)
