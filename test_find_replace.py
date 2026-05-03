#!/usr/bin/env python3
"""
Simple test to demonstrate find and replace functionality
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from mote.core.buffer import Buffer


def test_find_literal():
    """Test finding literal text"""
    buf = Buffer("hello world\nhello there\nhow are you")
    
    # Find all occurrences of "hello"
    occurrences = buf.find("hello", use_regex=False)
    print("Find 'hello' (literal):", occurrences)
    assert len(occurrences) == 2
    assert occurrences[0] == (0, 0, 5)  # Line 0, col 0-5
    assert occurrences[1] == (1, 0, 5)  # Line 1, col 0-5


def test_find_regex():
    """Test finding with regex"""
    buf = Buffer("hello123 world456 test789")
    
    # Find all numbers
    occurrences = buf.find(r"\d+", use_regex=True)
    print("Find digits (regex):", occurrences)
    assert len(occurrences) == 3


def test_replace_all_literal():
    """Test replacing all occurrences with literal text"""
    buf = Buffer("foo bar foo baz foo")
    
    count = buf.replace_all("foo", "FOO", use_regex=False)
    print(f"Replaced {count} occurrences of 'foo'")
    print("Result:", buf.get_full_text())
    
    assert count == 3
    assert buf.get_full_text() == "FOO bar FOO baz FOO"
    assert buf.dirty == True


def test_replace_all_regex():
    """Test replacing all occurrences with regex"""
    buf = Buffer("The year 2024 and 2025 are coming")
    
    count = buf.replace_all(r"\d{4}", "XXXX", use_regex=True)
    print(f"Replaced {count} years")
    print("Result:", buf.get_full_text())
    
    assert count == 2
    assert buf.get_full_text() == "The year XXXX and XXXX are coming"


def test_replace_specific():
    """Test replacing at a specific location"""
    buf = Buffer("apple apple apple")
    
    # Find all occurrences
    occurrences = buf.find("apple", use_regex=False)
    print("Found occurrences:", occurrences)
    
    # Replace the 2nd occurrence using its location
    success = buf.replace_specific(occurrences[1], "orange")
    print("Replace 2nd 'apple' with 'orange':", success)
    print("Result:", buf.get_full_text())
    
    assert success == True
    assert buf.get_full_text() == "apple orange apple"


def test_replace_specific_invalid_location():
    """Test replacing with invalid location"""
    buf = Buffer("test test test")
    
    # Try to replace with invalid location
    success = buf.replace_specific((10, 0, 4), "replaced")
    print("Replace with invalid location:", success)
    
    assert success == False
    assert buf.get_full_text() == "test test test"


if __name__ == "__main__":
    print("Testing find and replace functionality...\n")
    
    test_find_literal()
    print()
    
    test_find_regex()
    print()
    
    test_replace_all_literal()
    print()
    
    test_replace_all_regex()
    print()
    
    test_replace_specific()
    print()
    
    test_replace_specific_invalid_location()
    print()
    
    print("All tests passed!")
