import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


class ICSValidationError(Exception):
    pass


def stable_uid(*parts: str) -> str:
    """
    Generate a stable UID for an ICS invite.
    This ensures Outlook treats it as the same meeting if re-sent.
    """
    base = "|".join([p.strip() for p in parts if p])
    digest = hashlib.sha256(base.encode("utf-8")).hexdigest()
    return f"{digest[:32]}@powerdashhr.com"


def _fmt_dt(dt: datetime) -> str:
    """
    Format datetime into ICS UTC format: YYYYMMDDTHHMMSSZ
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
    attendees: list  # list of dicts: {"email":..., "name":..., "role":"REQ-PARTICIPANT"}
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
            email = a.get("email", "").strip()
            name = a.get("name", "").strip() or email
            role = a.get("role", "REQ-PARTICIPANT")
            if email:
                lines.append(
                    f"ATTENDEE;CN={name};ROLE={role};PARTSTAT=NEEDS-ACTION;RSVP=TRUE:MAILTO:{email}"
                )

        lines.extend([
            "END:VEVENT",
            "END:VCALENDAR"
        ])

        return "\r\n".join(lines) + "\r\n"


def create_interview_invite(
    uid: str,
    subject: str,
    description: str,
    location: str,
    organizer_email: str,
    organizer_name: str,
    attendees: list,
    start_utc: datetime,
    duration_minutes: int
) -> str:
    end_utc = start_utc + timedelta(minutes=duration_minutes)

    invite = ICSInvite(
        uid=uid,
        summary=subject,
        description=description,
        location=location,
        organizer_email=organizer_email,
        organizer_name=organizer_name,
        attendees=attendees,
        start_utc=start_utc,
        end_utc=end_utc
    )

    return invite.to_ics()
