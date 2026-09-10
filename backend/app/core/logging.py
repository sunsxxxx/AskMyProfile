from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def resolve_timezone(timezone_name: str) -> tzinfo:
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        # Keep the default usable on minimal systems before tzdata is installed.
        if timezone_name == "Asia/Shanghai":
            return timezone(timedelta(hours=8), name=timezone_name)
        raise


class TimezoneFormatter(logging.Formatter):
    """Format log timestamps in an explicit IANA timezone."""

    def __init__(self, fmt: str, timezone_name: str) -> None:
        super().__init__(fmt)
        self.timezone = resolve_timezone(timezone_name)

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        timestamp = datetime.fromtimestamp(record.created, self.timezone)
        if datefmt:
            return timestamp.strftime(datefmt)
        return timestamp.isoformat(timespec="milliseconds")
