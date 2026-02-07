import uuid
from datetime import datetime, timedelta


def _format_dt(dt: datetime) -> str:
    """Format datetime into iCalendar UTC format."""
    return dt.strftime("%Y%m%dT%H%M%SZ")


def build_meeting_invite_ics(
    subject: str,
    description: str,
    start_utc: datetime,
    end_utc: datetime,
    organizer_email: str,
    organizer_name: str,
    required_attendees: list,
    optional_attendees: list = None,
    location: str = ""
) -> bytes:
    """
    Creates a standard Outlook-compatible meeting request ICS.
    This produces Accept/Tentative/Decline behavior.
    """

    if optional_attendees is None:
        optional_attendees = []

    uid = str(uuid.uuid4())
    now = datetime.utcnow()

    lines = []
    lines.append("BEGIN:VCALENDAR")
    lines.append("PRODID:-//PowerDashHR//Interview Scheduler//EN")
    lines.append("VERSION:2.0")
    lines.append("CALSCALE:GREGORIAN")
    lines.append("METHOD:REQUEST")
    lines.append("BEGIN:VEVENT")
    lines.append(f"UID:{uid}")
    lines.append(f"DTSTAMP:{_format_dt(now)}")
    lines.append(f"DTSTART:{_format_dt(start_utc)}")
    lines.append(f"DTEND:{_format_dt(end_utc)}")
    lines.append(f"SUMMARY:{subject}")
    lines.append(f"DESCRIPTION:{description}")
    lines.append(f"LOCATION:{location}")

    # Organizer
    lines.append(f"ORGANIZER;CN={organizer_name}:MAILTO:{organizer_email}")

    # Required attendees
    for email in required_attendees:
        lines.append(f"ATTENDEE;CN={email};ROLE=REQ-PARTICIPANT;RSVP=TRUE:MAILTO:{email}")

    # Optional attendees
    for email in optional_attendees:
        lines.append(f"ATTENDEE;CN={email};ROLE=OPT-PARTICIPANT;RSVP=TRUE:MAILTO:{email}")

    lines.append("STATUS:CONFIRMED")
    lines.append("SEQUENCE:0")
    lines.append("TRANSP:OPAQUE")

    # Alarm reminder (15 minutes)
    lines.append("BEGIN:VALARM")
    lines.append("TRIGGER:-PT15M")
    lines.append("ACTION:DISPLAY")
    lines.append("DESCRIPTION:Reminder")
    lines.append("END:VALARM")

    lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")

    ics_text = "\r\n".join(lines) + "\r\n"
    return ics_text.encode("utf-8")
