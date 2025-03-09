"""
ThinkiPlex Package Entry Point
----------------------------
This module allows the package to be run as a script with 'python -m thinkiplex'.
"""

import sys

from thinkiplex.main import main

if __name__ == "__main__":
    sys.exit(main())
