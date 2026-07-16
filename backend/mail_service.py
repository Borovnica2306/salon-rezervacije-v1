import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from database import db

logger = logging.getLogger(__name__)

PAYMENT_MODE = os.environ.get("PAYMENT_MODE", "PI_ECOSYSTEM")


def _get_smtp_config_sync(db_settings=None):
    """Get SMTP config from DB settings first, then env fallback."""
    cfg = {
        "server": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": os.environ.get("SMTP_USER", ""),
        "password": os.environ.get("SMTP_PASSWORD", ""),
    }
    if db_settings:
        cfg["server"] = db_settings.get("smtp_server") or cfg["server"]
        cfg["port"] = db_settings.get("smtp_port") or cfg["port"]
        cfg["user"] = db_settings.get("smtp_user") or cfg["user"]
        cfg["password"] = db_settings.get("smtp_password") or cfg["password"]
    return cfg


def _build_html(
    salon_name: str,
    booking_id: str,
    client_name: str,
    date: str,
    time: str,
    end_time: str,
    service_lines: list[dict],
    total_price: float,
    total_duration: int,
):
    service_rows = ""
    for s in service_lines:
        service_rows += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #2A2A2D;color:#E5E7EB;font-size:14px;">{s['service_name']}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #2A2A2D;color:#38BDF8;font-size:14px;text-align:right;">{s['worker_name']}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background-color:#0A0D14;font-family:Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:24px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:500px;background-color:#131825;border-radius:16px;overflow:hidden;">

  <tr><td style="background:linear-gradient(135deg,#1E293B,#131825);padding:32px 24px;text-align:center;">
    <h1 style="margin:0;color:#F0F9FF;font-size:20px;font-weight:400;font-family:Georgia,serif;">{salon_name}</h1>
    <p style="margin:8px 0 0;color:#38BDF8;font-size:13px;">Potvrda rezervacije</p>
  </td></tr>

  <tr><td style="padding:24px;">
    <p style="margin:0 0 8px;color:#94A3B8;font-size:12px;text-transform:uppercase;letter-spacing:0.1em;">Rezervacija</p>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;">
      <tr>
        <td style="padding:12px 0;color:#94A3B8;font-size:13px;border-bottom:1px solid #2A2A2D;">ID</td>
        <td style="padding:12px 0;color:#F0F9FF;font-size:13px;text-align:right;border-bottom:1px solid #2A2A2D;">#{booking_id}</td>
      </tr>
      <tr>
        <td style="padding:12px 0;color:#94A3B8;font-size:13px;border-bottom:1px solid #2A2A2D;">Klijent</td>
        <td style="padding:12px 0;color:#F0F9FF;font-size:13px;text-align:right;border-bottom:1px solid #2A2A2D;">{client_name}</td>
      </tr>
      <tr>
        <td style="padding:12px 0;color:#94A3B8;font-size:13px;border-bottom:1px solid #2A2A2D;">Datum</td>
        <td style="padding:12px 0;color:#F0F9FF;font-size:13px;text-align:right;border-bottom:1px solid #2A2A2D;">{date}</td>
      </tr>
      <tr>
        <td style="padding:12px 0;color:#94A3B8;font-size:13px;border-bottom:1px solid #2A2A2D;">Vreme</td>
        <td style="padding:12px 0;color:#F0F9FF;font-size:13px;text-align:right;border-bottom:1px solid #2A2A2D;">{time} - {end_time}</td>
      </tr>
      <tr>
        <td style="padding:12px 0;color:#94A3B8;font-size:13px;border-bottom:1px solid #2A2A2D;">Trajanje</td>
        <td style="padding:12px 0;color:#F0F9FF;font-size:13px;text-align:right;border-bottom:1px solid #2A2A2D;">{total_duration} min</td>
      </tr>
      <tr>
        <td style="padding:12px 0;color:#94A3B8;font-size:13px;">Ukupno</td>
        <td style="padding:12px 0;color:#38BDF8;font-size:15px;font-weight:600;text-align:right;">{total_price} π</td>
      </tr>
    </table>

    <p style="margin:0 0 8px;color:#94A3B8;font-size:12px;text-transform:uppercase;letter-spacing:0.1em;">Usluge</p>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#0A0D14;border-radius:8px;overflow:hidden;">
      <tr>
        <th style="padding:10px 12px;text-align:left;color:#94A3B8;font-size:12px;font-weight:500;border-bottom:1px solid #2A2A2D;">Usluga</th>
        <th style="padding:10px 12px;text-align:right;color:#94A3B8;font-size:12px;font-weight:500;border-bottom:1px solid #2A2A2D;">Radnik</th>
      </tr>
      {service_rows}
    </table>
  </td></tr>

  <tr><td style="padding:0 24px 20px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.25);border-radius:12px;">
      <tr><td style="padding:24px;text-align:center;">
        <p style="margin:0 0 4px;color:#4ADE80;font-size:16px;font-weight:600;">Rezervacija potvrđena</p>
        <p style="margin:0;color:#94A3B8;font-size:13px;">Vaš termin je uspešno zakazan.</p>
      </td></tr>
    </table>
  </td></tr>

  <tr><td style="padding:0 24px 32px;text-align:center;">
    <p style="margin:0;color:#64748B;font-size:12px;">Hvala vam na poverenju!</p>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""


async def send_booking_confirmation_email(
    to_email: str,
    salon_name: str,
    booking_id: str,
    client_name: str,
    date: str,
    time: str,
    end_time: str,
    service_worker_pairs: list[dict],
    total_price: float,
    total_duration: int,
):
    logger.info(f"[EMAIL] Preparing to send booking #{booking_id} confirmation to: {to_email}")

    try:
        db_settings = await db.settings.find_one({"type": "salon"})
    except Exception:
        db_settings = None

    smtp_cfg = _get_smtp_config_sync(db_settings)
    if not smtp_cfg["user"] or not smtp_cfg["password"]:
        logger.warning("SMTP credentials not configured, skipping email send")
        return

    try:
        html = _build_html(
            salon_name=salon_name,
            booking_id=booking_id,
            client_name=client_name,
            date=date,
            time=time,
            end_time=end_time,
            service_lines=service_worker_pairs,
            total_price=total_price,
            total_duration=total_duration,
        )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Potvrda rezervacije #{booking_id} - {salon_name}"
        msg["From"] = smtp_cfg["user"]
        msg["To"] = to_email

        plain = f"Rezervacija #{booking_id} potvrđena. Datum: {date}, Vreme: {time}-{end_time}. Ukupno: {total_price} π."
        msg.attach(MIMEText(plain, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP(smtp_cfg["server"], smtp_cfg["port"], timeout=15) as server:
            server.starttls()
            server.login(smtp_cfg["user"], smtp_cfg["password"])
            server.sendmail(smtp_cfg["user"], to_email, msg.as_string())

        logger.info(f"[EMAIL] SUCCESS: Sent from {smtp_cfg['user']} to {to_email} for booking #{booking_id}")

    except Exception as e:
        logger.error(f"[EMAIL] FAILED: Could not send to {to_email} for booking #{booking_id}: {type(e).__name__}: {e}")
