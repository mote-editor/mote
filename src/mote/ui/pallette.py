from mote.core.buffer import Buffer


class Palette:
    """Command palette UI for the bottom bar."""

    def __init__(self, screen_slice, label="ESC Commands "):
        self.slice = screen_slice
        self.label = label
        self.buffer = Buffer(text="", name="Command Palette")

    def render(self, move_cursor=True):
        height, width = self.slice.get_dimensions()
        prompt = "> "
        command_text = self.buffer.get_line()
        available = max(0, width - len(prompt) - len(self.label) - 1)
        visible_command = command_text[:available]

        self.slice.clear()
        self.slice.draw(0, "", align="left", style="BAR", fill_line=True)
        self.slice.draw_at_coords(0, 0, f"{prompt}{visible_command}", style="BAR")
        self.slice.draw(0, self.label, align="right", style="BAR")

        if move_cursor:
            self.move_cursor()

    def move_cursor(self):
        height, width = self.slice.get_dimensions()
        prompt = "> "
        available = max(0, width - len(prompt) - len(self.label) - 1)
        cursor_x = len(prompt) + min(self.buffer.cx, max(0, available))
        cursor_x = max(0, min(cursor_x, width - 1))
        self.slice.move_cursor(0, cursor_x)

    def handle_key(self, key):
        if key == ord("\n"):
            self.clear()
            return
        if key == 27:
            self.clear()
            return
        if key in (ord("\b"), 8, 127, 263):
            self.buffer.delete_char()
            return
        if key == ord("\t"):
            for _ in range(4):
                self.buffer.insert_char(" ")
            return
        if 32 <= key <= 126:
            self.buffer.insert_char(chr(key))

    def get_command(self):
        return self.buffer.get_line()

    def clear(self):
        self.buffer = Buffer(text="", name="Command Palette")
