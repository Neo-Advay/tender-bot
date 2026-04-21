# pipeline/notifications.py

import logging
import smtplib
import ssl
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config_loader import load_config

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, mode="console"):
        self.mode = mode
        if mode == "smtp":
            config = load_config()
            smtp_cfg = config.get("smtp", {})
            self.host       = smtp_cfg.get("host")
            self.port       = int(smtp_cfg.get("port", 465))
            self.username   = smtp_cfg.get("username")
            self.password   = smtp_cfg.get("password")
            self.from_addr  = smtp_cfg.get("from_address")
            self.from_name  = smtp_cfg.get("from_name", "Tender Bot")
            self.recipients = smtp_cfg.get("recipients", [])

    def notify(self, tenders_with_status, source, db=None):
        """
        Send one batched email for all tenders in this run.
        Skips tenders already recorded in notifications_sent.
        tenders_with_status: list of (CanonicalTender, status) tuples
        """
        if not tenders_with_status:
            logger.info(f"[Notify] No tenders to notify for {source}")
            return

        # Filter out already-sent notifications
        if db:
            filtered = []
            for tender, status in tenders_with_status:
                if not db.is_notification_sent(tender.source, tender.external_id, status):
                    filtered.append((tender, status))
                else:
                    logger.info(f"[Notify] Skipping already-sent: {tender.external_id} ({status})")
            tenders_with_status = filtered

        if not tenders_with_status:
            logger.info(f"[Notify] All notifications already sent for {source}")
            return

        subject, body = self._format_batch(tenders_with_status, source)

        if self.mode == "console":
            print("\n" + "="*60)
            print(f"TENDER ALERT BATCH: {source} ({len(tenders_with_status)} tenders)")
            print("="*60)
            print(body)
            print("="*60 + "\n")
            if db:
                self._record_sent(db, tenders_with_status)

        elif self.mode == "smtp":
            success = self._send_smtp(subject, body)
            if success and db:
                self._record_sent(db, tenders_with_status)

    def _format_batch(self, tenders_with_status, source):
        """Formats a single email body for all tenders."""
        new_count     = sum(1 for _, s in tenders_with_status if s == "NEW")
        updated_count = sum(1 for _, s in tenders_with_status if s == "UPDATED")

        subject = f"[Tender Bot] {source} — {new_count} New, {updated_count} Updated"

        lines = [
            f"Tender Bot Run Summary — {source}",
            f"Run at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            f"New: {new_count}  |  Updated: {updated_count}",
            "=" * 60,
        ]

        for tender, status in tenders_with_status:
            lines += [
                f"",
                f"[{status}] [{tender.score_category}] Score: {tender.score}",
                f"Title:    {tender.title}",
                f"Buyer:    {tender.buyer_name} ({tender.buyer_country})",
                f"Pub Date: {tender.publication_date}",
                f"Deadline: {tender.deadline_date or 'N/A'}",
                f"Link:     {tender.url}",
                f"-" * 60,
            ]

        return subject, "\n".join(lines)

    def _send_smtp(self, subject, body):
        """Sends one email with the full batch."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = f"{self.from_name} <{self.from_addr}>"
            msg["To"]      = ", ".join(self.recipients)
            msg.attach(MIMEText(body, "plain", "utf-8"))

            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.host, self.port, context=context) as server:
                server.login(self.username, self.password)
                server.sendmail(self.from_addr, self.recipients, msg.as_string())

            logger.info(f"[Notify] Batch email sent — {len(self.recipients)} recipient(s)")
            return True
        except Exception as e:
            logger.error(f"[Notify] Failed to send batch email: {e}")
            return False

    def _record_sent(self, db, tenders_with_status):
        """Records each sent notification in the DB."""
        for tender, status in tenders_with_status:
            db.insert_notification_sent(tender.source, tender.external_id, status)