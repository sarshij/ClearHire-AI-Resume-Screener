import sys, httpx

BASE = 'http://localhost:8000'

def ok(name, passed, detail=''):
    sym = 'PASS' if passed else 'FAIL'
    print(f'  [{sym}] {name}' + (f' -- {detail}' if detail else ''))
    return passed

def main():
    print('\n' + '='*60)
    print('  ClearHire Live API Deep Test')
    print('='*60)
    R = []

    # Health
    print('\n--- Health ---')
    try:
        r = httpx.get(f'{BASE}/health', timeout=10)
        d = r.json()
        R.append(ok('Health 200', r.status_code == 200))
        R.append(ok('status=ok', d.get('status') == 'ok', str(d)))
        R.append(ok('model_loaded key present', 'model_loaded' in d))
    except Exception as e:
        R.append(ok('Server reachable', False, str(e)))
        print('  ERROR: Server not running. Start it first.')
        return

    # Unauthenticated redirects
    print('\n--- Unauth Redirects ---')
    for path in ['/', '/batch', '/analytics']:
        r = httpx.get(f'{BASE}{path}', follow_redirects=False, timeout=10)
        R.append(ok(f'GET {path} -> /login redirect', r.status_code in (302,303) and '/login' in r.headers.get('location',''), f'status={r.status_code}'))

    # Login page
    print('\n--- Login Page ---')
    r = httpx.get(f'{BASE}/login', timeout=10)
    R.append(ok('Login page 200', r.status_code == 200))
    R.append(ok('Has form tag', '<form' in r.text))
    R.append(ok('Has username field', 'username' in r.text))

    # Wrong creds
    print('\n--- Wrong Credentials ---')
    r = httpx.post(f'{BASE}/login', data={'username':'admin','password':'WRONG','role':'hr'}, follow_redirects=False, timeout=10)
    R.append(ok('Wrong creds -> 200 (error page)', r.status_code == 200))
    R.append(ok('Error message shown', 'invalid' in r.text.lower()))

    # Correct HR login
    print('\n--- HR Login + Pages ---')
    c = httpx.Client(follow_redirects=True, timeout=20)
    r = c.post(f'{BASE}/login', data={'username':'admin','password':'hr2026','role':'hr'})
    R.append(ok('HR login 200', r.status_code == 200))
    R.append(ok('Landed on dashboard', str(r.url).rstrip('/').endswith(BASE.rstrip('/'))))
    R.append(ok('Dashboard has ClearHire', 'ClearHire' in r.text))

    # Pages
    for path, kw in [('/batch','batchForm'), ('/analytics','analytics')]:
        r = c.get(f'{BASE}{path}')
        R.append(ok(f'{path} loads 200', r.status_code == 200))
        R.append(ok(f'{path} has content', kw.lower() in r.text.lower()))

    # Model info
    print('\n--- Model Info API ---')
    r = c.get(f'{BASE}/api/model/info')
    R.append(ok('/api/model/info 200', r.status_code == 200))
    d = r.json()
    R.append(ok('Has test_accuracy', 'test_accuracy' in d))
    R.append(ok('Accuracy > 0.5', float(d.get('test_accuracy',0)) > 0.5, str(d.get('test_accuracy'))))
    R.append(ok('Feature importance list', isinstance(d.get('feature_importance'), list) and len(d.get('feature_importance',[])) > 0))

    # History API
    print('\n--- History API ---')
    r = c.get(f'{BASE}/api/history?limit=10')
    R.append(ok('/api/history 200', r.status_code == 200, f'status={r.status_code}'))
    d = r.json()
    R.append(ok('history key present', 'history' in d))
    R.append(ok('history is list', isinstance(d.get('history'), list)))

    # Analytics export
    print('\n--- Analytics Export ---')
    r = c.get(f'{BASE}/api/export/analytics')
    R.append(ok('/api/export/analytics 200', r.status_code == 200))
    R.append(ok('CSV content-type', 'text/csv' in r.headers.get('content-type','')))
    R.append(ok('Content-Disposition set', 'attachment' in r.headers.get('content-disposition','')))
    R.append(ok('CSV has Metric header', 'Metric' in r.text or 'metric' in r.text.lower()))
    R.append(ok('CSV has accuracy row', 'accuracy' in r.text.lower()))

    # History CSV export
    print('\n--- History CSV Export ---')
    r = c.get(f'{BASE}/api/export?format=csv')
    R.append(ok('/api/export?format=csv 200', r.status_code == 200, f'status={r.status_code}'))
    if r.status_code == 200:
        R.append(ok('CSV content-type', 'text/csv' in r.headers.get('content-type','')))

    # History JSON export
    r = c.get(f'{BASE}/api/export?format=json')
    R.append(ok('/api/export?format=json 200', r.status_code == 200))
    if r.status_code == 200:
        d = r.json()
        R.append(ok('JSON has data key', 'data' in d))

    # Logout
    print('\n--- Logout ---')
    r = c.get(f'{BASE}/logout', follow_redirects=False)
    R.append(ok('Logout redirects', r.status_code in (302,303)))
    R.append(ok('Logout -> /login', '/login' in r.headers.get('location','')))
    r2 = c.get(f'{BASE}/', follow_redirects=False)
    R.append(ok('After logout / -> /login', r2.status_code in (302,303)))
    c.close()

    passed = sum(R)
    total = len(R)
    print('\n' + '='*60)
    print(f'  RESULT: {passed}/{total} passed')
    if passed == total:
        print('  ALL TESTS PASSED -- System is fully functional!')
    else:
        print(f'  {total-passed} FAILED -- check FAIL lines above')
    print('='*60 + '\n')
    return passed == total

if __name__ == '__main__':
    ok2 = main()
    sys.exit(0 if ok2 else 1)
