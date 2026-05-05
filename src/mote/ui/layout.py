import curses
from mote.ui_lib.screen import Screen


class ScreenLayout:
    """Screen layout with top, middle, and bottom slices.
    
    Top and bottom are fixed at 1 line each, middle fills the rest.
    Handles input focus switching and command dispatch.
    """

    def __init__(self, window, theme=None, command_handler=None):
        """Initialize layout with the given window and optional theme."""
        # Create the main screen
        self.main_screen = Screen(window, theme)
        
        # Get total dimensions
        height, width = self.main_screen.get_dimensions()
        
        # Create the three slices
        # Top slice: 1 line at position (0, 0)
        self.top = self.main_screen.create_slice(1, width, 0, 0)
        
        # Bottom slice: 1 line at position (height-1, 0)
        self.bottom = self.main_screen.create_slice(1, width, height - 1, 0)
        
        # Middle slice: fills the remaining space
        # Starts at y=1 and has height of (total_height - 2)
        middle_height = max(1, height - 2)
        self.middle = self.main_screen.create_slice(middle_height, width, 1, 0)
        
        # Input state management
        self.input_focus = "middle"  # "middle" or "bottom"
        self.command_handler = command_handler

    def get_top_slice(self):
        """Get the top slice (1 line)."""
        return self.top

    def get_middle_slice(self):
        """Get the middle slice (fills remaining space)."""
        return self.middle

    def get_bottom_slice(self):
        """Get the bottom slice (1 line)."""
        return self.bottom

    def refresh_all(self):
        """Refresh all slices and update the physical display."""
        self.top.refresh()
        self.middle.refresh()
        self.bottom.refresh()
        Screen.update_physical()

    def clear_all(self):
        """Clear all slices."""
        self.top.clear()
        self.middle.clear()
        self.bottom.clear()

    def _is_ctrl_key(self, key):
        """Check if key is a ctrl combination (1-26)."""
        # Ctrl+A = 1, Ctrl+B = 2, ... Ctrl+Z = 26
        return 1 <= key <= 26

    def _get_ctrl_char(self, key):
        """Convert ctrl key code (1-26) to char (a-z)."""
        # Ctrl+A = 1 -> 'a', Ctrl+B = 2 -> 'b', etc.
        return chr(ord('a') + key - 1)

    def handle_input(self):
        """Handle input and focus switching.
        
        Returns (should_continue, key).
        Ctrl+key calls command_handler and returns False.
        ESC toggles focus between middle/bottom.
        Enter in bottom slice returns to middle.
        """
        # Get input from the currently focused slice
        if self.input_focus == "middle":
            focused_slice = self.middle
        else:
            focused_slice = self.bottom
        
        key = focused_slice.get_input()
        
        # Handle Ctrl+key combinations
        if self._is_ctrl_key(key):
            char = self._get_ctrl_char(key)
            if self.command_handler:
                self.command_handler(char)
            return (False, char)
        
        # Handle ESC - toggle input focus
        if key == 27:  # ESC key
            if self.input_focus == "middle":
                self.input_focus = "bottom"
            else:
                self.input_focus = "middle"
            return (True, None)
        
        # Handle ENTER in bottom slice - return to middle
        if key == ord('\n') and self.input_focus == "bottom":
            self.input_focus = "middle"
            return (True, None)
        
        # Other keys are handled by the application layer
        return (True, key)

    def get_current_input_focus(self):
        """Get the slice that currently has input focus."""
        return self.input_focus
