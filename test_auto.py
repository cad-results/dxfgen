#!/usr/bin/env python3
"""Automated testing script for DXF API."""

import requests
import time
import json
import sys

API_URL = "http://localhost:5000/api/chat"
TEST_MESSAGE = "build a big house"  # This will trigger detail refinement
SESSION_ID = "test_session"

def test_request(iteration):
    """Send a test request to the API."""
    print(f"\n{'='*60}")
    print(f"Test Iteration {iteration}")
    print(f"{'='*60}")

    payload = {
        "message": TEST_MESSAGE,
        "session_id": f"{SESSION_ID}_{iteration}",
        "settings": {
            "units": "metric",
            "wall_thickness": 200,
            "door_width": 900,
            "window_size": "1200x1200"
        }
    }

    print(f"Sending request: {TEST_MESSAGE}")
    print(f"Session ID: {payload['session_id']}")

    try:
        response = requests.post(API_URL, json=payload, timeout=120)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✓ SUCCESS")
            print(f"Messages: {len(data.get('messages', []))}")
            print(f"Requires Feedback: {data.get('requires_feedback', False)}")
            print(f"Is Complete: {data.get('is_complete', False)}")

            # Print last message
            if data.get('messages'):
                last_msg = data['messages'][-1]
                content = last_msg.get('content', '')
                preview = content[:200] + "..." if len(content) > 200 else content
                print(f"Last message preview: {preview}")

            return True
        else:
            print("✗ FAILED")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"Error: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("✗ CONNECTION ERROR - Server not running?")
        return False
    except requests.exceptions.Timeout:
        print("✗ TIMEOUT - Request took too long")
        return False
    except Exception as e:
        print(f"✗ EXCEPTION: {e}")
        return False

def main():
    """Run automated tests."""
    print("DXF API Automated Testing")
    print("Press Ctrl+C to stop")

    # Wait for server to start
    print("\nWaiting for server to start...")
    time.sleep(3)

    # Check health endpoint first
    try:
        health_response = requests.get("http://localhost:5000/api/health", timeout=5)
        if health_response.status_code == 200:
            print("✓ Server is healthy")
            health_data = health_response.json()
            print(f"  OpenAI configured: {health_data.get('openai_configured', False)}")
        else:
            print("✗ Server health check failed")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Cannot connect to server: {e}")
        sys.exit(1)

    # Run tests
    iteration = 1
    successes = 0
    failures = 0

    try:
        while True:
            success = test_request(iteration)

            if success:
                successes += 1
            else:
                failures += 1

            print(f"\nStats: {successes} successes, {failures} failures")

            # Wait between requests
            print("Waiting 5 seconds before next test...")
            time.sleep(5)

            iteration += 1

    except KeyboardInterrupt:
        print("\n\nTest stopped by user")
        print(f"Final stats: {successes} successes, {failures} failures")
        sys.exit(0)

if __name__ == "__main__":
    main()
