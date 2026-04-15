#!/usr/bin/env python3
"""Example script showing how to use the DXF Generator API programmatically."""

import requests
import json
import time


class DXFGeneratorClient:
    """Client for DXF Generator API."""

    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session_id = f"api_session_{int(time.time())}"

    def health_check(self):
        """Check if the server is running and configured."""
        response = requests.get(f"{self.base_url}/api/health")
        return response.json()

    def chat(self, message: str):
        """Send a chat message."""
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "message": message,
                "session_id": self.session_id
            }
        )
        return response.json()

    def generate_dxf(self, csv_metadata: str = None, filename: str = None):
        """Generate a DXF file."""
        payload = {"session_id": self.session_id}
        if csv_metadata:
            payload["csv_metadata"] = csv_metadata
        if filename:
            payload["filename"] = filename

        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload
        )
        return response.json()

    def download_file(self, download_url: str, save_path: str):
        """Download a generated DXF file."""
        full_url = f"{self.base_url}{download_url}"
        response = requests.get(full_url)

        with open(save_path, 'wb') as f:
            f.write(response.content)

        return save_path

    def preview_metadata(self):
        """Preview metadata for current session."""
        response = requests.post(
            f"{self.base_url}/api/preview",
            json={"session_id": self.session_id}
        )
        return response.json()


def example_1_simple_square():
    """Example 1: Generate a simple square."""
    print("\n" + "=" * 60)
    print("Example 1: Simple Square")
    print("=" * 60)

    client = DXFGeneratorClient()

    # Check health
    print("\n1. Checking server health...")
    health = client.health_check()
    print(f"   Status: {health['status']}")
    print(f"   OpenAI configured: {health['openai_configured']}")

    # Send chat message
    print("\n2. Sending drawing request...")
    message = "Draw a square 100mm on each side"
    result = client.chat(message)

    # Display conversation
    print("\n3. Conversation:")
    for msg in result['messages']:
        print(f"\n   [{msg['role'].upper()}]")
        print(f"   {msg['content'][:200]}...")

    # Generate DXF
    if result.get('can_generate'):
        print("\n4. Generating DXF file...")
        gen_result = client.generate_dxf(filename="example_square.dxf")

        if gen_result.get('success'):
            print(f"   ✓ Generated: {gen_result['filename']}")

            # Download file
            print("\n5. Downloading file...")
            save_path = f"output/{gen_result['filename']}"
            client.download_file(gen_result['download_url'], save_path)
            print(f"   ✓ Saved to: {save_path}")
        else:
            print(f"   ✗ Error: {gen_result.get('error')}")
    else:
        print("\n4. Not ready to generate (requires more input)")


def example_2_circle_with_lines():
    """Example 2: Circle with perpendicular lines."""
    print("\n" + "=" * 60)
    print("Example 2: Circle with Perpendicular Lines")
    print("=" * 60)

    client = DXFGeneratorClient()

    message = "Create a circle with radius 40mm at coordinates (0, 0), and draw two perpendicular lines through its center, each 100mm long"

    print("\n1. Sending request...")
    result = client.chat(message)

    print("\n2. Processing complete!")
    print(f"   Complete: {result['is_complete']}")
    print(f"   Can generate: {result.get('can_generate', False)}")

    if result.get('can_generate'):
        print("\n3. Previewing metadata...")
        preview = client.preview_metadata()
        print("\n   CSV Metadata:")
        print("   " + "-" * 56)
        for line in preview['csv_metadata'].split('\n')[:10]:
            print(f"   {line}")
        print("   ...")

        print("\n4. Generating DXF...")
        gen_result = client.generate_dxf(filename="example_circle_lines.dxf")

        if gen_result.get('success'):
            print(f"   ✓ File ready: {gen_result['filename']}")
            save_path = f"output/{gen_result['filename']}"
            client.download_file(gen_result['download_url'], save_path)
            print(f"   ✓ Downloaded to: {save_path}")


def example_3_complex_drawing():
    """Example 3: Complex mechanical part."""
    print("\n" + "=" * 60)
    print("Example 3: Complex Mechanical Part")
    print("=" * 60)

    client = DXFGeneratorClient()

    message = """Draw a mechanical flange:
    - Outer circle: 120mm diameter
    - Inner circle: 40mm diameter
    - Four mounting holes: 8mm diameter, positioned 80mm from center, equally spaced
    - All centered at origin"""

    print("\n1. Sending complex drawing request...")
    result = client.chat(message)

    print("\n2. Analyzing entities...")
    if 'metadata' in result and result['metadata'].get('entities'):
        entities = result['metadata']['entities']
        print(f"   Lines: {len(entities.get('lines', []))}")
        print(f"   Circles: {len(entities.get('circles', []))}")
        print(f"   Arcs: {len(entities.get('arcs', []))}")
        print(f"   Total entities: {len(entities.get('lines', [])) + len(entities.get('circles', [])) + len(entities.get('arcs', []))}")

    if 'metadata' in result and result['metadata'].get('validation'):
        validation = result['metadata']['validation']
        print(f"\n3. Validation:")
        print(f"   Valid: {validation.get('is_valid')}")
        print(f"   Confidence: {validation.get('confidence_score', 0) * 100:.1f}%")

        if validation.get('suggestions'):
            print(f"   Suggestions: {len(validation['suggestions'])} item(s)")

    if result.get('can_generate'):
        print("\n4. Generating DXF...")
        gen_result = client.generate_dxf(filename="example_flange.dxf")

        if gen_result.get('success'):
            print(f"   ✓ Success: {gen_result['filename']}")


def example_4_batch_generation():
    """Example 4: Generate multiple drawings in batch."""
    print("\n" + "=" * 60)
    print("Example 4: Batch Generation")
    print("=" * 60)

    drawings = [
        ("rectangle 150mm x 100mm", "batch_rectangle.dxf"),
        ("circle radius 35mm", "batch_circle.dxf"),
        ("triangle with 60mm sides", "batch_triangle.dxf"),
    ]

    for i, (description, filename) in enumerate(drawings, 1):
        print(f"\n{i}. Generating: {description}")

        client = DXFGeneratorClient()  # New session for each
        result = client.chat(f"Draw a {description}")

        if result.get('can_generate'):
            gen_result = client.generate_dxf(filename=filename)
            if gen_result.get('success'):
                print(f"   ✓ Created: {filename}")
            else:
                print(f"   ✗ Failed: {gen_result.get('error')}")
        else:
            print(f"   ⚠ Needs more input")


def main():
    """Main function."""
    print("\n" + "=" * 60)
    print("DXF Generator API Examples")
    print("=" * 60)
    print("\nMake sure the server is running:")
    print("  ./start.sh")
    print("\nOr in another terminal:")
    print("  conda activate dxfgen")
    print("  python -m backend.server")
    print()

    examples = [
        ("Simple square", example_1_simple_square),
        ("Circle with lines", example_2_circle_with_lines),
        ("Complex mechanical part", example_3_complex_drawing),
        ("Batch generation", example_4_batch_generation),
    ]

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    print()

    choice = input("Select example (1-4, or 'all'): ").strip().lower()

    try:
        if choice == 'all':
            for _, func in examples:
                func()
                time.sleep(1)  # Brief pause between examples
        else:
            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                examples[idx][1]()
            else:
                print("Invalid choice")
    except ValueError:
        print("Invalid input")
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Cannot connect to server")
        print("  Make sure the server is running on http://localhost:5000")
    except Exception as e:
        print(f"\n✗ Error: {e}")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == '__main__':
    main()
