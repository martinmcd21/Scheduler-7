import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional


class ICSValidationError(Exception):
    pass


def stable_uid(*parts: str) -> str:
    """
    Generates a stable UID for the same interview slot.
    This ensures Outlook treats resends as the SAME meeting, not a new one.
    """
    base = "|".join([p.strip() for p in parts if p])
    digest = hashlib.sha256(base.encode("utf-8")).hexdigest()
    return f"{digest[:32]}@powerdashhr.com"


def _fmt_dt(dt: datetime) -> str:
    """
    Format datetime to ICS UTC format: YYYYMMDDTHHMMSSZ
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y%m%dT%H%M%SZ")


@dataclass
class ICSInvite:
    uid: str
    summary: str
    description: str
    location: str
    organizer_email: str
    organizer_name: str
    attendees: List[Dict[str, str]]
    start_utc: datetime
    end_utc: datetime
    method: str = "REQUEST"

    def validate(self):
        if not self.uid:
            raise ICSValidationError("Missing UID")
        if not self.summary:
            raise ICSValidationError("Missing summary")
        if not self.organizer_email:
            raise ICSValidationError("Missing organizer email")
        if not isinstance(self.start_utc, datetime) or not isinstance(self.end_utc, datetime):
            raise ICSValidationError("start_utc and end_utc must be datetime objects")
        if self.end_utc <= self.start_utc:
            raise ICSValidationError("end_utc must be after start_utc")

    def to_ics(self) -> str:
        self.validate()

        dtstamp = _fmt_dt(datetime.now(timezone.utc))
        dtstart = _fmt_dt(self.start_utc)
        dtend = _fmt_dt(self.end_utc)

        lines = [
            "BEGIN:VCALENDAR",
            "PRODID:-//PowerDash HR//Interview Scheduler//EN",
            "VERSION:2.0",
            f"METHOD:{self.method}",
            "CALSCALE:GREGORIAN",
            "BEGIN:VEVENT",
            f"UID:{self.uid}",
            f"DTSTAMP:{dtstamp}",
            f"DTSTART:{dtstart}",
            f"DTEND:{dtend}",
            f"SUMMARY:{self.summary}",
            f"DESCRIPTION:{self.description}",
            f"LOCATION:{self.location}",
            f"ORGANIZER;CN={self.organizer_name}:MAILTO:{self.organizer_email}",
            "SEQUENCE:0",
            "STATUS:CONFIRMED",
            "TRANSP:OPAQUE",
        ]

        for a in self.attendees:
            email = (a.get("email") or "").strip()
            name = (a.get("name") or "").strip() or email
            role = (a.get("role") or "REQ-PARTICIPANT").strip()

            if email:
                lines.append(
                    f"ATTENDEE;CN={name};ROLE={role};PARTSTAT=NEEDS-ACTION;RSVP=TRUE:MAILTO:{email}"
                )

        lines.extend([
            "END:VEVENT",
            "END:VCALENDAR"
        ])

        return "\r\n".join(lines) + "\r\n"


def create_ics_from_interview(
    subject: str,
    agenda: str,
    location: str,
    organizer_email: str,
    organizer_name: str,
    attendees: List[Dict[str, str]],
    start_utc: datetime,
    duration_minutes: int,
    uid: Optional[str] = None
) -> str:
    """
    Creates a proper ICS meeting request that Outlook/Gmail treat as a real invite.
    """

    if start_utc.tzinfo is None:
        start_utc = start_utc.replace(tzinfo=timezone.utc)

    end_utc = start_utc + timedelta(minutes=duration_minutes)

    if not uid:
        uid = stable_uid(subject, organizer_email, start_utc.isoformat())

    invite = ICSInvite(
        uid=uid,
        summary=subject,
        description=agenda or "",
        location=location or "",
        organizer_email=organizer_email,
        organizer_name=organizer_name or organizer_email,
        attendees=attendees,
        start_utc=start_utc,
        end_utc=end_utc
    )

    return invite.to_ics()
