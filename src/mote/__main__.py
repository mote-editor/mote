import argparse
import curses
import sys
from pathlib import Path

from mote.core.buffer import Buffer
from mote.ui.layout import ScreenLayout

def main():
    # Initialize argument parser
    parser = argparse.ArgumentParser(description="mote - A tiny terminal text editor")
    parser.add_argument("filename", nargs="?", help="The file to open")
    args = parser.parse_args()

    # Variable to store data from piped input
    input_data = None

    # Check if data is being piped in (not a TTY)
    if not sys.stdin.isatty():
        input_data = sys.stdin.read()

        # Restore stdin to the terminal so the editor can interact with the user
        if sys.platform.startswith("win"):
            sys.stdin = open("CONIN$", "r")
        else:
            sys.stdin = open("/dev/tty", "r")

    # Determine the startup buffer based on file arg or piped input
    buffer = None
    if args.filename:
        file_path = Path(args.filename)
        try:
            text = file_path.read_text(encoding="utf-8")
        except OSError:
            text = ""
        buffer = Buffer(text=text, name=str(file_path))
        buffer.file_path = str(file_path)
    elif input_data is not None:
        buffer = Buffer(text=input_data, name="stdin")

    def run_editor(window):
        layout = ScreenLayout(window, buffer=buffer, show_line_numbers=True)

        try:
            while True:
                layout.render()
                layout.refresh_all()

                should_continue, _key = layout.handle_input()
                if not should_continue:
                    break
        except KeyboardInterrupt:
            pass

    curses.wrapper(run_editor)
        
if __name__ == "__main__":
    main()