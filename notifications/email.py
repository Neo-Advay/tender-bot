# notifications/email.py

import os
import smtplib
import logging
from email.message import EmailMessage
from typing import Iterable, Optional

from models.canonical_tender import CanonicalTender
from core.config_loader import load_config

logger = logging.getLogger(__name__)


def _cfg():
    config = load_config()
    email_cfg = (config.get("notifications", {}) or {}).get("email", {}) or {}
    return config, email_cfg


def _get_smtp_credentials(email_cfg: dict) -> tuple[str, str]:
    user_env = email_cfg.get("username_env", "OUTLOOK_SMTP_USERNAME")
    pass_env = email_cfg.get("password_env", "OUTLOOK_SMTP_PASSWORD")
    username = os.getenv(user_env, "")
    password = os.getenv(pass_env, "")
    if not username or not password:
        raise RuntimeError(
            f"Missing SMTP credentials in env. Set {user_env} and {pass_env}."
        )
    return username, password


def _render_subject(source: str, new_count: int, updated_count: int) -> str:
    parts = []
    if new_count:
        parts.append(f"{new_count} new")
    if updated_count:
        parts.append(f"{updated_count} updated")
    suffix = ", ".join(parts) if parts else "no changes"
    return f"[Tender Bot] {source}: {suffix}"


def _render_text_body(tenders: list[CanonicalTender], source: str) -> str:
    lines = [f"Tender Bot notification ({source})", ""]
    for t in tenders:
        score = getattr(t, "score", None)
        cat = getattr(t, "score_category", None)
        score_part = f"[{cat} {score:.1f}]" if score is not None and cat else ""
        lines.append(f"- {score_part} {t.title}".strip())
        lines.append(f"  Buyer: {t.buyer_name} | Country: {t.buyer_country}")
        lines.append(f"  Pub date: {t.publication_date} | Notice type: {t.notice_type}")
        lines.append(f"  Link: {t.url}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _render_html_body(tenders: list[CanonicalTender], source: str) -> str:
    def esc(x: Optional[str]) -> str:
        return (
            (x or "")
            .replace("&", "&amp;")
            .replace("<​", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    rows = []
    for t in tenders:
        score = getattr(t, "score", None)
        cat = getattr(t, "score_category", None)
        score_txt = f"{cat} {score:.1f}" if score is not None and cat else ""
        rows.append(f"""
          <tr>
            <td style="padding:8px;border-bottom:1px solid #eee;white-space:nowrap;">{esc(score_txt)}</td>
            <td style="padding:8px;border-bottom:1px solid #eee;">
              <div style="font-weight:600;">{esc(t.title)}</div>
              <div style="color:#555;font-size:12px;">
                Buyer: {esc(t.buyer_name)} | {esc(t.buyer_country)} |
                Pub: {esc(t.publication_date)} | Type: {esc(t.notice_type)}
              </div>
              <div style="margin-top:6px;">
                <a href="{esc(t.url)}">{esc(t.url)}</a>
              </div>
            </td>
          </tr>
        """)

    html = f"""
    <html>
      <body style="font-family:Arial, sans-serif;">
        <h3 style="margin:0 0 12px 0;">Tender Bot notification ({esc(source)})</h3>
        <table style="border-collapse:collapse;width:100%;max-width:900px;">
          <thead>
            <tr>
              <th style="text-align:left;padding:8px;border-bottom:2px solid #ddd;">Score</th>
              <th style="text-align:left;padding:8px;border-bottom:2px solid #ddd;">Tender</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows) if rows else '<tr><td colspan="2" style="padding:8px;">No items</td></tr>'}
          </tbody>
        </table>
      </body>
    </html>
    """
    return html


def send_email(subject: str, text_body: str, html_body: Optional[str] = None) -> None:
    _, email_cfg = _cfg()
    if not email_cfg.get("enabled", True):
        logger.info("[Email] Email notifications disabled in config.")
        return

    smtp_host = email_cfg.get("smtp_host", "smtp.office365.com")
    smtp_port = int(email_cfg.get("smtp_port", 587))
    use_starttls = bool(email_cfg.get("use_starttls", True))

    from_addr = email_cfg.get("from_address")
    to_addrs = email_cfg.get("to_addresses") or []
    if not from_addr or not to_addrs:
        raise RuntimeError("Email from_address/to_addresses missing in config.yaml")

    username, password = _get_smtp_credentials(email_cfg)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    msg.set_content(text_body)

    if html_body:
        msg.add_alternative(html_body, subtype="html")

    logger.info(f"[Email] Sending email via {smtp_host}:{smtp_port} to {to_addrs}")
    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.ehlo()
        if use_starttls:
            server.starttls()
            server.ehlo()
        server.login(username, password)
        server.send_message(msg)

    logger.info("[Email] Email sent successfully.")


def notify_tenders(
    source: str,
    tenders: Iterable[CanonicalTender],
    new_count: int,
    updated_count: int,
) -> None:
    tenders = list(tenders)
    if not tenders:
        logger.info("[Email] No tenders to notify.")
        return

    _, email_cfg = _cfg()
    max_items = int(email_cfg.get("max_items", 50))
    tenders = tenders[:max_items]

    subject = _render_subject(source=source, new_count=new_count, updated_count=updated_count)
    text_body = _render_text_body(tenders, source=source)
    html_body = _render_html_body(tenders, source=source)
    send_email(subject, text_body, html_body)