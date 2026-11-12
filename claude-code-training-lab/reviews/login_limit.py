import hashlib
import time
import unicodedata
from dataclasses import dataclass

from django.core.cache import cache

MAX_FAILURES = 5
WINDOW_SECONDS = 900
LOCK_SECONDS = 900
LOCKED_MESSAGE = "Too many failed sign-in attempts. Try again in 15 minutes."
KEY_PREFIX = "login-limit:"
CACHE_TIMEOUT = WINDOW_SECONDS + LOCK_SECONDS


@dataclass(frozen=True)
class Attempts:
    """A username is locked only while `locked_until` is set and still ahead of the clock."""

    count: int
    first_at: float
    locked_until: float | None = None


def now() -> float:
    """The clock of the limit; tests patch this function to move time."""
    return time.time()


def is_locked(username: str) -> bool:
    """A username is locked for LOCK_SECONDS from its MAX_FAILURES-th counted failure."""
    return _locked(_read(_key(username)), now())


def record_failure(username: str) -> None:
    """Count one failure; the window starts at the first counted one, a locked username is left."""
    key = _key(username)
    attempts = _read(key)
    moment = now()
    if _locked(attempts, moment):
        return
    if attempts is None or not _in_window(attempts, moment):
        attempts = Attempts(count=0, first_at=moment)
    count = attempts.count + 1
    locked_until = moment + LOCK_SECONDS if count >= MAX_FAILURES else None
    cache.set(key, Attempts(count, attempts.first_at, locked_until), CACHE_TIMEOUT)


def record_success(username: str) -> None:
    """A successful sign-in sets the count of that username back to 0."""
    cache.delete(_key(username))


def _key(username: str) -> str:
    """Spellings Django signs in as one username (NFKC) share one count, as do case and spaces."""
    normalised = unicodedata.normalize("NFKC", username).strip().casefold()
    return KEY_PREFIX + hashlib.sha256(normalised.encode("utf-8", "surrogatepass")).hexdigest()


def _read(key: str) -> Attempts | None:
    attempts: Attempts | None = cache.get(key)
    return attempts


def _locked(attempts: Attempts | None, moment: float) -> bool:
    return (
        attempts is not None
        and attempts.locked_until is not None
        and moment < attempts.locked_until
    )


def _in_window(attempts: Attempts, moment: float) -> bool:
    """An ended lock or a first failure WINDOW_SECONDS or more ago starts a new count."""
    return attempts.locked_until is None and moment - attempts.first_at < WINDOW_SECONDS
