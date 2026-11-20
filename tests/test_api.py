"""Manual authenticated API smoke test.

Set TEST_EMAIL and TEST_PASSWORD to an existing CodeClarity account, start
`python app.py`, then run `PYTHONPATH=. python tests/test_api.py`.
"""
import http.cookiejar
import json
import os
import re
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPCookieProcessor

BASE_URL = os.getenv("CODECLARITY_URL", "http://127.0.0.1:5001")
EMAIL = os.getenv("TEST_EMAIL")
PASSWORD = os.getenv("TEST_PASSWORD")
if not EMAIL or not PASSWORD:
    raise SystemExit("Set TEST_EMAIL and TEST_PASSWORD to an existing test account.")

opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
login_page = opener.open(BASE_URL + "/login")
html = login_page.read().decode("utf-8")
match = re.search(r'name="csrf_token" value="([^"]+)"', html)
if not match:
    raise SystemExit("Could not find the login CSRF token.")
csrf = match.group(1)
login_request = Request(
    BASE_URL + "/login",
    data=urlencode({"email": EMAIL, "password": PASSWORD, "csrf_token": csrf}).encode(),
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    method="POST",
)
opener.open(login_request)

# Fetch a fresh token after login, then call the protected JSON endpoint.
workspace = opener.open(BASE_URL + "/analyzer").read().decode("utf-8")
match = re.search(r'<meta name="csrf-token" content="([^"]+)"', workspace)
if not match:
    raise SystemExit("Could not find the analyzer CSRF token.")
csrf = match.group(1)
data = {
    "code": "#include <stdio.h>\nint main(void) { printf(\"CodeClarity API OK\\n\"); return 0; }",
    "language": "c",
    "user_input": "",
}
request = Request(
    BASE_URL + "/api/analyze",
    data=json.dumps(data).encode(),
    headers={"Content-Type": "application/json", "X-CSRFToken": csrf},
    method="POST",
)
with opener.open(request, timeout=120) as response:
    result = json.loads(response.read().decode())
    print(json.dumps(result, indent=2))
