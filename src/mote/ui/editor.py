from mote.core.buffer import Buffer


class Editor:
    """Text editor for the middle slice of the screen layout.
    
    Renders buffer content with optional line numbers and manages input.
    """

    def __init__(self, screen_slice, buffer=None, show_line_numbers=False):
        """Initialize editor with a screen slice and optional buffer.
        
        Args:
            screen_slice: Screen object representing the middle slice
            buffer: Buffer object (creates new one if not provided)
            show_line_numbers: Whether to display line numbers column
        """
        self.slice = screen_slice
        self.show_line_numbers = show_line_numbers
        
        # Get dimensions and create buffer if needed
        height, width = self.slice.get_dimensions()
        self.buffer = buffer or Buffer(screen_height=height, screen_width=width)
        
        # Calculate available width for text if line numbers are shown
        self.line_num_width = 0
        if self.show_line_numbers:
            # Width needed for line numbers (e.g., "1234: " for up to 4 digit line numbers)
            self.line_num_width = len(str(len(self.buffer.lines))) + 2

    def render(self):
        """Draw the buffer content to the slice."""
        self.slice.clear()
        height, width = self.slice.get_dimensions()
        
        # Recompute line number width from total line count
        if self.show_line_numbers:
            self.line_num_width = len(str(len(self.buffer.lines))) + 2
        else:
            self.line_num_width = 0

        # Update buffer screen dimensions
        self.buffer.resize_screen(height, width - self.line_num_width)
        
        # Render each visible line
        for row in range(height):
            line_idx = self.buffer.row_off + row
            if line_idx >= len(self.buffer.lines):
                break
            
            line = self.buffer.lines[line_idx]
            
            # Get visible portion of the line
            visible_line = line[self.buffer.col_off:self.buffer.col_off + (width - self.line_num_width)]
            
            # Draw line number if enabled
            if self.show_line_numbers:
                line_num_str = str(line_idx + 1).rjust(self.line_num_width - 2) + "│ "
                self.slice.draw_at_coords(row, 0, line_num_str)
                self.slice.draw_at_coords(row, self.line_num_width, visible_line)
            else:
                self.slice.draw_at_coords(row, 0, visible_line)
        
        # Draw cursor
        self._draw_cursor()

    def _draw_cursor(self):
        """Position cursor at buffer cursor location."""
        height, width = self.slice.get_dimensions()
        
        # Calculate visible cursor position
        cursor_y = self.buffer.cy - self.buffer.row_off
        cursor_x = self.buffer.cx - self.buffer.col_off + self.line_num_width
        
        # Clamp cursor to visible area
        cursor_y = max(0, min(cursor_y, height - 1))
        cursor_x = max(0, min(cursor_x, width - 1))
        
        self.slice.move_cursor(cursor_y, cursor_x)

    def handle_key(self, key):
        """Process a key input and update buffer accordingly.
        
        Args:
            key: Key code from curses
        """
        if key == ord('\n'):
            self.buffer.split_line()
        elif key in (ord('\b'), 8, 127, 263):  # Backspace
            self.buffer.delete_char()
        elif 32 <= key <= 126:  # Printable ASCII
            self.buffer.insert_char(chr(key))
        elif key == 259:  # Up arrow
            self.buffer.move_up()
        elif key == 258:  # Down arrow
            self.buffer.move_down()
        elif key == 260:  # Left arrow
            self.buffer.move_left()
        elif key == 261:  # Right arrow
            self.buffer.move_right()

    def set_line_numbers(self, enabled):
        """Toggle line numbers display."""
        self.show_line_numbers = enabled
        if self.show_line_numbers:
            self.line_num_width = len(str(len(self.buffer.lines))) + 2
        else:
            self.line_num_width = 0
