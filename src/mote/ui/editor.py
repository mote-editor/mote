import curses

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

    def render(self, move_cursor=True):
        """Draw the buffer content to the slice."""
        self.slice.clear()
        height, width = self.slice.get_dimensions()
        
        # Recompute line number width from total line count
        if self.show_line_numbers:
            self.line_num_width = len(str(len(self.buffer.lines))) + 2
        else:
            self.line_num_width = 0

        # Update buffer screen dimensions (clamp to at least 1)
        text_width = max(1, width - self.line_num_width)
        self.buffer.resize_screen(height, text_width)
        
        selection_bounds = self.buffer.get_selection_bounds()

        # Render each visible line
        for row in range(height):
            line_idx = self.buffer.row_off + row
            if line_idx >= len(self.buffer.lines):
                break
            
            line = self.buffer.lines[line_idx]
            
            # Get visible portion of the line
            visible_line = line[self.buffer.col_off:self.buffer.col_off + text_width]
            
            # Draw line number if enabled
            if self.show_line_numbers:
                line_num_str = str(line_idx + 1).rjust(self.line_num_width - 2) + "│ "
                self.slice.draw_at_coords(row, 0, line_num_str)
                text_x = self.line_num_width
            else:
                text_x = 0

            if selection_bounds:
                self._draw_line_with_selection(
                    row,
                    line,
                    line_idx,
                    text_width,
                    text_x,
                    selection_bounds,
                )
            else:
                self.slice.draw_at_coords(row, text_x, visible_line)
        
        # Draw cursor
        if move_cursor:
            self._draw_cursor()

    def _draw_line_with_selection(
        self,
        row,
        line,
        line_idx,
        text_width,
        text_x,
        selection_bounds,
    ):
        start_y, start_x, end_y, end_x = selection_bounds

        if line_idx < start_y or line_idx > end_y:
            visible_line = line[self.buffer.col_off:self.buffer.col_off + text_width]
            self.slice.draw_at_coords(row, text_x, visible_line)
            return

        line_len = len(line)
        if start_y == end_y:
            sel_start = start_x
            sel_end = end_x
        elif line_idx == start_y:
            sel_start = start_x
            sel_end = line_len
        elif line_idx == end_y:
            sel_start = 0
            sel_end = end_x
        else:
            sel_start = 0
            sel_end = line_len

        sel_start = max(0, min(sel_start, line_len))
        sel_end = max(0, min(sel_end, line_len))

        vis_start = self.buffer.col_off
        vis_end = self.buffer.col_off + text_width
        visible_line = line[vis_start:vis_end]

        sel_vis_start = max(sel_start, vis_start)
        sel_vis_end = min(sel_end, vis_end)

        if sel_vis_start >= sel_vis_end:
            self.slice.draw_at_coords(row, text_x, visible_line)
            return

        pre_text = line[vis_start:sel_vis_start]
        sel_text = line[sel_vis_start:sel_vis_end]
        post_text = line[sel_vis_end:vis_end]

        if pre_text:
            self.slice.draw_at_coords(row, text_x, pre_text)
        if sel_text:
            self.slice.draw_at_coords(row, text_x + len(pre_text), sel_text, style="SELECTION")
        if post_text:
            self.slice.draw_at_coords(
                row,
                text_x + len(pre_text) + len(sel_text),
                post_text,
            )

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

    def move_cursor(self):
        """Move cursor to the editor position."""
        self._draw_cursor()

    def handle_key(self, key):
        """Process a key input and update buffer accordingly.
        
        Args:
            key: Key code from curses
        """
        shift_left = getattr(curses, "KEY_SLEFT", None)
        shift_right = getattr(curses, "KEY_SRIGHT", None)
        shift_up = getattr(curses, "KEY_SUP", None)
        shift_down = getattr(curses, "KEY_SDOWN", None)

        if key in (shift_left, shift_right, shift_up, shift_down):
            if not self.buffer.has_selection():
                self.buffer.start_selection()
            if key == shift_left:
                self.buffer.move_left()
            elif key == shift_right:
                self.buffer.move_right()
            elif key == shift_up:
                self.buffer.move_up()
            elif key == shift_down:
                self.buffer.move_down()
            return

        if key == ord('\n') or key == curses.KEY_ENTER:
            self.buffer.split_line()
        elif key == ord('\t'):
            for _ in range(4):
                self.buffer.insert_char(' ')
        elif key in (curses.KEY_BACKSPACE, ord('\b'), 127):  # Backspace
            self.buffer.delete_char()
        elif 32 <= key <= 126:  # Printable ASCII
            self.buffer.insert_char(chr(key))
        elif key == curses.KEY_UP:
            if self.buffer.has_selection():
                self.buffer.clear_selection()
            self.buffer.move_up()
        elif key == curses.KEY_DOWN:
            if self.buffer.has_selection():
                self.buffer.clear_selection()
            self.buffer.move_down()
        elif key == curses.KEY_LEFT:
            if self.buffer.has_selection():
                self.buffer.clear_selection()
            self.buffer.move_left()
        elif key == curses.KEY_RIGHT:
            if self.buffer.has_selection():
                self.buffer.clear_selection()
            self.buffer.move_right()

    def set_line_numbers(self, enabled):
        """Toggle line numbers display."""
        self.show_line_numbers = enabled
        if self.show_line_numbers:
            self.line_num_width = len(str(len(self.buffer.lines))) + 2
        else:
            self.line_num_width = 0
