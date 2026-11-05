from dataclasses import dataclass
from datetime import date, datetime, time

from reviews import report_repository
from reviews.services import RATING_RANGES, VIETNAM_TZ, average_from_totals

REPORT_MONTHS = 12
MONTH_NAMES = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


@dataclass(frozen=True)
class MonthOption:
    value: str
    label: str


@dataclass(frozen=True)
class ReportRow:
    branch_id: int
    name: str
    review_count: int
    average_rating: float | None
    good_count: int
    bad_count: int


@dataclass(frozen=True)
class MonthlyReport:
    month: date
    label: str
    options: list[MonthOption]
    rows: list[ReportRow]


def _label(month: date) -> str:
    return f"{MONTH_NAMES[month.month - 1]} {month.year}"


def _month_start(year: int, month_number: int) -> date:
    """First day of a month; a month number below 1 or above 12 rolls into the next year."""
    year += (month_number - 1) // 12
    return date(year, (month_number - 1) % 12 + 1, 1)


def _start_of(month: date) -> datetime:
    return datetime.combine(month, time.min, tzinfo=VIETNAM_TZ)


def monthly_report(month: date | None, now: datetime) -> MonthlyReport:
    """Numbers of each location for one month of Vietnam time; an unlisted month means this one."""
    today = now.astimezone(VIETNAM_TZ)
    months = [_month_start(today.year, today.month - back) for back in range(REPORT_MONTHS)]
    chosen = month if month in months else months[0]
    following = _month_start(chosen.year, chosen.month + 1)
    totals = report_repository.month_totals(
        _start_of(chosen), _start_of(following), RATING_RANGES["good"], RATING_RANGES["bad"]
    )
    rows = [
        ReportRow(
            branch_id=t.branch_id,
            name=t.name,
            review_count=t.review_count,
            average_rating=average_from_totals(t.rating_total, t.review_count),
            good_count=t.good_count,
            bad_count=t.bad_count,
        )
        for t in totals
    ]
    return MonthlyReport(
        month=chosen,
        label=_label(chosen),
        options=[MonthOption(value=f"{m.year}-{m.month:02d}", label=_label(m)) for m in months],
        rows=rows,
    )
