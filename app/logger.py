"""
╔═══════════════════════════════════════════════════╗
║           SKYY – Logging Configuration            ║
║  Structured logging with rotation & security      ║
╚═══════════════════════════════════════════════════╝
"""

import os
import logging
import logging.handlers


def setup_logging(app):
    """Configure application logging with rotation and structured format."""

    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_file = os.getenv('LOG_FILE', 'logs/skyy.log')
    log_dir = os.path.dirname(log_file)

    # Ensure log directory exists
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # ─── Formatter ───
    class SecurityFormatter(logging.Formatter):
        """Custom formatter that sanitizes sensitive data from logs."""

        SENSITIVE_FIELDS = [
            'password', 'token', 'secret', 'authorization', 'cookie'
        ]

        def format(self, record):
            msg = super().format(record)
            for field in self.SENSITIVE_FIELDS:
                msg = msg.replace(field, '[REDACTED]')
            return msg

    formatter = SecurityFormatter(
        '[%(asctime)s] %(levelname)s '
        '[%(name)s:%(funcName)s:%(lineno)d] %(message)s'
    )

    # ─── File Handler (rotating, 10MB per file, 30 backups) ───
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=30,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, log_level, logging.INFO))

    # ─── Console Handler ───
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s: %(message)s'
    ))
    console_handler.setLevel(logging.DEBUG if app.debug else logging.WARNING)

    # ─── Apply to Flask app logger ───
    app.logger.handlers.clear()
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(getattr(logging, log_level, logging.INFO))

    # ─── Also configure root logger ───
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)

    app.logger.info(
        f'Logging initialized: level={log_level}, file={log_file}'
    )

    return app.logger
