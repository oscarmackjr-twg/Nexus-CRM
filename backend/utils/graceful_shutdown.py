from __future__ import annotations

import signal


def install_signal_handlers(app, celery_app=None) -> None:
    def _handle_sigterm(signum, frame):
        print("[shutdown] SIGTERM received — shutting down gracefully")

    signal.signal(signal.SIGTERM, _handle_sigterm)
