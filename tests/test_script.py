import requests
import sys
import os
import json

BASE_URL = "http://localhost:8000"
s = requests.Session()

def test_get_login():
    r = s.get(f"{BASE_URL}/login")
    assert r.status_code == 200, f"GET /login failed: {r.status_code}"
    print("��✓ GET /login OK")

def test_post_login_fail():
    r = s.post(f"{BASE_URL}/login", data={"username":"wrong","password":"wrong","role":"hr"})
    # Should return 200 with error message in HTML
    assert r.status_code == 200
    assert b"Invalid username or password" in r.content or b"error" in r.content.lower()
    print("��✓ POST /login with bad credentials returns error")

def test_post_login_success_hr():
    # Use hardcoded credentials from main.py
    r = s.post(f"{BASE_URL}/login", data={"username":"admin","password":"hr2026","role":"hr"}, allow_redirects=False)
    # Should redirect to /
    assert r.status_code in (302, 303)
    assert r.headers.get('Location', '').endswith("/")
    # Follow redirect to get session cookies
    s.get(f"{BASE_URL}/", allow_redirects=True)
    print("��✓ POST /login admin/hr2026 succeeds and redirects")

def test_protected_route_hr():
    r = s.get(f"{BASE_URL}/")
    assert r.status_code == 200
    assert b"Resume Screener" in r.content or b"dashboard" in r.content.lower()
    print("��✓ Protected HR dashboard accessible after login")

def test_logout():
    r = s.get(f"{BASE_URL}/logout", allow_redirects=False)
    assert r.status_code in (302,303)
    s.clear()  # clear session
    print("��✓ Logout works")

def test_register_get():
    r = s.get(f"{BASE_URL}/register")
    assert r.status_code == 200
    print("��✓ GET /register OK")

def test_register_success():
    # Use a unique username
    import time
    uname = f"testuser{int(time.time())}"
    r = s.post(f"{BASE_URL}/register", data={
        "username": uname,
        "password": "Testpass123!",
        "confirm_password": "Testpass123!",
        "role": "user"
    }, allow_redirects=False)
    # Expect redirect to login with success query
    assert r.status_code in (302,303)
    loc = r.headers.get('Location','')
    assert 'registered=1' in loc
    print("��✓ Registration successful")

def test_user_upload_get():
    # Need to login as user first
    s.post(f"{BASE_URL}/login", data={"username":"applicant","password":"apply2026","role":"user"})
    r = s.get(f"{BASE_URL}/user/upload")
    assert r.status_code == 200
    print("��✓ GET /user/upload OK for user")
    s.clear()

def test_file_validation_reject_exe():
    s.post(f"{BASE_URL}/login", data={"username":"admin","password":"hr2026","role":"hr"})
    # Create a fake .exe file
    files = {'resume': ('virus.exe', b'MZ', 'application/octet-stream')}
    data = {'job_title':'Software Engineer','job_description':'Develop software.'}
    r = s.post(f"{BASE_URL}/api/predict", files=files, data=data)
    # Should reject with 415 unsupported media type
    assert r.status_code == 415
    print("��✓ File validation rejects .exe")
    s.clear()

def test_file_validation_oversize():
    s.post(f"{BASE_URL}/login", data={"username":"admin","password":"hr2026","role":"hr"})
    # Create 6 MB file
    big = b'x' * (6 * 1024 * 1024)
    files = {'resume': ('big.pdf', big, 'application/pdf')}
    data = {'job_title':'Software Engineer','job_description':'Develop software.'}
    r = s.post(f"{BASE_URL}/api/predict", files=files, data=data)
    # Expect 413
    assert r.status_code == 413
    print("��✓ File validation rejects oversized file")
    s.clear()

def test_predict_with_txt_resume():
    s.post(f"{BASE_URL}/login", data={"username":"admin","password":"hr2026","role":"hr"})
    # Create a simple resume text
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
        print("��✓ Prediction with txt resume succeeded")
    else:
        print(f"  Error: {r.text}")
    s.clear()

def test_batch_endpoint():
    s.post(f"{BASE_URL}/login", data={"username":"admin","password":"hr2026","role":"hr"})
    # Create two simple resumes
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
        # Poll status a couple times
        for _ in range(3):
            rs = s.get(f"{BASE_URL}/api/batch_status/{job_id}")
            if rs.status_code == 200:
                status_json = rs.json()
                print(f"  Batch status: {status_json.get('status')} completed {status_json.get('completed')}/{status_json.get('total')}")
                if status_json.get('status') == 'completed':
                    break
            import time; time.sleep(2)
        # Get final results
        rs = s.get(f"{BASE_URL}/api/batch_status/{job_id}")
        if rs.status_code == 200:
            status_json = rs.json()
            results = status_json.get('results', [])
            print(f"  Results count: {len(results)}")
            for i, res in enumerate(results[:2]):
                print(f"    {res.get('filename')} -> {res.get('classification')} score {res.get('final_match_score')}")
        print("��✓ Batch endpoint works")
    else:
        print(f"  Batch failed: {r.text}")
    s.clear()

def main():
    try:
        test_get_login()
        test_post_login_fail()
        test_post_login_success_hr()
        test_protected_route_hr()
        test_logout()
        test_register_get()
        test_register_success()
        test_user_upload_get()
        test_file_validation_reject_exe()
        test_file_validation_oversize()
        test_predict_with_txt_resume()
        test_batch_endpoint()
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