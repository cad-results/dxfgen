#!/usr/bin/env python3
"""
Automated test script for DXF Generator chatbot.
Tests various prompts including warehouses, spaceships, castles, and BREP objects.
"""

import requests
import time
import json
import sys
from typing import Dict, Any, List

BASE_URL = "http://localhost:5001"

# Test prompts to run
TEST_PROMPTS = [
    {
        "name": "Warehouse",
        "prompt": "Draw a warehouse with loading docks, storage shelves, and a main entrance. Include dimensions for a 50m x 30m building."
    },
    {
        "name": "Spaceship",
        "prompt": "Draw a spaceship with a cockpit, engine room, cargo bay, and sleeping quarters. Include curved hull sections and airlock doors."
    },
    {
        "name": "Princess Peach's Castle",
        "prompt": "Draw Princess Peach's castle from Mario with towers, a main entrance, stained glass windows, and a courtyard. Include the iconic red roofs and white walls."
    },
    {
        "name": "BREP Plumber's Pipes",
        "prompt": "Draw BREP plumber's pipes including elbows, T-junctions, straight sections, and flanged connections. Use standard 2-inch pipe dimensions with proper wall thickness."
    },
    {
        "name": "BREP Bolts",
        "prompt": "Draw BREP bolts including hex head bolts, washers, and nuts. Include M10 and M12 sizes with proper thread representations and head dimensions."
    }
]


class ChatbotTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []

    def check_server(self) -> bool:
        """Check if the server is running."""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False

    def send_chat(self, message: str, session_id: str) -> Dict[str, Any]:
        """Send a chat message to the chatbot."""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "message": message,
                    "session_id": session_id,
                    "settings": {
                        "auto_accept_mode": True,  # Auto-accept to avoid blocking on validation
                        "quality_level": "professional"
                    }
                },
                timeout=120  # Allow up to 2 minutes for complex prompts
            )
            return response.json()
        except requests.exceptions.Timeout:
            return {"error": "Request timed out after 120 seconds"}
        except requests.exceptions.ConnectionError as e:
            return {"error": f"Connection error: {str(e)}"}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON response: {str(e)}"}

    def run_test(self, test_case: Dict[str, str]) -> Dict[str, Any]:
        """Run a single test case."""
        name = test_case["name"]
        prompt = test_case["prompt"]
        session_id = f"autotest_{name.lower().replace(' ', '_')}_{int(time.time())}"

        print(f"\n{'='*60}")
        print(f"Testing: {name}")
        print(f"{'='*60}")
        print(f"Prompt: {prompt[:80]}...")
        print(f"Session ID: {session_id}")
        print("-" * 60)

        start_time = time.time()
        result = self.send_chat(prompt, session_id)
        elapsed_time = time.time() - start_time

        test_result = {
            "name": name,
            "prompt": prompt,
            "session_id": session_id,
            "elapsed_time": elapsed_time,
            "success": "error" not in result,
            "response": result
        }

        # Print summary
        if "error" in result:
            print(f"ERROR: {result['error']}")
            test_result["error"] = result["error"]
        else:
            print(f"Status: SUCCESS")
            print(f"Time: {elapsed_time:.2f}s")

            # Extract key information
            if "metadata" in result:
                metadata = result["metadata"]
                if "entities" in metadata:
                    entities = metadata["entities"]
                    entity_counts = {k: len(v) if isinstance(v, list) else v
                                   for k, v in entities.items() if v}
                    print(f"Entities extracted: {entity_counts}")
                    test_result["entity_counts"] = entity_counts

                if "validation" in metadata:
                    validation = metadata["validation"]
                    print(f"Validation: valid={validation.get('is_valid', 'N/A')}, "
                          f"confidence={validation.get('confidence_score', 'N/A')}")
                    test_result["validation"] = validation

            if "csv_metadata" in result:
                csv_lines = result["csv_metadata"].strip().split("\n")
                print(f"CSV lines generated: {len(csv_lines)}")
                test_result["csv_line_count"] = len(csv_lines)

            if result.get("can_generate"):
                print("Ready to generate DXF: YES")
            else:
                print("Ready to generate DXF: NO")
                if "requires_feedback" in result and result["requires_feedback"]:
                    print("Requires user feedback")

            # Print any validation issues
            if "metadata" in result and "validation" in result["metadata"]:
                issues = result["metadata"]["validation"].get("issues", [])
                if issues:
                    print(f"\nValidation issues ({len(issues)}):")
                    for issue in issues[:5]:  # Show first 5 issues
                        print(f"  - {issue}")
                    if len(issues) > 5:
                        print(f"  ... and {len(issues) - 5} more")

        self.results.append(test_result)
        return test_result

    def run_all_tests(self) -> None:
        """Run all test cases."""
        print("\n" + "=" * 60)
        print("DXF Generator Chatbot - Automated Test Suite")
        print("=" * 60)

        # Check server first
        print("\nChecking server availability...")
        if not self.check_server():
            print(f"ERROR: Server not available at {self.base_url}")
            print("Please start the server first with: python -m backend.server")
            sys.exit(1)
        print(f"Server is running at {self.base_url}")

        # Run all tests
        for test_case in TEST_PROMPTS:
            self.run_test(test_case)
            time.sleep(1)  # Brief pause between tests

        # Print summary
        self.print_summary()

    def print_summary(self) -> None:
        """Print test summary."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        failed = total - passed

        print(f"\nTotal tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")

        print("\nDetailed Results:")
        print("-" * 60)
        for r in self.results:
            status = "PASS" if r["success"] else "FAIL"
            time_str = f"{r['elapsed_time']:.2f}s"
            entities = r.get("entity_counts", {})
            entity_str = ", ".join(f"{k}:{v}" for k, v in entities.items()) if entities else "N/A"

            print(f"  [{status}] {r['name']:<25} | {time_str:>8} | Entities: {entity_str}")

            if not r["success"]:
                print(f"         Error: {r.get('error', 'Unknown error')}")

        print("\n" + "=" * 60)

        # Save results to file
        results_file = f"test_results_{int(time.time())}.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"Full results saved to: {results_file}")


def main():
    """Main entry point."""
    tester = ChatbotTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
