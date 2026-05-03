import curses

class Screen:
    def __init__(self, window, theme=None):
        
        # Store the raw curses window
        self.window = window
        
        # 1 Terminal Preferences (Only initialized on the root screen)
        if theme:
            try:
                curses.curs_set(1) # Show the cursor (0 = invisible, 1 = normal)
            except curses.error:
                pass
            self.window.keypad(True) # Enable Arrow keys F-keys so on
            self.window.nodelay(False) # Wait for user input (blocking)
            self.styles = self._setup_colors(theme)
        else:
            # Slices inherit styles from the parent instead of re-initializing
            self.styles = {}

    # Returns the (height, width) of the current window or slice
    def get_dimensions(self):
        return self.window.getmaxyx()

    # Returns a new Screen object that is a slice of the current one
    # This uses a recursive wrapper pattern so all methods remain available
    def create_slice(self, h, w, y, x):
        # derwin creates a sub-window relative to the parent coordinates
        sub_win = self.window.derwin(h, w, y, x)
        
        # Create a new Screen instance wrapping the sub-window
        new_slice = Screen(sub_win)
        
        # Share the parent's styles so colors and themes remain consistent
        new_slice.styles = self.styles 
        return new_slice

    # Initialize curses colors based on the provided theme configuration
    # Optimized to return a style map and only run once
    def _setup_colors(self, theme_dict):
        if not curses.has_colors():
            return {}

        curses.start_color()
        curses.use_default_colors()
        
        registered_styles = {}
        max_colors = curses.COLORS # Detection: 8, 16, or 256?
        max_pairs = curses.COLOR_PAIRS

        for i, (name, config) in enumerate(theme_dict.items(), start=1):
            # Check for terminal pair limits
            if i >= max_pairs:
                break
            
            preferred, fallback, bg_color = config
            
            # Select Foreground based on terminal capability (256 vs 8)
            fg = preferred if preferred < max_colors else fallback
            
            # Select Background (handle -1 as default terminal background)
            if bg_color == -1:
                bg = -1
            else:
                bg = bg_color if bg_color < max_colors else curses.COLOR_BLACK
            
            # Register the pair with curses
            curses.init_pair(i, fg, bg)
            # Store the attribute for high-level access
            registered_styles[name] = curses.color_pair(i)
        
        return registered_styles

    # Draws text at specific coordinates relative to the slice
    # Includes safety checks and slicing to prevent boundary crashes
    def draw_at_coords(self, y, x, text, style="TEXT"):
        h, w = self.get_dimensions()
        # Silent safety check to prevent crash on out-of-bounds
        if y >= h or x >= w or y < 0 or x < 0:
            return
        
        style_attr = self.styles.get(style, 0)
        try:
            # We slice the text to ensure it never exceeds the window width
            self.window.addstr(y, x, text[:w-x], style_attr)
        except curses.error:
            # Curses throws error if writing to the last character; we ignore it
            pass

    # The master draw function handling justification and row filling
    def draw(self, y, text, align="left", style="TEXT", fill_line=False):
        h, w = self.get_dimensions()
        text_len = len(text)
        style_attr = self.styles.get(style, 0)

        # Handle background filling for headers and footers
        if fill_line:
            if 0 <= y < h:
                # Fill the row background before placing text
                self.window.attron(style_attr)
                self.window.move(y, 0)
                self.window.hline(' ', w)
                self.window.attroff(style_attr)

        # Calculate X coordinate based on requested justification
        if align == "center":
            x = max(0, (w - text_len) // 2)
        elif align == "right":
            x = max(0, w - text_len)
        else:
            x = 0

        # Delegate to draw_at_coords for final rendering
        self.draw_at_coords(y, x, text, style)

    # Moves the physical terminal cursor safely
    def move_cursor(self, y, x):
        try:
            self.window.move(y, x)
        except curses.error:
            pass

    # Clears the current window buffer
    def clear(self):
        self.window.erase()

    # Logical refresh: updates the virtual window state
    def refresh(self):
        self.window.noutrefresh()

    # Physical refresh: pushes all logical updates to the hardware at once
    @staticmethod
    def update_physical():
        curses.doupdate()

    # Get a single keypress from the user
    def get_input(self):
        return self.window.getch()