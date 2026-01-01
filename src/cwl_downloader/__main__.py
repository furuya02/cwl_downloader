"""
Main entry point for cwl_downloader
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
from .cli import run_interactive_mode


def main() -> int:
    """
    Main entry point

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Load environment variables from .env file
    load_dotenv()

    try:
        run_interactive_mode()
        return 0
    except Exception as e:
        print(f"予期しないエラーが発生しました: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
