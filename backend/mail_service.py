import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from logic import (
    generate_ips_qr_image, clean_bank_account, format_ips_amount,
)
from database import db

logger = logging.getLogger(__name__)


def _get_smtp_config_sync(db_settings=None):
    """Get SMTP config from DB settings first, then env fallback."""
    if db_settings:
        user = db_settings.get("smtp_user", "")
        password = db_settings.get("smtp_password", "")
        if user and password:
            return {
                "server": db_settings.get("smtp_server", "smtp.gmail.com"),
                "port": int(db_settings.get("smtp_port", 587)),
                "user": user,
                "password": password,
            }
    return {
        "server": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": os.environ.get("SMTP_USER", ""),
        "password": os.environ.get("SMTP_PASSWORD", ""),
    }


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
    bank_account: str,
    payment_recipient: str,
):
    account_clean = clean_bank_account(bank_account)
    account_fmt = f"{account_clean[:3]}-{account_clean[3:16]}-{account_clean[16:]}"
    amount_fmt = format_ips_amount(total_price)
    reference = f"99{booking_id}"

    service_rows = ""
    for s in service_lines:
        service_rows += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #2A2A2D;color:#E5E7EB;font-size:14px;">{s['service_name']}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #2A2A2D;color:#C5A880;font-size:14px;text-align:right;">{s['worker_name']}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="sr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#0A0A0B;font-family:Arial,Helvetica,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#0A0A0B;">
<tr><td align="center" style="padding:24px 16px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;background-color:#141416;border-radius:16px;border:1px solid #2A2A2D;">

  <!-- Header -->
  <tr><td style="padding:32px 24px 16px;text-align:center;">
    <h1 style="margin:0;font-size:28px;font-weight:300;color:#FFFFFF;font-family:Georgia,serif;">{salon_name}</h1>
    <p style="margin:8px 0 0;color:#C5A880;font-size:14px;">Potvrda rezervacije</p>
  </td></tr>

  <!-- Booking ID -->
  <tr><td style="padding:0 24px 16px;text-align:center;">
    <span style="display:inline-block;background-color:rgba(197,168,128,0.1);border:1px solid rgba(197,168,128,0.3);border-radius:8px;padding:8px 16px;">
      <span style="color:#9CA3AF;font-size:13px;">Vaš ID: </span>
      <span style="color:#C5A880;font-size:18px;font-weight:bold;font-family:monospace;">#{booking_id}</span>
    </span>
  </td></tr>

  <!-- Details -->
  <tr><td style="padding:0 24px 20px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#0A0A0B;border-radius:12px;">
      <tr>
        <td style="padding:12px;color:#9CA3AF;font-size:13px;">Klijent:</td>
        <td style="padding:12px;color:#FFFFFF;font-size:14px;text-align:right;">{client_name}</td>
      </tr>
      <tr>
        <td style="padding:12px;color:#9CA3AF;font-size:13px;border-top:1px solid #2A2A2D;">Datum:</td>
        <td style="padding:12px;color:#FFFFFF;font-size:14px;text-align:right;border-top:1px solid #2A2A2D;">{date}</td>
      </tr>
      <tr>
        <td style="padding:12px;color:#9CA3AF;font-size:13px;border-top:1px solid #2A2A2D;">Vreme:</td>
        <td style="padding:12px;color:#FFFFFF;font-size:14px;text-align:right;border-top:1px solid #2A2A2D;">{time} - {end_time}</td>
      </tr>
      <tr>
        <td style="padding:12px;color:#9CA3AF;font-size:13px;border-top:1px solid #2A2A2D;">Trajanje:</td>
        <td style="padding:12px;color:#FFFFFF;font-size:14px;text-align:right;border-top:1px solid #2A2A2D;">{total_duration} min</td>
      </tr>
    </table>
  </td></tr>

  <!-- Services -->
  <tr><td style="padding:0 24px 20px;">
    <p style="margin:0 0 8px;color:#9CA3AF;font-size:11px;text-transform:uppercase;letter-spacing:1px;">Usluge</p>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#0A0A0B;border-radius:12px;">
      {service_rows}
      <tr>
        <td style="padding:12px;color:#FFFFFF;font-size:14px;font-weight:bold;">Ukupno:</td>
        <td style="padding:12px;color:#C5A880;font-size:16px;font-weight:bold;text-align:right;">{total_price:,.0f} RSD</td>
      </tr>
    </table>
  </td></tr>

  <!-- QR Code Section -->
  <tr><td style="padding:0 24px 20px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#0A0A0B;border:1px solid rgba(197,168,128,0.2);border-radius:12px;">
      <tr><td style="padding:20px;text-align:center;">
        <p style="margin:0 0 4px;color:#C5A880;font-size:15px;font-weight:600;">Brzo plaćanje (IPS QR kod)</p>
        <p style="margin:0 0 16px;color:#9CA3AF;font-size:12px;">Skenirajte kod iz vaše mBanking aplikacije</p>
        <div style="display:inline-block;background:#FFFFFF;border-radius:12px;padding:12px;">
          <img src="cid:qrcode_image" alt="IPS QR kod" width="200" height="200" style="display:block;" />
        </div>
      </td></tr>
      <tr><td style="padding:0 20px 16px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="padding:10px 0;color:#9CA3AF;font-size:13px;border-top:1px solid #2A2A2D;">Račun:</td>
            <td style="padding:10px 0;color:#FFFFFF;font-size:13px;font-family:monospace;text-align:right;border-top:1px solid #2A2A2D;">{account_fmt}</td>
          </tr>
          <tr>
            <td style="padding:10px 0;color:#9CA3AF;font-size:13px;border-top:1px solid #2A2A2D;">Iznos:</td>
            <td style="padding:10px 0;color:#C5A880;font-size:13px;font-weight:600;text-align:right;border-top:1px solid #2A2A2D;">{amount_fmt}</td>
          </tr>
          <tr>
            <td style="padding:10px 0;color:#9CA3AF;font-size:13px;border-top:1px solid #2A2A2D;">Poziv na broj:</td>
            <td style="padding:10px 0;color:#FFFFFF;font-size:13px;font-family:monospace;text-align:right;border-top:1px solid #2A2A2D;">{reference}</td>
          </tr>
        </table>
      </td></tr>
    </table>
  </td></tr>

  <!-- Footer -->
  <tr><td style="padding:16px 24px 32px;text-align:center;">
    <p style="margin:0;color:#6B7280;font-size:12px;line-height:1.5;">
      Molimo pošaljite sliku uplatnice na Viber/Instagram salona radi konačne potvrde termina.
    </p>
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
    bank_account: str,
    payment_recipient: str,
):
    # Fetch DB settings for SMTP config
    try:
        db_settings = await db.settings.find_one({"type": "salon"})
    except Exception:
        db_settings = None

    smtp_cfg = _get_smtp_config_sync(db_settings)
    if not smtp_cfg["user"] or not smtp_cfg["password"]:
        logger.warning("SMTP credentials not configured, skipping email send")
        return

    try:
        # QR generation in its own try-except so failure doesn't block email
        qr_image_bytes = None
        try:
            qr_image_bytes = generate_ips_qr_image(
                bank_account=bank_account,
                recipient_name=payment_recipient or salon_name,
                amount=total_price,
                booking_id=booking_id,
            )
        except Exception as qr_err:
            logger.error(f"QR generation failed for booking #{booking_id}: {qr_err}")

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
            bank_account=bank_account,
            payment_recipient=payment_recipient,
        )

        msg = MIMEMultipart("related")
        msg["Subject"] = f"Potvrda rezervacije #{booking_id} - {salon_name}"
        msg["From"] = smtp_cfg["user"]
        msg["To"] = to_email

        msg_alt = MIMEMultipart("alternative")
        msg.attach(msg_alt)

        plain = f"Rezervacija #{booking_id} potvrđena. Datum: {date}, Vreme: {time}-{end_time}. Ukupno: {total_price:.0f} RSD."
        msg_alt.attach(MIMEText(plain, "plain", "utf-8"))
        msg_alt.attach(MIMEText(html, "html", "utf-8"))

        if qr_image_bytes:
            qr_img = MIMEImage(qr_image_bytes, _subtype="png")
            qr_img.add_header("Content-ID", "<qrcode_image>")
            qr_img.add_header("Content-Disposition", "inline", filename="qr_code.png")
            msg.attach(qr_img)

        with smtplib.SMTP(smtp_cfg["server"], smtp_cfg["port"], timeout=15) as server:
            server.starttls()
            server.login(smtp_cfg["user"], smtp_cfg["password"])
            server.sendmail(smtp_cfg["user"], to_email, msg.as_string())

        logger.info(f"Confirmation email sent to {to_email} for booking #{booking_id}")

    except Exception as e:
        logger.error(f"Failed to send confirmation email to {to_email}: {e}")
