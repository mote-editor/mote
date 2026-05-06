class CommandHandler:
    """Handle editor commands from keyboard or command palette."""

    def __call__(self, command_text):
        text = command_text.strip().lower()
        if text in ("q", "quit", "exit"):
            return False
        return True
