#!/usr/bin/env python3
"""
Entry point for running paint_controller as a module.

Usage:
    python3 -m paint_controller
    python3 paint_controller
    
    # Use old implementation (deprecated):
    USE_OLD_MAIN=1 python3 -m paint_controller
"""

from paint_controller.core.application import main_wrapper

if __name__ == '__main__':
    main_wrapper()
