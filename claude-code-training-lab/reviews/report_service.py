import csv
import io
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import ROUND_HALF_UP, Decimal

from reviews import report_repository
from reviews.services import CSV_BOM, RATING_RANGES, VIETNAM_TZ, average_from_totals, csv_safe

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
    change: float | None = None


@dataclass(frozen=True)
class MonthlyReport:
    month: date
    label: str
    previous_label: str
    options: list[MonthOption]
    rows: list[ReportRow]

    @property
    def month_value(self) -> str:
        return f"{self.month.year}-{self.month.month:02d}"

    @property
    def has_reviews(self) -> bool:
        return any(row.review_count for row in self.rows)


def _change(average: float | None, before: float | None) -> float | None:
    """Difference of two shown averages to one decimal; None when either month has no score."""
    if average is None or before is None:
        return None
    return float(
        (Decimal(str(average)) - Decimal(str(before))).quantize(
            Decimal("0.1"), rounding=ROUND_HALF_UP
        )
    )


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
    previous = _month_start(chosen.year, chosen.month - 1)
    pairs = report_repository.month_pair_totals(
        _start_of(chosen),
        _start_of(following),
        _start_of(previous),
        RATING_RANGES["good"],
        RATING_RANGES["bad"],
    )
    rows = []
    for pair in pairs:
        t = pair.current
        average = average_from_totals(t.rating_total, t.review_count)
        before = average_from_totals(pair.previous_rating_total, pair.previous_review_count)
        rows.append(
            ReportRow(
                branch_id=t.branch_id,
                name=t.name,
                review_count=t.review_count,
                average_rating=average,
                good_count=t.good_count,
                bad_count=t.bad_count,
                change=_change(average, before),
            )
        )
    return MonthlyReport(
        month=chosen,
        label=_label(chosen),
        previous_label=MONTH_NAMES[previous.month - 1],
        options=[MonthOption(value=f"{m.year}-{m.month:02d}", label=_label(m)) for m in months],
        rows=rows,
    )


CSV_REPORT_HEADER = ("Location", "Reviews", "Average", "Good", "Bad", "Change vs previous month")


def report_filename(report: MonthlyReport) -> str:
    return f"reviewradar-report-{report.month_value}.csv"


def _signed(change: float | None) -> str:
    if change is None:
        return ""
    return f"{change:+.1f}" if change else "0.0"


def report_csv(report: MonthlyReport) -> str:
    """The page table as CSV text: BOM first, CRLF line ends, names safe for a spreadsheet."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(CSV_REPORT_HEADER)
    for row in report.rows:
        average = "" if row.average_rating is None else f"{row.average_rating:.1f}"
        writer.writerow(
            (
                csv_safe(row.name),
                row.review_count,
                average,
                row.good_count,
                row.bad_count,
                _signed(row.change),
            )
        )
    return CSV_BOM + buffer.getvalue()
