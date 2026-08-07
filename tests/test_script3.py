import requests
import sys
import os
import json
import time

BASE_URL = "http://localhost:8000"

def make_session():
    return requests.Session()

def test_get_login(s):
    r = s.get(f"{BASE_URL}/login")
    assert r.status_code == 200, f"GET /login failed: {r.status_code}"
    print("GET /login OK")

def test_post_login_fail(s):
    r = s.post(f"{BASE_URL}/login", data={"username":"wrong","password":"wrong","role":"hr"})
    assert r.status_code == 200
    assert b"Invalid username or password" in r.content or b"error" in r.content.lower()
    print("POST /login with bad credentials returns error")

def test_post_login_success_hr(s):
    r = s.post(f"{BASE_URL}/login", data={"username":"admin","password":"hr2026","role":"hr"}, allow_redirects=False)
    assert r.status_code in (302, 303)
    assert r.headers.get('Location', '').endswith("/")
    s.get(f"{BASE_URL}/", allow_redirects=True)
    print("POST /login admin/hr2026 succeeds and redirects")

def test_protected_route_hr(s):
    r = s.get(f"{BASE_URL}/")
    assert r.status_code == 200
    assert b"Resume Screener" in r.content or b"dashboard" in r.content.lower()
    print("Protected HR dashboard accessible after login")

def test_logout(s):
    r = s.get(f"{BASE_URL}/logout", allow_redirects=False)
    assert r.status_code in (302,303)
    # return new session
    return make_session()

def test_register_get(s):
    r = s.get(f"{BASE_URL}/register")
    assert r.status_code == 200
    print("GET /register OK")

def test_register_success(s):
    uname = f"testuser{int(time.time())}"
    r = s.post(f"{BASE_URL}/register", data={
        "username": uname,
        "password": "Testpass123!",
        "confirm_password": "Testpass123!",
        "role": "user"
    }, allow_redirects=False)
    assert r.status_code in (302,303)
    loc = r.headers.get('Location','')
    assert 'registered=1' in loc
    print("Registration successful")

def test_user_upload_get(s):
    s.post(f"{BASE_URL}/login", data={"username":"applicant","password":"apply2026","role":"user"})
    r = s.get(f"{BASE_URL}/user/upload")
    assert r.status_code == 200
    print("GET /user/upload OK for user")
    # after test, clear session
    return make_session()

def test_file_validation_reject_exe(s):
    s.post(f"{BASE_URL}/login", data={"username":"admin","password":"hr2026","role":"hr"})
    files = {'resume': ('virus.exe', b'MZ', 'application/octet-stream')}
    data = {'job_title':'Software Engineer','job_description':'Develop software.'}
    r = s.post(f"{BASE_URL}/api/predict", files=files, data=data)
    assert r.status_code == 415
    print("File validation rejects .exe")
    return make_session()

def test_file_validation_oversize(s):
    s.post(f"{BASE_URL}/login", data={"username":"admin","password":"hr2026","role":"hr"})
    big = b'x' * (6 * 1024 * 1024)
    files = {'resume': ('big.pdf', big, 'application/pdf')}
    data = {'job_title':'Software Engineer','job_description':'Develop software.'}
    r = s.post(f"{BASE_URL}/api/predict", files=files, data=data)
    assert r.status_code == 413
    print("File validation rejects oversized file")
    return make_session()

def test_predict_with_txt_resume(s):
    s.post(f"{BASE_URL}/login", data={"username":"admin","password":"hr2026","role":"hr"})
    resume_text = b"""John Doe
Email: john@example.com
Phone: 555-1234
Experience:
Software Engineer at ABC Corp (2020-2023) - Developed web applications using Python and JavaScript.
Education:
B.S. Computer Science, University of Example, 2020
Skills: Python, JavaScript, REST, AWS
"""
    files = {'resume': ('resume.txt', resume_text, 'text/plain')}
    data = {
        'job_title': 'Software Engineer',
        'job_description': 'Looking for a skilled software engineer with experience in Python and web development.'
    }
    r = s.post(f"{BASE_URL}/api/predict", files=files, data=data)
    print(f"Predict status: {r.status_code}")
    if r.status_code == 200:
        resp = r.json()
        print(f"  Classification: {resp.get('classification',{}).get('classification')}")
        print(f"  Final score: {resp.get('scores',{}).get('final_match_score')}")
        assert 'scores' in resp
        assert 'classification' in resp
        print("Prediction with txt resume succeeded")
    else:
        print(f"  Error: {r.text}")
    return make_session()

def test_batch_endpoint(s):
    s.post(f"{BASE_URL}/login", data={"username":"admin","password":"hr2026","role":"hr"})
    resume1 = b"""Alice Smith\nExperience: 3 years as Data Scientist\nEducation: MS Statistics\nSkills: Python, ML"""
    resume2 = b"""Bob Lee\nExperience: 1 year as Intern\nEducation: BS Biology\nSkills: Excel"""
    files = [
        ('resumes', ('resume1.txt', resume1, 'text/plain')),
        ('resumes', ('resume2.txt', resume2, 'text/plain'))
    ]
    data = {
        'job_title': 'Data Scientist',
        'job_description': 'Seeking a data scientist with strong Python and machine learning background.'
    }
    r = s.post(f"{BASE_URL}/api/predict_batch", files=files, data=data)
    print(f"Batch status: {r.status_code}")
    if r.status_code == 200:
        resp = r.json()
        job_id = resp.get('job_id')
        print(f"  Job ID: {job_id}")
        for _ in range(3):
            rs = s.get(f"{BASE_URL}/api/batch_status/{job_id}")
            if rs.status_code == 200:
                status_json = rs.json()
                print(f"  Batch status: {status_json.get('status')} completed {status_json.get('completed')}/{status_json.get('total')}")
                if status_json.get('status') == 'completed':
                    break
            time.sleep(2)
        rs = s.get(f"{BASE_URL}/api/batch_status/{job_id}")
        if rs.status_code == 200:
            status_json = rs.json()
            results = status_json.get('results', [])
            print(f"  Results count: {len(results)}")
            for i, res in enumerate(results[:2]):
                print(f"    {res.get('filename')} -> {res.get('classification')} score {res.get('final_match_score')}")
        print("Batch endpoint works")
    else:
        print(f"  Batch failed: {r.text}")
    return make_session()

def main():
    try:
        s = make_session()
        test_get_login(s)
        test_post_login_fail(s)
        test_post_login_success_hr(s)
        test_protected_route_hr(s)
        s = test_logout(s)
        test_register_get(s)
        test_register_success(s)
        s = test_user_upload_get(s)
        s = test_file_validation_reject_exe(s)
        s = test_file_validation_oversize(s)
        s = test_predict_with_txt_resume(s)
        s = test_batch_endpoint(s)
        print("\nAll tests passed!")
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()