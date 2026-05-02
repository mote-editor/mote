import argparse
import sys

def main():
    # Initialize argument parser
    parser = argparse.ArgumentParser(description="mote - A tiny terminal text editor")
    parser.add_argument("filename", nargs="?", help="The file to open")
    args = parser.parse_args()

    # Variable to store data from piped input
    input_data = None

    # Check if data is being piped in (not a TTY)
    if not sys.stdin.isatty():
        # Read all piped input from stdin
        input_data = sys.stdin.read()
        
        # Restore stdin to the terminal so the editor can interact with the user
        sys.stdin = open('/dev/tty', 'r') 
        
        print(f"Captured {len(input_data)} characters from pipe.")

    # Determine the startup mode based on if there is a file arg or piped input
    if args.filename:
        # Open file from arg
        pass
    elif input_data:
        # Open piped input
        pass
    else:
        # Open new buffer
        pass
        
if __name__ == "__main__":
    main()