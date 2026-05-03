import pytest
import curses
from unittest.mock import Mock, MagicMock, patch, call
from mote.ui_lib.screen import Screen


class TestScreenInitialization:
    """Test Screen initialization with and without theme."""
    
    def test_screen_initialization_with_theme(self):
        """Test creating a root screen with theme."""
        mock_window = Mock()
        theme = {"TEXT": (7, 0, -1)}
        
        with patch('curses.curs_set'):
            with patch.object(Screen, '_setup_colors', return_value={"TEXT": 0}):
                screen = Screen(mock_window, theme=theme)
        
        assert screen.window == mock_window
        assert screen.styles == {"TEXT": 0}
        mock_window.keypad.assert_called_once_with(True)
        mock_window.nodelay.assert_called_once_with(False)
    
    def test_screen_initialization_without_theme(self):
        """Test creating a slice screen without theme."""
        mock_window = Mock()
        screen = Screen(mock_window)
        
        assert screen.window == mock_window
        assert screen.styles == {}
        mock_window.keypad.assert_not_called()
        mock_window.nodelay.assert_not_called()
    
    def test_cursor_shown_on_root_screen(self):
        """Test that cursor is shown on root screen initialization."""
        mock_window = Mock()
        theme = {"TEXT": (7, 0, -1)}
        
        with patch('curses.curs_set') as mock_curs_set:
            with patch.object(Screen, '_setup_colors', return_value={"TEXT": 0}):
                Screen(mock_window, theme=theme)
        
        mock_curs_set.assert_called_once_with(1)


class TestDimensions:
    """Test screen dimension queries."""
    
    def test_get_dimensions(self):
        """Test getting current window dimensions."""
        mock_window = Mock()
        mock_window.getmaxyx.return_value = (24, 80)
        screen = Screen(mock_window)
        
        height, width = screen.get_dimensions()
        
        assert height == 24
        assert width == 80
        mock_window.getmaxyx.assert_called_once()


class TestCreateSlice:
    """Test creating screen slices."""
    
    def test_create_slice_basic(self):
        """Test creating a basic slice."""
        mock_window = Mock()
        mock_subwin = Mock()
        mock_window.derwin.return_value = mock_subwin
        
        parent_screen = Screen(mock_window)
        parent_screen.styles = {"TEXT": 0, "HEADER": 1}
        
        slice_screen = parent_screen.create_slice(10, 20, 5, 5)
        
        mock_window.derwin.assert_called_once_with(10, 20, 5, 5)
        assert slice_screen.window == mock_subwin
        assert slice_screen.styles == {"TEXT": 0, "HEADER": 1}
    
    def test_slice_inherits_parent_styles(self):
        """Test that slices inherit parent styles."""
        mock_window = Mock()
        mock_subwin = Mock()
        mock_window.derwin.return_value = mock_subwin
        
        parent_screen = Screen(mock_window)
        parent_screen.styles = {"CUSTOM": 42}
        
        slice_screen = parent_screen.create_slice(5, 5, 0, 0)
        
        assert slice_screen.styles is parent_screen.styles


class TestColorSetup:
    """Test color initialization and setup."""
    
    def test_setup_colors_no_colors_support(self):
        """Test setup when terminal doesn't support colors."""
        mock_window = Mock()
        theme = {"TEXT": (7, 0, -1)}
        
        with patch('curses.curs_set'):
            with patch('curses.has_colors', return_value=False):
                screen = Screen(mock_window, theme=theme)
        
        assert screen.styles == {}
    
    def test_setup_colors_with_theme(self):
        """Test color pair registration."""
        mock_window = Mock()
        theme = {
            "TEXT": (7, 0, -1),
            "HEADER": (3, 3, 4)
        }
        
        # Mock the _setup_colors to return a known dict
        with patch('curses.curs_set'):
            with patch.object(Screen, '_setup_colors') as mock_setup_colors:
                mock_setup_colors.return_value = {"TEXT": 256, "HEADER": 512}
                screen = Screen(mock_window, theme=theme)
        
        assert screen.styles == {"TEXT": 256, "HEADER": 512}
        mock_setup_colors.assert_called_once_with(theme)
    
    def test_setup_colors_respects_terminal_limits(self):
        """Test that _setup_colors respects terminal color pair limits."""
        mock_window = Mock()
        theme = {
            "TEXT": (7, 0, -1),
            "HEADER": (3, 3, 4),
            "FOOTER": (5, 5, -1),
        }

        with patch('curses.has_colors', return_value=True), \
             patch('curses.start_color'), \
             patch('curses.use_default_colors'), \
             patch('curses.COLORS', 8, create=True), \
             patch('curses.COLOR_PAIRS', 2, create=True), \
             patch('curses.init_pair') as mock_init_pair, \
             patch('curses.color_pair', side_effect=lambda i: i * 256):
            screen = Screen.__new__(Screen)
            screen.window = mock_window
            styles = screen._setup_colors(theme)

        # COLOR_PAIRS=2 means only i=1 is registered (loop breaks when i >= 2)
        assert len(styles) == 1
        assert mock_init_pair.call_count == 1


class TestDrawing:
    """Test drawing functions."""
    
    def test_draw_at_coords_basic(self):
        """Test drawing text at specific coordinates."""
        mock_window = Mock()
        mock_window.getmaxyx.return_value = (24, 80)
        screen = Screen(mock_window)
        screen.styles = {"TEXT": 0}
        
        screen.draw_at_coords(5, 10, "Hello", "TEXT")
        
        mock_window.addstr.assert_called_once_with(5, 10, "Hello", 0)
    
    def test_draw_at_coords_out_of_bounds_y(self):
        """Test that out-of-bounds Y coordinate is silently ignored."""
        mock_window = Mock()
        mock_window.getmaxyx.return_value = (24, 80)
        screen = Screen(mock_window)
        
        screen.draw_at_coords(30, 10, "Hello")
        
        mock_window.addstr.assert_not_called()
    
    def test_draw_at_coords_out_of_bounds_x(self):
        """Test that out-of-bounds X coordinate is silently ignored."""
        mock_window = Mock()
        mock_window.getmaxyx.return_value = (24, 80)
        screen = Screen(mock_window)
        
        screen.draw_at_coords(5, 90, "Hello")
        
        mock_window.addstr.assert_not_called()
    
    def test_draw_at_coords_negative_coordinates(self):
        """Test that negative coordinates are silently ignored."""
        mock_window = Mock()
        mock_window.getmaxyx.return_value = (24, 80)
        screen = Screen(mock_window)
        
        screen.draw_at_coords(-1, 10, "Hello")
        mock_window.addstr.assert_not_called()
        
        screen.draw_at_coords(5, -1, "Hello")
        mock_window.addstr.assert_not_called()
    
    def test_draw_at_coords_text_truncation(self):
        """Test that text is truncated to fit window width."""
        mock_window = Mock()
        mock_window.getmaxyx.return_value = (24, 10)
        screen = Screen(mock_window)
        screen.styles = {"TEXT": 0}
        
        screen.draw_at_coords(5, 5, "Hello World Long Text", "TEXT")
        
        # Text should be truncated to fit: 10 - 5 = 5 characters
        mock_window.addstr.assert_called_once_with(5, 5, "Hello", 0)
    
    def test_draw_at_coords_curses_error_handling(self):
        """Test that curses errors are silently caught."""
        mock_window = Mock()
        mock_window.getmaxyx.return_value = (24, 80)
        mock_window.addstr.side_effect = curses.error("Mock error")
        screen = Screen(mock_window)
        
        # Should not raise exception
        screen.draw_at_coords(5, 10, "Hello")
    
    def test_draw_left_aligned(self):
        """Test drawing text left-aligned."""
        mock_window = Mock()
        mock_window.getmaxyx.return_value = (24, 80)
        screen = Screen(mock_window)
        screen.styles = {"TEXT": 0}
        
        screen.draw(5, "Hello", align="left", style="TEXT")
        
        mock_window.addstr.assert_called_once_with(5, 0, "Hello", 0)
    
    def test_draw_center_aligned(self):
        """Test drawing text center-aligned."""
        mock_window = Mock()
        mock_window.getmaxyx.return_value = (24, 80)
        screen = Screen(mock_window)
        screen.styles = {"TEXT": 0}
        
        screen.draw(5, "Hello", align="center", style="TEXT")
        
        # Center of 80 is 40, text is 5 chars, so x = (80-5)//2 = 37
        call_args = mock_window.addstr.call_args
        assert call_args[0][1] == 37
    
    def test_draw_right_aligned(self):
        """Test drawing text right-aligned."""
        mock_window = Mock()
        mock_window.getmaxyx.return_value = (24, 80)
        screen = Screen(mock_window)
        screen.styles = {"TEXT": 0}
        
        screen.draw(5, "Hello", align="right", style="TEXT")
        
        # Right align: x = 80 - 5 = 75
        call_args = mock_window.addstr.call_args
        assert call_args[0][1] == 75
    
    def test_draw_with_fill_line(self):
        """Test drawing with line filling."""
        mock_window = Mock()
        mock_window.getmaxyx.return_value = (24, 80)
        screen = Screen(mock_window)
        screen.styles = {"HEADER": 1}
        
        screen.draw(5, "Title", align="left", style="HEADER", fill_line=True)
        
        # Should call attron, move, hline, attroff
        mock_window.attron.assert_called_once_with(1)
        mock_window.move.assert_called_once_with(5, 0)
        mock_window.hline.assert_called_once_with(' ', 80)
        mock_window.attroff.assert_called_once_with(1)
    
    def test_draw_uses_unknown_style_default(self):
        """Test that unknown style defaults to 0."""
        mock_window = Mock()
        mock_window.getmaxyx.return_value = (24, 80)
        screen = Screen(mock_window)
        screen.styles = {"TEXT": 0}
        
        screen.draw(5, "Hello", style="UNKNOWN")
        
        # Should use 0 as default for style attribute
        call_args = mock_window.addstr.call_args
        assert call_args[0][3] == 0  # style_attr argument


class TestCursorManagement:
    """Test cursor management functions."""
    
    def test_move_cursor(self):
        """Test moving the cursor."""
        mock_window = Mock()
        screen = Screen(mock_window)
        
        screen.move_cursor(10, 20)
        
        mock_window.move.assert_called_once_with(10, 20)
    
    def test_move_cursor_error_handling(self):
        """Test that cursor move errors are silently caught."""
        mock_window = Mock()
        mock_window.move.side_effect = curses.error("Mock error")
        screen = Screen(mock_window)
        
        # Should not raise exception
        screen.move_cursor(10, 20)


class TestWindowManagement:
    """Test window clearing and refresh operations."""
    
    def test_clear(self):
        """Test clearing the window."""
        mock_window = Mock()
        screen = Screen(mock_window)
        
        screen.clear()
        
        mock_window.erase.assert_called_once()
    
    def test_refresh_logical(self):
        """Test logical refresh."""
        mock_window = Mock()
        screen = Screen(mock_window)
        
        screen.refresh()
        
        mock_window.noutrefresh.assert_called_once()
    
    def test_update_physical(self):
        """Test physical update."""
        with patch('curses.doupdate') as mock_doupdate:
            Screen.update_physical()
        
        mock_doupdate.assert_called_once()


class TestInput:
    """Test input handling."""
    
    def test_get_input(self):
        """Test getting user input."""
        mock_window = Mock()
        mock_window.getch.return_value = ord('a')
        screen = Screen(mock_window)
        
        key = screen.get_input()
        
        assert key == ord('a')
        mock_window.getch.assert_called_once()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_text_drawing(self):
        """Test drawing empty text."""
        mock_window = Mock()
        mock_window.getmaxyx.return_value = (24, 80)
        screen = Screen(mock_window)
        screen.styles = {"TEXT": 0}
        
        screen.draw_at_coords(5, 10, "", "TEXT")
        
        mock_window.addstr.assert_called_once_with(5, 10, "", 0)
    
    def test_very_long_text(self):
        """Test drawing very long text."""
        mock_window = Mock()
        mock_window.getmaxyx.return_value = (24, 80)
        screen = Screen(mock_window)
        screen.styles = {"TEXT": 0}
        
        long_text = "A" * 1000
        screen.draw_at_coords(5, 10, long_text, "TEXT")
        
        # Should be truncated to fit window
        call_args = mock_window.addstr.call_args
        assert len(call_args[0][2]) == 70  # 80 - 10
    
    def test_window_at_boundary(self):
        """Test drawing at window boundary."""
        mock_window = Mock()
        mock_window.getmaxyx.return_value = (24, 80)
        screen = Screen(mock_window)
        screen.styles = {"TEXT": 0}
        
        # Draw at last valid position
        screen.draw_at_coords(23, 79, "X", "TEXT")
        
        mock_window.addstr.assert_called_once()
