#!/usr/bin/env python3
"""Test script for DXF workflow without running the full server."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for API key
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("Error: OPENAI_API_KEY not set in .env file")
    print("Please create .env file with your OpenAI API key")
    sys.exit(1)

from backend.graph import DXFWorkflow
from backend.dxf_generator import DXFGenerator


def test_workflow(user_input: str, output_filename: str = None):
    """Test the workflow with a user input."""
    print("=" * 60)
    print("DXF Workflow Test")
    print("=" * 60)
    print(f"\nUser Input: {user_input}\n")

    # Initialize workflow
    print("Initializing workflow...")
    workflow = DXFWorkflow(api_key, model='gpt-4-turbo-preview')

    # Run workflow
    print("Running workflow...\n")
    result = workflow.run(user_input, max_iterations=3)

    # Display messages
    print("\n" + "=" * 60)
    print("Conversation:")
    print("=" * 60)
    for msg in result['messages']:
        role = "USER" if msg.type == "human" else "ASSISTANT"
        print(f"\n[{role}]")
        print(msg.content)

    # Display results
    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)

    if 'intent' in result:
        print("\nIntent:")
        print(f"  Type: {result['intent'].get('drawing_type')}")
        print(f"  Description: {result['intent'].get('description')}")

    if 'entities' in result:
        entities = result['entities']
        print("\nEntities:")
        print(f"  Lines: {len(entities.get('lines', []))}")
        print(f"  Circles: {len(entities.get('circles', []))}")
        print(f"  Arcs: {len(entities.get('arcs', []))}")
        print(f"  Polylines: {len(entities.get('polylines', []))}")
        print(f"  Hatches: {len(entities.get('hatches', []))}")

    if 'validation' in result:
        validation = result['validation']
        print("\nValidation:")
        print(f"  Valid: {validation.get('is_valid')}")
        print(f"  Confidence: {validation.get('confidence_score', 0):.1%}")

    if 'formatted_csv' in result:
        csv_data = result['formatted_csv']
        print("\nFormatted CSV Metadata:")
        print("-" * 60)
        print(csv_data)
        print("-" * 60)

        # Generate DXF
        print("\nGenerating DXF file...")
        generator = DXFGenerator()
        success, output_path, error = generator.generate(csv_data, output_filename)

        if success:
            print(f"✓ DXF file generated successfully!")
            print(f"  Output: {output_path}")
        else:
            print(f"✗ DXF generation failed: {error}")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


def main():
    """Main function."""
    # Test examples
    examples = [
        ("Draw a square 100mm on each side", "square.dxf"),
        ("Create a circle with radius 50mm at coordinates (0, 0)", "circle.dxf"),
        ("Draw a rectangle 150mm x 80mm with a circle of radius 30mm in the center", "rect_circle.dxf"),
    ]

    if len(sys.argv) > 1:
        # Use command line argument
        user_input = " ".join(sys.argv[1:])
        output_filename = "custom_drawing.dxf"
        test_workflow(user_input, output_filename)
    else:
        # Show menu
        print("\n" + "=" * 60)
        print("DXF Workflow Test - Examples")
        print("=" * 60)
        for i, (example, _) in enumerate(examples, 1):
            print(f"{i}. {example}")
        print(f"{len(examples) + 1}. Custom input")
        print()

        choice = input("Select an example (or press Enter for #1): ").strip()

        if not choice:
            choice = "1"

        try:
            idx = int(choice) - 1
            if idx < len(examples):
                user_input, output_filename = examples[idx]
                test_workflow(user_input, output_filename)
            elif idx == len(examples):
                user_input = input("\nEnter your drawing description: ").strip()
                if user_input:
                    test_workflow(user_input, "custom_drawing.dxf")
            else:
                print("Invalid choice")
        except ValueError:
            print("Invalid input")


if __name__ == '__main__':
    main()
