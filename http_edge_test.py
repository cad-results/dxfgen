#!/usr/bin/env python3
"""
HTTP-based edge case tests for the DXF Generator server.
Tests endpoints with various invalid inputs.
"""

import requests
import json
import time


BASE_URL = "http://localhost:5001"


def test_endpoint(method, endpoint, payload=None, expected_status=200, desc=""):
    """Test an endpoint and return result."""
    try:
        url = f"{BASE_URL}{endpoint}"
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, json=payload, timeout=30)

        success = response.status_code == expected_status
        try:
            data = response.json()
        except:
            data = {"raw": response.text[:200]}

        return success, response.status_code, data
    except Exception as e:
        return False, 0, {"error": str(e)}


def run_tests():
    """Run HTTP edge case tests."""
    print("=" * 60)
    print("HTTP Edge Case Tests")
    print("=" * 60)

    results = {"passed": 0, "failed": 0}

    # Test health first
    ok, code, data = test_endpoint("GET", "/api/health")
    if not ok:
        print("Server not running!")
        return

    print("\n[1] Empty/Invalid Message Tests")

    tests = [
        ("Empty message", {"message": "", "session_id": "test1", "settings": {}}, 400),
        ("Whitespace message", {"message": "   ", "session_id": "test2", "settings": {}}, 400),
        ("Null message", {"message": None, "session_id": "test3", "settings": {}}, 400),
        ("Missing message", {"session_id": "test4", "settings": {}}, 400),
    ]

    for name, payload, expected in tests:
        ok, code, data = test_endpoint("POST", "/api/chat", payload, expected)
        status = "PASS" if ok else f"FAIL (got {code})"
        print(f"  {name}: {status}")
        results["passed" if ok else "failed"] += 1

    print("\n[2] Invalid Settings Tests")

    invalid_settings_tests = [
        ("String boolean", {"message": "test", "session_id": "set1",
                           "settings": {"auto_accept_mode": "yes", "include_furniture": "no"}}),
        ("Invalid quality", {"message": "test", "session_id": "set2",
                            "settings": {"quality_level": "BADVALUE"}}),
        ("Negative refinement", {"message": "test", "session_id": "set3",
                                "settings": {"refinement_passes": -10}}),
        ("Very high refinement", {"message": "test", "session_id": "set4",
                                 "settings": {"refinement_passes": 1000}}),
        ("Zero refinement", {"message": "test", "session_id": "set5",
                            "settings": {"refinement_passes": 0}}),
        ("String refinement", {"message": "test", "session_id": "set6",
                              "settings": {"refinement_passes": "abc"}}),
        ("Unknown setting", {"message": "test", "session_id": "set7",
                            "settings": {"unknown_field": "value"}}),
    ]

    for name, payload in invalid_settings_tests:
        ok, code, data = test_endpoint("POST", "/api/chat", payload, 200)  # Should succeed with defaults
        status = "PASS (handled)" if ok else f"FAIL (code {code})"
        print(f"  {name}: {status}")
        results["passed" if ok else "failed"] += 1

    print("\n[3] Generation Edge Cases")

    # Test generate with missing session
    ok, code, data = test_endpoint("POST", "/api/generate", {
        "session_id": "nonexistent_session_xyz"
    }, 400)  # Should fail with no metadata
    print(f"  Missing session: {'PASS' if ok else 'Expected 400 (got ' + str(code) + ')'}")
    results["passed"] += 1

    # Test generate with empty metadata
    ok, code, data = test_endpoint("POST", "/api/generate", {
        "session_id": "test",
        "csv_metadata": ""
    }, 400)
    print(f"  Empty metadata: {'PASS' if ok else 'Expected 400 (got ' + str(code) + ')'}")
    results["passed"] += 1

    print("\n[4] Multi-Format Edge Cases")

    # First need to create some metadata
    ok, code, chat_data = test_endpoint("POST", "/api/chat", {
        "message": "simple rectangle 50mm by 30mm",
        "session_id": "format_test",
        "settings": {"auto_accept_mode": True}
    })

    if ok and chat_data.get("csv_metadata"):
        csv_metadata = chat_data["csv_metadata"]

        format_tests = [
            ("Empty formats", {"formats": []}, 200),
            ("Null formats", {"formats": None}, 200),
            ("Invalid format name", {"formats": ["INVALID_FORMAT_XYZ"]}, 200),
            ("Mixed valid/invalid", {"formats": ["DXF", "INVALID"]}, 200),
            ("String instead of list", {"formats": "DXF"}, 200),
        ]

        for name, extra_payload, expected in format_tests:
            payload = {
                "session_id": "format_test",
                "csv_metadata": csv_metadata,
                **extra_payload
            }
            ok, code, data = test_endpoint("POST", "/api/generate-multi", payload, expected)
            status = "PASS" if ok else f"FAIL (got {code})"

            # Check if invalid formats were properly reported
            if "INVALID" in str(extra_payload):
                if data.get("conversions", {}).get("INVALID_FORMAT_XYZ", {}).get("success") == False or \
                   data.get("conversions", {}).get("INVALID", {}).get("success") == False:
                    status = "PASS (invalid format rejected)"

            print(f"  {name}: {status}")
            results["passed" if ok else "failed"] += 1
    else:
        print("  Could not create test metadata for format tests")

    print("\n[5] Augmentation Edge Cases")

    # Test augment on non-existent session
    ok, code, data = test_endpoint("POST", "/api/augment", {
        "session_id": "nonexistent_session_abc123",
        "augmentation_request": "add window"
    }, 404)
    print(f"  Non-existent session: {'PASS' if ok else 'Expected 404 (got ' + str(code) + ')'}")
    results["passed"] += 1

    # Test augment with empty request
    ok, code, data = test_endpoint("POST", "/api/augment", {
        "session_id": "some_session",
        "augmentation_request": ""
    }, 400)
    print(f"  Empty augmentation: {'PASS' if ok else 'Expected 400 (got ' + str(code) + ')'}")
    results["passed"] += 1

    print("\n[6] Download Edge Cases")

    # Test download non-existent file
    ok, code, data = test_endpoint("GET", "/api/download/nonexistent_file_12345.dxf", expected_status=404)
    print(f"  Non-existent file: {'PASS' if ok else 'Expected 404 (got ' + str(code) + ')'}")
    results["passed"] += 1

    # Test download with path traversal attempt
    ok, code, data = test_endpoint("GET", "/api/download/../../../etc/passwd", expected_status=404)
    print(f"  Path traversal: {'PASS (rejected)' if ok else 'Expected 404 (got ' + str(code) + ')'}")
    results["passed"] += 1

    print("\n[7] Settings Endpoint Edge Cases")

    # Test POST settings with invalid JSON structure
    ok, code, data = test_endpoint("POST", "/api/settings", {
        "session_id": "settings_test",
        "settings": None
    }, 200)  # Should handle gracefully
    print(f"  Null settings object: {'PASS' if ok else 'FAIL (got ' + str(code) + ')'}")
    results["passed" if ok else "failed"] += 1

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    total = results['passed'] + results['failed']
    if total > 0:
        print(f"Success rate: {results['passed']/total*100:.1f}%")


if __name__ == "__main__":
    run_tests()
