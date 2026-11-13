from collections.abc import Mapping

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.types import Event, Hint

SCRUBBED_REQUEST_KEYS = ("query_string", "data", "cookies")


def scrub_event(event: Event, hint: Hint) -> Event:
    """No query string, body or cookies of a request leave the site."""
    request = event.get("request")
    if request is not None:
        for key in SCRUBBED_REQUEST_KEYS:
            request.pop(key, None)
    return event


def init_error_tracking(env: Mapping[str, str], debug: bool) -> bool:
    """Server errors go to Sentry only when SENTRY_DSN is set; no personal data is sent."""
    dsn = env.get("SENTRY_DSN", "").strip()
    if not dsn:
        return False
    sentry_sdk.init(
        dsn=dsn,
        integrations=[DjangoIntegration()],
        send_default_pii=False,
        include_local_variables=False,
        max_request_body_size="never",
        traces_sample_rate=0.0,
        environment="development" if debug else "production",
        release=env.get("RENDER_GIT_COMMIT", "").strip() or None,
        before_send=scrub_event,
    )
    return True
