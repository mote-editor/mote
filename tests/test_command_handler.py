import pytest
from mote.core.command_handler import CommandHandler


class TestCommandHandler:
    """Tests for the CommandHandler callable."""

    def setup_method(self):
        self.handler = CommandHandler()

    def test_quit_returns_false(self):
        """'q' should signal quit."""
        assert self.handler("q") is False

    def test_quit_word_returns_false(self):
        """'quit' should signal quit."""
        assert self.handler("quit") is False

    def test_exit_returns_false(self):
        """'exit' should signal quit."""
        assert self.handler("exit") is False

    def test_quit_uppercase_returns_false(self):
        """Quit commands are case-insensitive."""
        assert self.handler("QUIT") is False
        assert self.handler("Exit") is False
        assert self.handler("Q") is False

    def test_quit_with_surrounding_whitespace_returns_false(self):
        """Leading/trailing whitespace is stripped before matching."""
        assert self.handler("  quit  ") is False
        assert self.handler("\tq\n") is False

    def test_unknown_command_returns_true(self):
        """Unknown commands allow the editor to keep running."""
        assert self.handler("unknown") is True

    def test_empty_string_returns_true(self):
        """An empty string is not a quit command."""
        assert self.handler("") is True

    def test_whitespace_only_returns_true(self):
        """Whitespace-only input is not a quit command."""
        assert self.handler("   ") is True

    def test_partial_quit_word_returns_true(self):
        """Partial matches like 'qu' are not quit commands."""
        assert self.handler("qu") is True
        assert self.handler("exi") is True
