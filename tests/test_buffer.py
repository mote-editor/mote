import pytest
from mote.core.buffer import Buffer


class TestBufferInitialization:
    def test_empty_buffer_initialization(self):
        """Test creating an empty buffer"""
        buf = Buffer()
        assert buf.lines == [""]
        assert buf.cx == 0
        assert buf.cy == 0
        assert buf.dirty is False

    def test_buffer_with_text(self):
        """Test creating a buffer with initial text"""
        text = "line 1\nline 2\nline 3"
        buf = Buffer(text)
        assert buf.lines == ["line 1", "line 2", "line 3"]
        assert len(buf.lines) == 3

    def test_buffer_custom_dimensions(self):
        """Test buffer with custom screen dimensions"""
        buf = Buffer(screen_height=30, screen_width=100)
        assert buf.screen_height == 30
        assert buf.screen_width == 100

    def test_effective_cursor_initialization(self):
        """Test effective cursor is initialized"""
        buf = Buffer()
        assert buf._effective_cx == 0


class TestCursorMovement:
    def test_move_right(self):
        """Test moving cursor right"""
        buf = Buffer("hello")
        buf.move_right()
        assert buf.cx == 1
        buf.move_right()
        assert buf.cx == 2

    def test_move_left(self):
        """Test moving cursor left"""
        buf = Buffer("hello")
        buf.cx = 2
        buf._effective_cx = 2
        buf.move_left()
        assert buf.cx == 1

    def test_move_up(self):
        """Test moving cursor up"""
        buf = Buffer("line 1\nline 2\nline 3")
        buf.cy = 2
        buf.move_up()
        assert buf.cy == 1
        buf.move_up()
        assert buf.cy == 0

    def test_move_down(self):
        """Test moving cursor down"""
        buf = Buffer("line 1\nline 2\nline 3")
        buf.move_down()
        assert buf.cy == 1
        buf.move_down()
        assert buf.cy == 2

    def test_move_right_at_end_of_line_moves_to_next_line(self):
        """Test moving right at end of line wraps to next line"""
        buf = Buffer("hi\nbye")
        buf.cx = 2  # end of first line
        buf._effective_cx = 2
        buf.move_right()
        assert buf.cy == 1
        assert buf.cx == 0

    def test_move_left_at_start_of_line_moves_to_previous(self):
        """Test moving left at start of line wraps to previous line"""
        buf = Buffer("hi\nbye")
        buf.cy = 1
        buf.cx = 0
        buf._effective_cx = 0
        buf.move_left()
        assert buf.cy == 0
        assert buf.cx == 2

    def test_effective_cursor_on_vertical_movement(self):
        """Test effective cursor maintains column on vertical movement"""
        buf = Buffer("hello\nhi\nworld")
        buf.cx = 4
        buf._effective_cx = 4
        buf.move_down()  # Move from "hello" to "hi"
        # Should clamp to line length (2)
        assert buf.cx == 2
        buf.move_down()  # Move from "hi" to "world"
        # Should restore to effective cursor position (4)
        assert buf.cx == 4

    def test_move_down_boundary(self):
        """Test move down doesn't go past end of buffer"""
        buf = Buffer("line 1\nline 2")
        buf.cy = 1
        buf.move_down()
        assert buf.cy == 1  # Should stay at last line


class TestTextInsertion:
    def test_insert_char_at_beginning(self):
        """Test inserting character at beginning of line"""
        buf = Buffer("hello")
        buf.insert_char("x")
        assert buf.lines[0] == "xhello"
        assert buf.cx == 1

    def test_insert_char_in_middle(self):
        """Test inserting character in middle of line"""
        buf = Buffer("heo")
        buf.cx = 2
        buf.insert_char("l")
        assert buf.lines[0] == "helo"
        assert buf.cx == 3

    def test_insert_char_marks_dirty(self):
        """Test that inserting marks buffer as dirty"""
        buf = Buffer()
        assert buf.dirty is False
        buf.insert_char("a")
        assert buf.dirty is True

    def test_insert_with_selection_replaces(self):
        """Test inserting with selection replaces the selection"""
        buf = Buffer("hello")
        buf.start_selection()
        buf.cx = 3
        buf.insert_char("x")
        assert buf.lines[0] == "xlo"
        assert buf.cx == 1
        assert buf.has_selection() is False


class TestTextDeletion:
    def test_delete_char_before_cursor(self):
        """Test deleting character before cursor"""
        buf = Buffer("hello")
        buf.cx = 3
        buf.delete_char()
        assert buf.lines[0] == "helo"
        assert buf.cx == 2

    def test_delete_char_at_start_merges_lines(self):
        """Test deleting at start of line merges with previous"""
        buf = Buffer("hi\nbye")
        buf.cy = 1
        buf.cx = 0
        buf.delete_char()
        assert buf.lines == ["hibye"]
        assert buf.cy == 0
        assert buf.cx == 2

    def test_delete_char_marks_dirty(self):
        """Test that deleting marks buffer as dirty"""
        buf = Buffer("hello")
        buf.cx = 1
        assert buf.dirty is False
        buf.delete_char()
        assert buf.dirty is True

    def test_delete_with_selection_deletes_selection(self):
        """Test deleting with selection removes the selection"""
        buf = Buffer("hello")
        buf.start_selection()
        buf.cx = 3
        buf.delete_char()
        assert buf.lines[0] == "lo"
        assert buf.cx == 0
        assert buf.has_selection() is False


class TestLineSplitting:
    def test_split_line_at_beginning(self):
        """Test splitting line at the beginning"""
        buf = Buffer("hello")
        buf.cx = 0
        buf.split_line()
        assert buf.lines == ["", "hello"]
        assert buf.cy == 1
        assert buf.cx == 0

    def test_split_line_in_middle(self):
        """Test splitting line in the middle"""
        buf = Buffer("hello")
        buf.cx = 2
        buf.split_line()
        assert buf.lines == ["he", "llo"]
        assert buf.cy == 1
        assert buf.cx == 0

    def test_split_line_at_end(self):
        """Test splitting line at the end"""
        buf = Buffer("hello")
        buf.cx = 5
        buf.split_line()
        assert buf.lines == ["hello", ""]
        assert buf.cy == 1
        assert buf.cx == 0

    def test_split_line_with_selection(self):
        """Test splitting line with selection removes selection"""
        buf = Buffer("hello")
        buf.start_selection()
        buf.cx = 3
        buf.split_line()
        assert buf.lines == ["", "lo"]
        assert buf.has_selection() is False


class TestSelection:
    def test_start_selection(self):
        """Test starting a selection"""
        buf = Buffer("hello")
        buf.cx = 2
        buf.cy = 0
        buf.start_selection()
        assert buf.select_x == 2
        assert buf.select_y == 0

    def test_clear_selection(self):
        """Test clearing a selection"""
        buf = Buffer("hello")
        buf.start_selection()
        assert buf.has_selection() is True
        buf.clear_selection()
        assert buf.has_selection() is False

    def test_selection_bounds_single_line(self):
        """Test getting selection bounds on single line"""
        buf = Buffer("hello")
        buf.start_selection()
        buf.cx = 3
        bounds = buf.get_selection_bounds()
        assert bounds == (0, 0, 0, 3)

    def test_selection_bounds_reversed(self):
        """Test selection bounds are normalized when reversed"""
        buf = Buffer("hello")
        buf.cx = 3
        buf.cy = 0
        buf.start_selection()
        buf.cx = 1
        bounds = buf.get_selection_bounds()
        # Should be normalized to start -> end
        assert bounds == (0, 1, 0, 3)

    def test_delete_selection_single_line(self):
        """Test deleting selection on single line"""
        buf = Buffer("hello")
        buf.start_selection()
        buf.cx = 3
        buf.delete_selection()
        assert buf.lines[0] == "lo"
        assert buf.cx == 0

    def test_delete_selection_multiline(self):
        """Test deleting selection across multiple lines"""
        buf = Buffer("hello\nworld\nfoo")
        buf.start_selection()
        buf.cy = 2
        buf.cx = 1
        buf.delete_selection()
        assert buf.lines == ["oo"]


class TestScrolling:
    def test_vertical_scroll_cursor_below(self):
        """Test vertical scrolling when cursor goes below"""
        buf = Buffer(screen_height=5)
        for i in range(10):
            buf.lines.append(f"line {i}")
        buf.cy = 8
        buf._check_scroll()
        assert buf.row_off == 4  # cy - height + 1 = 8 - 5 + 1

    def test_vertical_scroll_cursor_above(self):
        """Test vertical scrolling when cursor goes above"""
        buf = Buffer(screen_height=5)
        buf.row_off = 5
        buf.cy = 2
        buf._check_scroll()
        assert buf.row_off == 2

    def test_horizontal_scroll_cursor_left(self):
        """Test horizontal scrolling when cursor goes left"""
        buf = Buffer(screen_width=10)
        buf.col_off = 5
        buf.cx = 2
        buf._check_scroll()
        assert buf.col_off == 2

    def test_horizontal_scroll_cursor_right(self):
        """Test horizontal scrolling when cursor goes right"""
        buf = Buffer(screen_width=10)
        buf.cx = 15
        buf._check_scroll()
        assert buf.col_off == 6  # cx - width + 1 = 15 - 10 + 1

    def test_get_visible_lines_vertical(self):
        """Test getting visible lines with vertical scrolling"""
        buf = Buffer("line 0\nline 1\nline 2\nline 3\nline 4", screen_height=3)
        buf.row_off = 1
        visible = buf.get_visible_lines(3)
        assert visible == ["line 1", "line 2", "line 3"]

    def test_get_visible_lines_horizontal(self):
        """Test getting visible lines with horizontal scrolling"""
        buf = Buffer("0123456789ABCDEF", screen_width=5)
        buf.col_off = 3
        visible = buf.get_visible_lines(1)
        assert visible == ["34567"]

    def test_get_visible_lines_both_scrolls(self):
        """Test getting visible lines with both scrolls"""
        text = "0123456789\n0123456789\n0123456789"
        buf = Buffer(text, screen_height=2, screen_width=5)
        buf.row_off = 1
        buf.col_off = 3
        visible = buf.get_visible_lines(2)
        assert visible == ["34567", "34567"]


class TestUtilities:
    def test_get_full_text(self):
        """Test getting full text"""
        text = "line 1\nline 2\nline 3"
        buf = Buffer(text)
        assert buf.get_full_text() == text

    def test_get_line_default_current(self):
        """Test getting current line by default"""
        buf = Buffer("line 1\nline 2")
        buf.cy = 1
        assert buf.get_line() == "line 2"

    def test_get_line_specific_index(self):
        """Test getting specific line by index"""
        buf = Buffer("line 1\nline 2\nline 3")
        assert buf.get_line(1) == "line 2"

    def test_goto_line(self):
        """Test goto line function"""
        buf = Buffer("1\n2\n3\n4\n5")
        buf.goto_line(3)
        assert buf.cy == 2
        assert buf.cx == 0
        assert buf._effective_cx == 0

    def test_goto_line_clamped_below(self):
        """Test goto line clamps to valid range (below)"""
        buf = Buffer("1\n2\n3")
        buf.goto_line(0)
        assert buf.cy == 0

    def test_goto_line_clamped_above(self):
        """Test goto line clamps to valid range (above)"""
        buf = Buffer("1\n2\n3")
        buf.goto_line(100)
        assert buf.cy == 2

    def test_resize_screen(self):
        """Test resizing screen"""
        buf = Buffer(screen_height=24, screen_width=80)
        buf.resize_screen(30, 100)
        assert buf.screen_height == 30
        assert buf.screen_width == 100


class TestComplexScenarios:
    def test_typing_a_line(self):
        """Test typing a complete line"""
        buf = Buffer()
        for char in "hello":
            buf.insert_char(char)
        assert buf.lines[0] == "hello"
        assert buf.cx == 5

    def test_multiple_lines_navigation(self):
        """Test navigating through multiple lines"""
        buf = Buffer("hello\nworld\nfoo")
        buf.move_down()
        assert buf.cy == 1
        buf.move_down()
        assert buf.cy == 2
        buf.move_up()
        assert buf.cy == 1

    def test_select_and_replace_text(self):
        """Test selecting text and replacing it"""
        buf = Buffer("hello world")
        buf.cx = 6
        buf.start_selection()
        buf.cx = 11
        buf.insert_char("!")
        assert buf.lines[0] == "hello !"

    def test_split_and_continue_typing(self):
        """Test splitting a line and continuing to type"""
        buf = Buffer("helloworld")
        buf.cx = 5
        buf.split_line()
        assert buf.lines == ["hello", "world"]
        buf.insert_char("_")
        assert buf.lines == ["hello", "_world"]

    def test_large_document_navigation(self):
        """Test navigation in a large document"""
        lines = [f"line {i}" for i in range(100)]
        buf = Buffer("\n".join(lines), screen_height=10)
        buf.goto_line(50)
        assert buf.cy == 49
        buf.move_down()
        assert buf.cy == 50

    def test_horizontal_scrolling_with_long_line(self):
        """Test horizontal scrolling with very long line"""
        long_line = "a" * 200
        buf = Buffer(long_line, screen_width=20)
        buf.cx = 150
        buf._check_scroll()
        assert buf.col_off > 0
        visible = buf.get_visible_lines(1)
        assert len(visible[0]) <= 20
