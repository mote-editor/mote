class CommandHandler:
    """Handle editor commands from keyboard or command palette."""

    def __init__(self, buffer=None, save_func=None):
        self.buffer = buffer
        self.save_func = save_func

    def _handle_save(self):
        if not self.save_func:
            return False
        if self.buffer is not None:
            return self.save_func(self.buffer)
        return self.save_func()

    def __call__(self, command_text):
        text = command_text.strip().lower()
        if text in ("q", "quit", "exit"):
            return False
        if text in ("save", "write", "w", "s"):
            self._handle_save()
            return True
        return True
