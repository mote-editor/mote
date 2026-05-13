import curses
import sys
from mote import __version__
from mote.core.command_handler import CommandHandler
from mote.core.save import save_buffer
from mote.ui_lib.screen import Screen
from mote.ui.editor import Editor
from mote.ui.palette import Palette


class ScreenLayout:
    """Screen layout with top, middle, and bottom slices.
    
    Top and bottom are fixed at 1 line each, middle fills the rest.
    Handles input focus switching and command dispatch.
    """

    def __init__(self, window, theme=None, command_handler=None, buffer=None, show_line_numbers=False):
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
        
        # Create editor for the middle slice
        self.editor = Editor(self.middle, buffer=buffer, show_line_numbers=show_line_numbers)
        self.palette = Palette(self.bottom)
        self._default_palette_label = self.palette.label
        self._pending_save_as = False
        self._clipboard = ""
        
        # Input state management
        self.input_focus = "middle"  # "middle" or "bottom"
        if command_handler is None:
            self.command_handler = CommandHandler(buffer=self.editor.buffer, save_func=save_buffer)
        else:
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
        if self.input_focus == "bottom":
            self.middle.refresh()
            self.bottom.refresh()
        else:
            self.bottom.refresh()
            self.middle.refresh()
        Screen.update_physical()
        if self.input_focus == "bottom":
            self.palette.move_cursor()
            self.bottom.refresh()
        else:
            self.editor.move_cursor()
            self.middle.refresh()
        Screen.update_physical()

    def clear_all(self):
        """Clear all slices."""
        self.top.clear()
        self.middle.clear()
        self.bottom.clear()

    def _is_ctrl_key(self, key):
        """Check if key is a ctrl combination (1-26)."""
        # Ctrl+A = 1, Ctrl+B = 2, ... Ctrl+Z = 26
        return 1 <= key <= 26 and key not in (9, 10, 13)

    def _get_ctrl_char(self, key):
        """Convert ctrl key code (1-26) to char (a-z)."""
        # Ctrl+A = 1 -> 'a', Ctrl+B = 2 -> 'b', etc.
        return chr(ord('a') + key - 1)

    def _buffer_needs_path(self):
        buffer = self.editor.buffer
        if getattr(buffer, "file_path", None):
            return False
        return buffer.name == "Untitled"

    def _begin_save_as_prompt(self):
        self._pending_save_as = True
        self.input_focus = "bottom"
        self.palette.label = "ENTER Save As "
        self.palette.render(move_cursor=True)
        self.bottom.refresh()
        Screen.update_physical()

    def _cancel_save_as_prompt(self):
        self._pending_save_as = False
        self.palette.label = self._default_palette_label
        self.palette.clear()
        self.input_focus = "middle"
        self.editor.render(move_cursor=True)
        self.middle.refresh()
        Screen.update_physical()

    def _complete_save_as_prompt(self, filename):
        self._pending_save_as = False
        self.palette.label = self._default_palette_label
        self.palette.clear()
        self.input_focus = "middle"

        if filename:
            self.editor.buffer.name = filename
            save_buffer(self.editor.buffer)

        self.editor.render(move_cursor=True)
        self.middle.refresh()
        Screen.update_physical()

    def _handle_save_request(self):
        if self._buffer_needs_path():
            self._begin_save_as_prompt()
            return
        save_buffer(self.editor.buffer)

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

        # Windows often reports backspace as Ctrl+H (8). Handle it early so it
        # reaches the editor/palette instead of command dispatch.
        if sys.platform.startswith("win") and key == 8:
            if self.input_focus == "middle":
                self.editor.handle_key(key)
            else:
                self.palette.handle_key(key)
            return (True, key)
        
        # Handle Ctrl+key combinations
        if self._is_ctrl_key(key):
            char = self._get_ctrl_char(key)
            if char == "q":
                return (False, char)
            if char == "s":
                self._handle_save_request()
                return (True, char)
            if char == "c":
                if self.input_focus == "middle":
                    selected = self.editor.buffer.get_selection_text()
                    if selected:
                        self._clipboard = selected
                else:
                    selected = self.palette.buffer.get_selection_text()
                    if selected:
                        self._clipboard = selected
                return (True, char)
            if char == "x":
                if self.input_focus == "middle":
                    selected = self.editor.buffer.get_selection_text()
                    if selected:
                        self._clipboard = selected
                        self.editor.buffer.delete_selection()
                else:
                    selected = self.palette.buffer.get_selection_text()
                    if selected:
                        self._clipboard = selected
                        self.palette.buffer.delete_selection()
                return (True, char)
            if char == "v":
                if self.input_focus == "middle":
                    if self._clipboard:
                        self.editor.buffer.insert_text(self._clipboard)
                else:
                    if self._clipboard:
                        self.palette.buffer.insert_text(self._clipboard)
                return (True, char)
            if self.command_handler:
                should_continue = self.command_handler(char)
                if should_continue is False:
                    return (False, char)
            return (True, char)
        
        # Handle ESC - toggle input focus
        if key == 27:  # ESC key
            if self._pending_save_as and self.input_focus == "bottom":
                self._cancel_save_as_prompt()
                return (True, None)
            if self.input_focus == "middle":
                self.input_focus = "bottom"
                self.bottom.draw(0, "", align="left", style="BAR", fill_line=True)
                self.palette.render(move_cursor=True)
                self.bottom.refresh()
            else:
                self.input_focus = "middle"
                self.editor.render(move_cursor=True)
                self.middle.refresh()
            if self.input_focus == "bottom":
                self.bottom.refresh()
            else:
                self.middle.refresh()
            Screen.update_physical()
            return (True, None)
        
        # Handle ENTER in bottom slice - run command, clear, return to middle
        if key in (10, 13) and self.input_focus == "bottom":
            command_text = self.palette.get_command().strip()
            if self._pending_save_as:
                self._complete_save_as_prompt(command_text)
                return (True, None)

            self.palette.clear()
            self.input_focus = "middle"
            if command_text:
                if command_text.lower() in ("save", "write", "w", "s"):
                    self._handle_save_request()
                elif self.command_handler:
                    should_continue = self.command_handler(command_text)
                    if should_continue is False:
                        return (False, None)
            return (True, None)
        
        # Pass input to editor if middle has focus (including Enter for newline)
        if self.input_focus == "middle":
            self.editor.handle_key(key)
        elif self.input_focus == "bottom":
            self.palette.handle_key(key)
        
        # Other keys are handled by the application layer
        return (True, key)

    def get_current_input_focus(self):
        """Get the slice that currently has input focus."""
        return self.input_focus

    def render(self):
        """Render all components to the screen."""
        buffer_name = self.editor.buffer.name or "Untitled"
        if self.editor.buffer.dirty:
            buffer_name = f"{buffer_name}*"
        self.top.draw(0, " Mote Editor", align="left", style="BAR", fill_line=True)
        self.top.draw(0, buffer_name, align="center", style="BAR", fill_line=False)
        self.top.draw(0, f"v{__version__} ", align="right", style="BAR", fill_line=False)
        self.editor.render(move_cursor=False)
        self.bottom.draw(0, "", align="left", style="BAR", fill_line=True)
        self.palette.render(move_cursor=False)
        if self.input_focus == "bottom":
            self.palette.move_cursor()
        else:
            self.editor.move_cursor()

    def get_editor(self):
        """Get the editor instance."""
        return self.editor


if __name__ == "__main__":
    def main(window):
        """Run the layout in test mode."""
        layout = ScreenLayout(
            window,
            show_line_numbers=True,
        )
        
        # Draw initial content
        layout.top.draw(0, "Top Bar", align="left", style="BAR", fill_line=True)
        layout.bottom.draw(0, "Bottom Bar", align="left", style="BAR", fill_line=True)
        
        # Main loop
        try:
            while True:
                layout.render()
                layout.refresh_all()
                
                should_continue, key = layout.handle_input()
                if not should_continue:
                    break
        except KeyboardInterrupt:
            pass
    
    curses.wrapper(main)
