import requests

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class GraphAPIError(Exception):
    pass


class GraphAuthError(Exception):
    pass


class GraphConfig:
    """
    Compatibility config class expected by app.py
    """
    def __init__(self, tenant_id=None, client_id=None, client_secret=None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret


class GraphClient:
    def __init__(self, access_token: str):
        self.access_token = access_token

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def send_mail(
        self,
        sender_email: str,
        to_emails: list,
        subject: str,
        html_body: str,
        attachments: list = None,
        cc_emails: list = None
    ):
        if attachments is None:
            attachments = []

        if cc_emails is None:
            cc_emails = []

        payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": html_body
                },
                "toRecipients": [
                    {"emailAddress": {"address": e}} for e in to_emails
                ],
                "ccRecipients": [
                    {"emailAddress": {"address": e}} for e in cc_emails
                ],
                "attachments": [
                    {
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": a["name"],
                        "contentType": a["contentType"],
                        "contentBytes": a["contentBytes"]
                    }
                    for a in attachments
                ]
            },
            "saveToSentItems": True
        }

        url = f"{GRAPH_BASE}/users/{sender_email}/sendMail"
        r = requests.post(url, headers=self._headers(), json=payload)

        if r.status_code in (401, 403):
            raise GraphAuthError(f"Graph auth error: {r.status_code} {r.text}")

        if r.status_code not in (200, 201, 202):
            raise GraphAPIError(f"Graph sendMail failed: {r.status_code} {r.text}")

        return {"success": True, "status_code": r.status_code}
