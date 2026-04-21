#!/usr/bin/env python3

from __future__ import annotations

import logging
import os
import signal
import sys

from typing import Any

logger = logging.getLogger(__name__)

# Force Qt to use X11 backend for VTK compatibility (Wayland issues)
if 'QT_QPA_PLATFORM' not in os.environ:
    os.environ['QT_QPA_PLATFORM'] = 'xcb'

# Disable Linux native virtual keyboard (on-screen keyboard) for text input fields
os.environ['QT_IM_MODULE'] = 'none'

# Global reference for signal handler
_app_instance = None
_shutdown_requested = False

def _teardown_qml_runtime(engine: Any, app: Any, log_shutdown) -> None:
    from paint_controller.core.app_runtime import teardown_qml_runtime

    teardown_qml_runtime(engine, app, log_shutdown)

def signal_handler(signum, frame):
    """Handle SIGINT (Ctrl+C) gracefully and force-exit on repeat."""
    global _shutdown_requested

    print("\n\nReceived interrupt signal (Ctrl+C)...")
    if _shutdown_requested:
        print("Forced shutdown complete.")
        os._exit(1)

    _shutdown_requested = True
    print("Requesting graceful shutdown...")

    try:
        global _app_instance
        if _app_instance is not None:
            _app_instance.quit()
            return
    except Exception:
        pass

    print("No active QApplication; forcing shutdown.")
    os._exit(1)


def main():
    from paint_controller.core.app_runtime import AppRuntime

    global _app_instance
    runtime: AppRuntime | None = None

    def _register_app_instance(app) -> None:
        global _app_instance

        _app_instance = app

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    try:
        runtime = AppRuntime(sys.argv, on_app_created=_register_app_instance)
        sys.exit(runtime.exec())
    except Exception as error:
        logger.error("Application error: %s", error)
        import traceback

        traceback.print_exc()
    finally:
        if runtime is not None:
            runtime.shutdown()

if __name__ == '__main__':
    main()