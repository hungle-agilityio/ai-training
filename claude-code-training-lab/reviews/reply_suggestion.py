import logging
from dataclasses import dataclass
from typing import Literal

from django.conf import settings

from reviews import claude_client, reply_repository
from reviews.claude_client import ClaudeError
from reviews.reply_service import REPLY_MAX_LENGTH

SUGGESTION_TIMEOUT_SECONDS = 15
SUGGESTION_MAX_TOKENS = 500
FAKE_REPLY_TEXT = (
    "Thank you for taking the time to share your experience. We are sorry it fell short of "
    "what you expected, and we would like to make it right. Please contact us so we can help."
)
REPLY_SYSTEM_PROMPT = (
    "You write a reply from a business location to a customer review.\n"
    "- Write in the same language as the review.\n"
    "- Be polite and short: at most 600 characters, plain text.\n"
    "- For a rating of 1 or 2, apologise, name the problem from the review and invite the "
    "customer to contact the location.\n"
    "- For a rating of 3, thank the customer and answer the concern.\n"
    "- For a rating of 4 or 5, thank the customer.\n"
    "- Never promise a refund, a discount or any compensation.\n"
    "- Never add facts that are not in the review.\n"
    "- Write no signature and no placeholder such as [Name]."
)

logger = logging.getLogger("reviews.reply_suggestion")


@dataclass(frozen=True)
class ReplySuggestion:
    status: Literal["ok", "failed", "off"]
    draft: str


def suggestion_mode() -> Literal["off", "fake", "live"]:
    """Fake when asked or in DEBUG without a key; live with a key; otherwise off."""
    if settings.REVIEWRADAR_AI_FAKE or (settings.DEBUG and not settings.ANTHROPIC_API_KEY):
        return "fake"
    return "live" if settings.ANTHROPIC_API_KEY else "off"


def user_message(location: str, rating: int, text: str) -> str:
    """Only the location name, the rating and the review text are sent."""
    return f"Location: {location}\nRating: {rating} out of 5\nReview:\n{text}"


def build_draft(answer: str, location: str) -> str:
    """The answer, a blank line and the signature, cut at a space to fit 1000 characters."""
    signature = f"\n\n— {location} team"
    body = answer.strip()
    room = REPLY_MAX_LENGTH - len(signature)
    if len(body) > room:
        cut = body[: room + 1].rfind(" ")
        body = body[:cut].rstrip() if cut > 0 else body[:room]
    return body + signature


def suggest_reply(review_id: int) -> ReplySuggestion | None:
    """A draft reply for the review; None for an unknown review."""
    review = reply_repository.review_with_branch(review_id)
    if review is None:
        return None
    mode = suggestion_mode()
    if mode == "off":
        return ReplySuggestion("off", "")
    location = review.branch.name
    if mode == "fake":
        return ReplySuggestion("ok", build_draft(FAKE_REPLY_TEXT, location))
    try:
        answer = claude_client.create_message(
            api_key=settings.ANTHROPIC_API_KEY,
            model=settings.ANTHROPIC_MODEL,
            system=REPLY_SYSTEM_PROMPT,
            user_text=user_message(location, review.rating, review.text),
            max_tokens=SUGGESTION_MAX_TOKENS,
            timeout=SUGGESTION_TIMEOUT_SECONDS,
        )
    except ClaudeError as error:
        logger.warning(
            "Reply suggestion failed: %s %s",
            error.kind,
            error.status if error.status is not None else "-",
        )
        return ReplySuggestion("failed", "")
    if not answer.strip():
        logger.warning("Reply suggestion failed: empty_answer -")
        return ReplySuggestion("failed", "")
    return ReplySuggestion("ok", build_draft(answer, location))
