"""Email automation module for RPA framework."""

import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass

from jinja2 import Template

from ..core.logger import LoggerMixin


@dataclass
class EmailMessage:
    """Represents an email message."""
    subject: str
    sender: str
    recipients: List[str]
    body: str
    html_body: Optional[str] = None
    attachments: Optional[List[str]] = None
    date: Optional[str] = None
    message_id: Optional[str] = None


class EmailModule(LoggerMixin):
    """Handle email sending and receiving."""

    def __init__(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: int = 587,
        imap_server: Optional[str] = None,
        imap_port: int = 993,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.username = username
        self.password = password

    def configure(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        imap_server: Optional[str] = None,
        imap_port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        """Configure email settings."""
        if smtp_server:
            self.smtp_server = smtp_server
        if smtp_port:
            self.smtp_port = smtp_port
        if imap_server:
            self.imap_server = imap_server
        if imap_port:
            self.imap_port = imap_port
        if username:
            self.username = username
        if password:
            self.password = password

    def send(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[str]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> bool:
        """Send an email.

        Args:
            to: Recipient(s)
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            attachments: List of file paths to attach
            cc: CC recipients
            bcc: BCC recipients

        Returns:
            True if sent successfully
        """
        if isinstance(to, str):
            to = [to]

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.username
        msg["To"] = ", ".join(to)

        if cc:
            msg["Cc"] = ", ".join(cc)

        # Add body
        msg.attach(MIMEText(body, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        # Add attachments
        if attachments:
            for file_path in attachments:
                self._attach_file(msg, file_path)

        # Build recipient list
        all_recipients = to.copy()
        if cc:
            all_recipients.extend(cc)
        if bcc:
            all_recipients.extend(bcc)

        # Send
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.username, all_recipients, msg.as_string())

            self.logger.info(f"Email sent to {to}: {subject}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            raise

    def _attach_file(self, msg: MIMEMultipart, file_path: str) -> None:
        """Attach a file to an email message."""
        path = Path(file_path)

        with open(path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())

        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={path.name}",
        )
        msg.attach(part)

    def send_template(
        self,
        to: Union[str, List[str]],
        subject: str,
        template: str,
        data: Dict[str, Any],
        **kwargs,
    ) -> bool:
        """Send an email using a template.

        Args:
            to: Recipient(s)
            subject: Email subject
            template: Jinja2 template string for body
            data: Template variables
            **kwargs: Additional arguments for send()

        Returns:
            True if sent successfully
        """
        tmpl = Template(template)
        body = tmpl.render(**data)

        # Check if template looks like HTML
        html_body = body if "<html" in body.lower() or "<body" in body.lower() else None
        plain_body = body if not html_body else ""

        return self.send(to, subject, plain_body, html_body=html_body, **kwargs)

    def read_inbox(
        self,
        folder: str = "INBOX",
        limit: int = 10,
        unread_only: bool = False,
    ) -> List[EmailMessage]:
        """Read emails from inbox.

        Args:
            folder: Mailbox folder
            limit: Maximum emails to fetch
            unread_only: Only fetch unread emails

        Returns:
            List of EmailMessage objects
        """
        messages = []

        try:
            with imaplib.IMAP4_SSL(self.imap_server, self.imap_port) as mail:
                mail.login(self.username, self.password)
                mail.select(folder)

                search_criteria = "UNSEEN" if unread_only else "ALL"
                _, message_ids = mail.search(None, search_criteria)

                ids = message_ids[0].split()[-limit:]

                for msg_id in ids:
                    _, msg_data = mail.fetch(msg_id, "(RFC822)")
                    email_body = msg_data[0][1]
                    msg = email.message_from_bytes(email_body)

                    body = self._get_email_body(msg)

                    messages.append(EmailMessage(
                        subject=msg.get("Subject", ""),
                        sender=msg.get("From", ""),
                        recipients=msg.get("To", "").split(","),
                        body=body,
                        date=msg.get("Date", ""),
                        message_id=msg.get("Message-ID", ""),
                    ))

            self.logger.info(f"Read {len(messages)} emails from {folder}")
            return messages

        except Exception as e:
            self.logger.error(f"Failed to read emails: {e}")
            raise

    def _get_email_body(self, msg: email.message.Message) -> str:
        """Extract body text from email message."""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode("utf-8", errors="ignore")
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                return payload.decode("utf-8", errors="ignore")
        return ""

    def search(
        self,
        folder: str = "INBOX",
        from_addr: Optional[str] = None,
        subject: Optional[str] = None,
        since: Optional[str] = None,
        before: Optional[str] = None,
    ) -> List[EmailMessage]:
        """Search for emails matching criteria.

        Args:
            folder: Mailbox folder
            from_addr: Filter by sender
            subject: Filter by subject (contains)
            since: Date string (e.g., "01-Jan-2024")
            before: Date string

        Returns:
            List of matching emails
        """
        criteria = []

        if from_addr:
            criteria.append(f'FROM "{from_addr}"')
        if subject:
            criteria.append(f'SUBJECT "{subject}"')
        if since:
            criteria.append(f'SINCE "{since}"')
        if before:
            criteria.append(f'BEFORE "{before}"')

        search_string = " ".join(criteria) if criteria else "ALL"

        messages = []

        try:
            with imaplib.IMAP4_SSL(self.imap_server, self.imap_port) as mail:
                mail.login(self.username, self.password)
                mail.select(folder)

                _, message_ids = mail.search(None, search_string)
                ids = message_ids[0].split()

                for msg_id in ids:
                    _, msg_data = mail.fetch(msg_id, "(RFC822)")
                    email_body = msg_data[0][1]
                    msg = email.message_from_bytes(email_body)

                    body = self._get_email_body(msg)

                    messages.append(EmailMessage(
                        subject=msg.get("Subject", ""),
                        sender=msg.get("From", ""),
                        recipients=msg.get("To", "").split(","),
                        body=body,
                        date=msg.get("Date", ""),
                        message_id=msg.get("Message-ID", ""),
                    ))

            self.logger.info(f"Found {len(messages)} matching emails")
            return messages

        except Exception as e:
            self.logger.error(f"Failed to search emails: {e}")
            raise

    def download_attachments(
        self,
        folder: str = "INBOX",
        output_dir: str = "./attachments",
        limit: int = 10,
    ) -> List[str]:
        """Download attachments from recent emails.

        Args:
            folder: Mailbox folder
            output_dir: Directory to save attachments
            limit: Maximum emails to check

        Returns:
            List of downloaded file paths
        """
        downloaded = []
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            with imaplib.IMAP4_SSL(self.imap_server, self.imap_port) as mail:
                mail.login(self.username, self.password)
                mail.select(folder)

                _, message_ids = mail.search(None, "ALL")
                ids = message_ids[0].split()[-limit:]

                for msg_id in ids:
                    _, msg_data = mail.fetch(msg_id, "(RFC822)")
                    email_body = msg_data[0][1]
                    msg = email.message_from_bytes(email_body)

                    for part in msg.walk():
                        if part.get_content_maintype() == "multipart":
                            continue

                        filename = part.get_filename()
                        if filename:
                            file_path = output_path / filename
                            with open(file_path, "wb") as f:
                                f.write(part.get_payload(decode=True))
                            downloaded.append(str(file_path))

            self.logger.info(f"Downloaded {len(downloaded)} attachments")
            return downloaded

        except Exception as e:
            self.logger.error(f"Failed to download attachments: {e}")
            raise

    def mark_as_read(self, folder: str, message_id: str) -> bool:
        """Mark an email as read."""
        try:
            with imaplib.IMAP4_SSL(self.imap_server, self.imap_port) as mail:
                mail.login(self.username, self.password)
                mail.select(folder)
                mail.store(message_id, "+FLAGS", "\\Seen")
            return True
        except Exception as e:
            self.logger.error(f"Failed to mark as read: {e}")
            return False

    def delete(self, folder: str, message_id: str) -> bool:
        """Delete an email."""
        try:
            with imaplib.IMAP4_SSL(self.imap_server, self.imap_port) as mail:
                mail.login(self.username, self.password)
                mail.select(folder)
                mail.store(message_id, "+FLAGS", "\\Deleted")
                mail.expunge()
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete email: {e}")
            return False
