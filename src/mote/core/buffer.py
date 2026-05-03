import re


class Buffer:
    # Init func, takes text arg for loading text, defaults to empty string for new buffer
    def __init__(self, text="", screen_height=24, screen_width=80):
        # Store text as lots of lines, split by newlines if text is given in the args
        self.lines = text.splitlines() if text else [""]
        # Cursor x and y positions
        self.cx = 0
        self.cy = 0
        # Effective cursor x position - tracks desired column when moving vertically
        self._effective_cx = 0
        # Selection starting coords
        self.select_x = None
        self.select_y = None
        # Check if the buffer has unsaved changes
        self.dirty = False
        # Screen height for calculating visible lines and scrolling
        self.screen_height = screen_height
        # Screen width for calculating visible columns and horizontal scrolling
        self.screen_width = screen_width
        # Row offset for vertical scrolling
        self.row_off = 0
        # Column offset for horizontal scrolling
        self.col_off = 0
    
    def resize_screen(self, new_height, new_width=None):
        self.screen_height = new_height
        if new_width is not None:
            self.screen_width = new_width
        self._check_scroll()

    # Get line func, takes index arg for which line to get, defaults to current cursor y position
    def get_line(self, index=None):
        # Set the index to given, or cursor y if not given
        idx = index if index is not None else self.cy
        return self.lines[idx]

    # Insert char func, takes char arg for which character to insert at the cursor position
    def insert_char(self, char):
        # Mark buffer as dirty since its changing it
        self.dirty = True
        # If there is a selection, delete it first and replace with char
        if self.has_selection():
            self.delete_selection()
        # Get the current line
        line = self.get_line()
        # Insert char at x position in the line in the buffer
        self.lines[self.cy] = line[:self.cx] + char + line[self.cx:]
        # Move the cursor right by 1
        self.cx += 1
        # Reset effective cursor to actual cursor position
        self._effective_cx = self.cx
        self._check_scroll()

    def delete_char(self):
        # If there is a selection, delete it
        if self.has_selection():
            self.delete_selection()
            return
        # If cursor x is greater than 0, delete char before cursor and move left
        if self.cx > 0:
            self.dirty = True
            line = self.get_line()
            self.lines[self.cy] = line[:self.cx - 1] + line[self.cx:]
            self.cx -= 1
        elif self.cy > 0:
            # Merge current line with previous
            self.dirty = True
            prev_len = len(self.lines[self.cy - 1])
            current_line = self.lines.pop(self.cy)
            self.lines[self.cy - 1] += current_line
            self.cy -= 1
            self.cx = prev_len
        else:
            # No-op: cursor is at the very start of the buffer
            return
        # Reset effective cursor to actual cursor position
        self._effective_cx = self.cx
        self._check_scroll()

    # Split line func, splits the current line at the cursor position into two lines
    def split_line(self):
        # Mark buffer as dirty since its changing it
        self.dirty = True
        # If there is a selection, delete it first
        if self.has_selection():
            self.delete_selection()
        # Get the current line
        line = self.get_line()
        # Split the line at the cursor x position, keep the left part in the current line and insert the right part as a new line below
        self.lines[self.cy] = line[:self.cx]
        # Insert the right part as a new line below the current line
        self.lines.insert(self.cy + 1, line[self.cx:])
        # Move the cursor down to the new line and reset x to 0
        self.cy += 1
        self.cx = 0
        # Reset effective cursor to actual cursor position
        self._effective_cx = self.cx
        self._check_scroll()

    # Start selection func, sets the selection starting coordinates to the current cursor position
    def start_selection(self):
        self.select_x = self.cx
        self.select_y = self.cy
    
    # Clear selection func, clears the selection starting coordinates
    def clear_selection(self):
        self.select_x = None
        self.select_y = None
    
    # Check if there is an active selection
    def has_selection(self):
        return self.select_x is not None and self.select_y is not None
    
    # Get selection bounds, returns (start_y, start_x, end_y, end_x) sorted from start to end
    def get_selection_bounds(self):
        if not self.has_selection():
            return None
        
        start_y, start_x = self.select_y, self.select_x
        end_y, end_x = self.cy, self.cx
        
        # Sort so start is always before end
        if start_y > end_y or (start_y == end_y and start_x > end_x):
            start_y, start_x, end_y, end_x = end_y, end_x, start_y, start_x
        
        return (start_y, start_x, end_y, end_x)
    
    # Delete text within selection bounds
    def delete_selection(self):
        bounds = self.get_selection_bounds()
        if not bounds:
            return
        
        self.dirty = True
        start_y, start_x, end_y, end_x = bounds
        
        if start_y == end_y:
            # Single line selection - just remove the text
            line = self.lines[start_y]
            self.lines[start_y] = line[:start_x] + line[end_x:]
        else:
            # Multi-line selection
            # Keep the part before selection on start line
            start_line = self.lines[start_y][:start_x]
            # Keep the part after selection on end line
            end_line = self.lines[end_y][end_x:]
            # Merge them
            self.lines[start_y] = start_line + end_line
            # Delete the lines in between
            del self.lines[start_y + 1:end_y + 1]
        
        # Move cursor to start of selection and clear selection
        self.cy = start_y
        self.cx = start_x
        # Reset effective cursor to actual cursor position
        self._effective_cx = self.cx
        self.clear_selection()
        self._check_scroll()
    
    def _check_scroll(self):
        # Vertical scrolling: If cursor moved above the top of the screen
        if self.cy < self.row_off:
            self.row_off = self.cy
        
        # If cursor moved below the bottom of the screen
        elif self.cy >= self.row_off + self.screen_height:
            self.row_off = self.cy - self.screen_height + 1
        
        # Horizontal scrolling: If cursor moved left of the visible area
        if self.cx < self.col_off:
            self.col_off = self.cx
        
        # If cursor moved right of the visible area
        elif self.cx >= self.col_off + self.screen_width:
            self.col_off = self.cx - self.screen_width + 1

    # Move cursor up one line, using effective cursor position
    def move_up(self):
        if self.cy > 0:
            self.cy -= 1
            # Set cursor x to effective cursor position, clamped to line length
            self.cx = min(self._effective_cx, len(self.lines[self.cy]))
            self._check_scroll()
    
    # Move cursor down one line, using effective cursor position
    def move_down(self):
        if self.cy < len(self.lines) - 1:
            self.cy += 1
            # Set cursor x to effective cursor position, clamped to line length
            self.cx = min(self._effective_cx, len(self.lines[self.cy]))
            self._check_scroll()
    
    # Move cursor left, resetting effective cursor
    def move_left(self):
        if self.cx > 0:
            self.cx -= 1
            self._effective_cx = self.cx
        elif self.cy > 0:
            self.cy -= 1
            self.cx = len(self.lines[self.cy])
            self._effective_cx = self.cx
        self._check_scroll()
    
    # Move cursor right, resetting effective cursor
    def move_right(self):
        line = self.get_line()
        if self.cx < len(line):
            self.cx += 1
            self._effective_cx = self.cx
        elif self.cy < len(self.lines) - 1:
            self.cy += 1
            self.cx = 0
            self._effective_cx = self.cx
        self._check_scroll()

    # Get full text func, returns the full text of the buffer by joining all lines with newlines
    def get_full_text(self):
        return "\n".join(self.lines)
    
    # Get visible range func, takes screen_height to determine which lines are visible based on the current row offset, returns (start, end) line indices
    def get_visible_range(self, screen_height):
        start = self.row_off
        # Don't try to show more lines than the buffer actually has
        end = min(len(self.lines), self.row_off + screen_height)
        return start, end
    
    # Get visible lines func, takes screen_height to determine which lines to return for rendering
    def get_visible_lines(self, screen_height, screen_width=None):
        if screen_width is None:
            screen_width = self.screen_width
        start, end = self.get_visible_range(screen_height)
        lines = self.lines[start:end]
        # Apply horizontal scrolling by slicing each line based on col_off
        scrolled_lines = [line[self.col_off:self.col_off + screen_width] for line in lines]
        return scrolled_lines
    
    # Go to line func, moves cursor to specified line number (1-indexed)
    def goto_line(self, line_num):
        # Convert to 0-indexed and clamp to valid range
        line_index = max(0, min(line_num - 1, len(self.lines) - 1))
        self.cy = line_index
        # Move cursor to beginning of line and reset effective cursor
        self.cx = 0
        self._effective_cx = 0
        self._check_scroll()
    
    # Find all occurrences of a pattern in the buffer, takes pattern arg for text or regex to search for, and use_regex boolean to determine how to interpret the pattern, returns list of tuples (start_line, start_col, end_line, end_col) for each occurrence found
    def find(self, pattern, use_regex=False):
        occurrences = []
        full_text = self.get_full_text()
        
        try:
            if use_regex:
                # Use regex matching
                for match in re.finditer(pattern, full_text):
                    start_pos = match.start()
                    end_pos = match.end()
                    # Convert absolute positions to line and column
                    start_line, start_col = self._pos_to_line_col(start_pos)
                    end_line, end_col = self._pos_to_line_col(end_pos)
                    occurrences.append((start_line, start_col, end_line, end_col))
            else:
                # Use literal text matching
                search_pos = 0
                while True:
                    pos = full_text.find(pattern, search_pos)
                    if pos == -1:
                        break
                    start_line, start_col = self._pos_to_line_col(pos)
                    end_line, end_col = self._pos_to_line_col(pos + len(pattern))
                    occurrences.append((start_line, start_col, end_line, end_col))
                    search_pos = pos + 1
        except re.error:
            # Invalid regex pattern
            return []
        
        return occurrences
    
    # Replace all occurrences of a pattern, takes pattern arg for text or regex to search for, replacement arg for text to replace with, and use_regex boolean to determine how to interpret the pattern, returns number of replacements made
    def replace_all(self, pattern, replacement, use_regex=False):
        full_text = self.get_full_text()
        count = 0
        
        try:
            if use_regex:
                new_text, count = re.subn(pattern, replacement, full_text)
            else:
                count = full_text.count(pattern)
                new_text = full_text.replace(pattern, replacement)
        except re.error:
            return 0
        
        if new_text != full_text:
            self.dirty = True
            self.lines = new_text.splitlines() if new_text else [""]
            self.cy = min(self.cy, len(self.lines) - 1)
            self.cx = min(self.cx, len(self.lines[self.cy]))
            self._effective_cx = self.cx
            self._check_scroll()
        return count
    
    # Replace at a specific location, takes location tuple (start_line, start_col, end_line, end_col) from find() and replacement text, returns True if replacement was made
    def replace_specific(self, location, replacement):
        if not isinstance(location, tuple) or len(location) != 4:
            return False
        
        start_line, start_col, end_line, end_col = location
        
        # Validate bounds
        if start_line < 0 or start_line >= len(self.lines):
            return False
        if end_line < 0 or end_line >= len(self.lines):
            return False
        if start_line > end_line:
            return False
        if start_col < 0 or start_col > len(self.lines[start_line]):
            return False
        if end_col < 0 or end_col > len(self.lines[end_line]):
            return False
        if start_line == end_line and start_col > end_col:
            return False
        
        self.dirty = True
        
        if start_line == end_line:
            # Single line replacement
            line = self.lines[start_line]
            self.lines[start_line] = line[:start_col] + replacement + line[end_col:]
        else:
            # Multi-line replacement
            # Keep the part before the match on the start line
            start_line_text = self.lines[start_line][:start_col]
            # Keep the part after the match on the end line
            end_line_text = self.lines[end_line][end_col:]
            # Combine with replacement
            new_text = start_line_text + replacement + end_line_text
            # Replace the affected lines
            self.lines[start_line] = new_text
            # Delete the lines in between
            del self.lines[start_line + 1:end_line + 1]
        
        return True
    
    # Helper function to convert absolute position in full text to line and column
    def _pos_to_line_col(self, pos):
        """Convert absolute position in full text to (line, col)."""
        full_text = self.get_full_text()
        line = 0
        current_pos = 0
        
        for i, line_text in enumerate(self.lines):
            line_length = len(line_text) + 1  # +1 for newline
            if current_pos + line_length > pos:
                col = pos - current_pos
                return i, col
            current_pos += line_length
        
        # Position is at the end
        return len(self.lines) - 1, len(self.lines[-1])