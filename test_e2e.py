"""
Automated End-to-End (E2E) Integration Test Suite for Grievance Portal.
Tests full pipeline execution through Express REST API server endpoints.
"""

import time
import json
import urllib.request
import urllib.error
import subprocess
import sys
from pathlib import Path

BASE_URL = "http://localhost:3000"

def log(msg, status="INFO"):
    print(f"[{status}] {msg}")

def http_post(endpoint, data):
    url = f"{BASE_URL}{endpoint}"
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8")), resp.status

def http_get(endpoint):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8")), resp.status

def http_patch(endpoint, data):
    url = f"{BASE_URL}{endpoint}"
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="PATCH")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8")), resp.status


def run_e2e_tests():
    log("Starting E2E Integration Suite...", "RUN")
    passed = 0
    failed = 0

    # 1. Health check - server running?
    try:
        data, status = http_get("/api/analytics")
        assert status == 200
        log("Server health check passed.", "PASS")
        passed += 1
    except Exception as e:
        log(f"Server health check failed: {e}", "FAIL")
        log("Please start server (`node server.js`) before running test_e2e.py", "WARN")
        return False

    # 2. Test input validation (short text)
    try:
        res, status = http_post("/api/process-grievance", {"text": "short"})
        log(f"Short text test unexpected status: {status}", "FAIL")
        failed += 1
    except urllib.error.HTTPError as e:
        if e.code == 400:
            log("Validation test (min length guard) passed: HTTP 400 returned.", "PASS")
            passed += 1
        else:
            log(f"Validation test returned unexpected code: {e.code}", "FAIL")
            failed += 1

    # 3. Submit valid English complaint
    en_complaint = "Main water pipeline burst near Station Road. Heavy water logging."
    try:
        res, status = http_post("/api/process-grievance", {"text": en_complaint, "area": "Anna Nagar"})
        assert status == 200
        assert res["success"] is True
        ticket = res["ticket"]
        assert ticket["category"] == "Water Supply & Quality"
        assert ticket["priority"] == "Critical"
        ticket_id = ticket["id"]
        log(f"Submit English complaint passed -> Ticket {ticket_id} ({ticket['category']}, {ticket['priority']})", "PASS")
        passed += 1
    except Exception as e:
        log(f"Submit English complaint failed: {e}", "FAIL")
        failed += 1

    # 4. Submit near-duplicate complaint (Duplicate flag check)
    dup_complaint = "Main water pipeline burst near Station Road crossing. Thousands of gallons leaking."
    try:
        res, status = http_post("/api/process-grievance", {"text": dup_complaint, "area": "Anna Nagar"})
        assert status == 200
        assert res["success"] is True
        ticket = res["ticket"]
        assert ticket["duplicate_matched"] is True
        assert ticket["status"] == "Flagged Duplicate"
        log(f"Duplicate detection test passed -> Flagged Ticket {ticket['id']} (sim score={ticket['similarity_score']})", "PASS")
        passed += 1
    except Exception as e:
        log(f"Duplicate detection test failed: {e}", "FAIL")
        failed += 1

    # 5. Admin ticket status update
    try:
        res, status = http_patch(f"/api/grievances/{ticket_id}", {"status": "In Progress", "priority": "High"})
        assert status == 200
        assert res["ticket"]["status"] == "In Progress"
        assert res["ticket"]["priority"] == "High"
        log(f"Admin PATCH update test passed -> Status: {res['ticket']['status']}", "PASS")
        passed += 1
    except Exception as e:
        log(f"Admin PATCH update test failed: {e}", "FAIL")
        failed += 1

    # 6. Filter & Search query test
    try:
        res, status = http_get("/api/grievances?priority=High")
        assert status == 200
        assert res["total"] >= 1
        log(f"Query filtering test passed -> Total High priority grievances: {res['total']}", "PASS")
        passed += 1
    except Exception as e:
        log(f"Query filtering test failed: {e}", "FAIL")
        failed += 1

    # 7. Analytics endpoint verification
    try:
        res, status = http_get("/api/analytics")
        assert status == 200
        assert res["total_complaints"] >= 2
        log(f"Analytics endpoint passed -> Total complaints: {res['total_complaints']}, Duplicates: {res['duplicate_count']}", "PASS")
        passed += 1
    except Exception as e:
        log(f"Analytics endpoint test failed: {e}", "FAIL")
        failed += 1

    print("\n" + "="*50)
    print(f"E2E Integration Test Results: {passed} PASSED, {failed} FAILED")
    print("="*50 + "\n")

    return failed == 0

if __name__ == "__main__":
    success = run_e2e_tests()
    sys.exit(0 if success else 1)
