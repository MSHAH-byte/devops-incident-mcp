from pathlib import Path


LOG_FILE = Path(__file__).resolve().parents[2] / "logs" / "application.log"


def read_recent_logs(lines: int = 20) -> list[str]:
    """Return the most recent log lines."""

    if lines <= 0:
        return []

    if not LOG_FILE.exists():
        return [f"Log file not found: {LOG_FILE}"]

    with LOG_FILE.open("r", encoding="utf-8") as file:
        log_lines = file.readlines()

    return [line.rstrip("\n") for line in log_lines[-lines:]]


def find_log_errors() -> list[str]:
    """Return log lines containing ERROR."""

    if not LOG_FILE.exists():
        return [f"Log file not found: {LOG_FILE}"]

    with LOG_FILE.open("r", encoding="utf-8") as file:
        return [
            line.rstrip("\n")
            for line in file
            if "ERROR" in line
        ]


def get_application_health() -> dict:
    """Return a simple health summary based on application logs."""

    if not LOG_FILE.exists():
        return {
            "status": "unknown",
            "reason": "Log file not found.",
        }

    with LOG_FILE.open("r", encoding="utf-8") as file:
        log_lines = file.readlines()

    error_count = sum("ERROR" in line for line in log_lines)
    warning_count = sum("WARN" in line for line in log_lines)

    payment_unhealthy = any(
        "service=payment status=unhealthy" in line
        for line in log_lines
    )

    return {
        "status": "degraded" if payment_unhealthy else "healthy",
        "errors": error_count,
        "warnings": warning_count,
        "payment_service": "unhealthy" if payment_unhealthy else "healthy",
    }