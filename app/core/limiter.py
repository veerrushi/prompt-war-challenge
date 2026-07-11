"""
Shared SlowAPI rate-limiter instance.

Configured to identify clients by their remote IP address.
Import ``limiter`` wherever a rate-limited endpoint is needed.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
