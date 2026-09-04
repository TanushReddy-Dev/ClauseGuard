"""Smoke test — run with: python smoke_test.py"""
import subprocess, sys, time, httpx

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8003"],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
)
time.sleep(4)

try:
    r = httpx.post(
        "http://127.0.0.1:8003/analyze-contract",
        files={"file": ("test.jpg", b"fake image bytes", "image/jpeg")},
    )
    print(f"Status: {r.status_code}")
    import json
    print(json.dumps(r.json(), indent=2))
    assert r.status_code == 200
    data = r.json()
    assert "clauses" in data
    assert "overall_risk_score" in data
    assert "negotiation_script" in data
    print("\nAll assertions passed")
finally:
    proc.terminate()
    proc.wait()
