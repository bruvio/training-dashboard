#!/usr/bin/env python3
"""Test script to debug the upload button issue."""

import base64


# Simple test to verify base64 handling works correctly
def test_base64_handling():
    # Create a small test file content
    test_content = b"Test FIT file content"

    # Encode like browser would
    encoded = base64.b64encode(test_content).decode()

    # Decode like our upload handler would
    decoded = base64.b64decode(encoded)

    print(f"Original: {test_content}")
    print(f"Encoded: {encoded}")
    print(f"Decoded: {decoded}")
    print(f"Match: {test_content == decoded}")


if __name__ == "__main__":
    test_base64_handling()
