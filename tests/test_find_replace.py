import pytest
from mote.core.buffer import Buffer


class TestFind:
    def test_find_literal(self):
        """Test finding literal text"""
        buf = Buffer("hello world\nhello there\nhow are you")
        occurrences = buf.find("hello", use_regex=False)
        assert len(occurrences) == 2
        assert occurrences[0] == (0, 0, 0, 5)
        assert occurrences[1] == (1, 0, 1, 5)

    def test_find_regex(self):
        """Test finding with regex"""
        buf = Buffer("hello123 world456 test789")
        occurrences = buf.find(r"\d+", use_regex=True)
        assert len(occurrences) == 3

    def test_find_empty_pattern_literal(self):
        """Empty literal pattern returns empty list (no infinite loop)"""
        buf = Buffer("hello world")
        assert buf.find("", use_regex=False) == []

    def test_find_empty_pattern_regex(self):
        """Empty regex pattern returns empty list"""
        buf = Buffer("hello world")
        assert buf.find("", use_regex=True) == []

    def test_find_multiline(self):
        """Test finding a pattern that spans multiple lines"""
        buf = Buffer("line1\nline2\nline3")
        occurrences = buf.find("line2\nline3", use_regex=False)
        assert len(occurrences) == 1
        assert occurrences[0] == (1, 0, 2, 5)

    def test_find_no_match(self):
        """Test finding a pattern with no matches"""
        buf = Buffer("hello world")
        assert buf.find("xyz", use_regex=False) == []

    def test_find_invalid_regex(self):
        """Invalid regex returns empty list"""
        buf = Buffer("hello world")
        assert buf.find("[invalid", use_regex=True) == []


class TestReplaceAll:
    def test_replace_all_literal(self):
        """Test replacing all occurrences with literal text"""
        buf = Buffer("foo bar foo baz foo")
        count = buf.replace_all("foo", "FOO", use_regex=False)
        assert count == 3
        assert buf.get_full_text() == "FOO bar FOO baz FOO"
        assert buf.dirty is True

    def test_replace_all_regex(self):
        """Test replacing all occurrences with regex"""
        buf = Buffer("The year 2024 and 2025 are coming")
        count = buf.replace_all(r"\d{4}", "XXXX", use_regex=True)
        assert count == 2
        assert buf.get_full_text() == "The year XXXX and XXXX are coming"

    def test_replace_all_empty_pattern(self):
        """Empty pattern is a no-op and returns 0"""
        buf = Buffer("hello world")
        original = buf.get_full_text()
        count = buf.replace_all("", "X", use_regex=False)
        assert count == 0
        assert buf.get_full_text() == original

    def test_replace_all_no_match(self):
        """Replace with no matches returns 0 and leaves buffer unchanged"""
        buf = Buffer("hello world")
        count = buf.replace_all("xyz", "abc", use_regex=False)
        assert count == 0
        assert buf.get_full_text() == "hello world"
        assert buf.dirty is False


class TestReplaceSpecific:
    def test_replace_specific(self):
        """Test replacing at a specific location"""
        buf = Buffer("apple apple apple")
        occurrences = buf.find("apple", use_regex=False)
        success = buf.replace_specific(occurrences[1], "orange")
        assert success is True
        assert buf.get_full_text() == "apple orange apple"

    def test_replace_specific_invalid_location(self):
        """Test replacing with invalid location tuple"""
        buf = Buffer("test test test")
        success = buf.replace_specific((10, 0, 4), "replaced")
        assert success is False
        assert buf.get_full_text() == "test test test"

    def test_replace_specific_multiline(self):
        """Test replacing a multi-line match"""
        buf = Buffer("line1\nline2\nline3")
        occurrences = buf.find("line2\nline3", use_regex=False)
        success = buf.replace_specific(occurrences[0], "REPLACED")
        assert success is True
        assert buf.get_full_text() == "line1\nREPLACED"

    def test_replace_specific_out_of_bounds(self):
        """Out-of-bounds location returns False"""
        buf = Buffer("hello")
        success = buf.replace_specific((5, 0, 6, 0), "x")
        assert success is False
        assert buf.get_full_text() == "hello"
