import logging

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.logging import TimezoneFormatter


def test_timezone_formatter_uses_configured_timezone():
    formatter = TimezoneFormatter("%(asctime)s %(message)s", "Asia/Shanghai")
    record = logging.LogRecord("test", logging.INFO, "", 0, "hello", (), None)
    record.created = 0

    assert formatter.format(record) == "1970-01-01T08:00:00.000+08:00 hello"


def test_settings_reject_invalid_log_timezone():
    with pytest.raises(ValidationError, match="valid IANA timezone"):
        Settings(_env_file=None, log_timezone="Mars/Olympus_Mons")
