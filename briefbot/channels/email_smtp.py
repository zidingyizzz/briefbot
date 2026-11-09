"""SMTP email channel (shared `smtp:` block in config).

Ports: 587 = STARTTLS (default), 465 = implicit SSL.
"""
import smtplib
from email.message import EmailMessage

from .base import Channel


class EmailChannel(Channel):
    type = "email"

    def send(self, subject, body):
        smtp = self.ctx.get("smtp") or {}
        host = smtp.get("host")
        user = smtp.get("user")
        password = smtp.get("password")
        if not host:
            raise RuntimeError("email channel requires an `smtp:` section in config")

        port = int(smtp.get("port", 587))
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = smtp.get("from") or user
        msg["To"] = self.spec["to"]
        msg.set_content(body)

        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=30)
        else:
            server = smtplib.SMTP(host, port, timeout=30)
        with server:
            if port != 465:
                server.starttls()
            if user:
                server.login(user, password or "")
            server.send_message(msg)
