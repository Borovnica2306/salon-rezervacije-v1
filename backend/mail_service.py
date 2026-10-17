import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from database import db

logger = logging.getLogger(__name__)

PAYMENT_MODE = os.environ.get("PAYMENT_MODE", "PI_ECOSYSTEM")

# Email i18n strings per language
EMAIL_STRINGS = {
    "sr": {
        "subject": "Potvrda rezervacije #{bid} - {salon}",
        "confirmation": "Potvrda rezervacije",
        "booking": "Rezervacija",
        "id": "ID",
        "client": "Klijent",
        "date": "Datum",
        "time": "Vreme",
        "duration": "Trajanje",
        "total": "Ukupno",
        "services": "Usluge",
        "service": "Usluga",
        "worker": "Radnik",
        "confirmed": "Rezervacija potvrđena",
        "confirmed_desc": "Vaš termin je uspešno zakazan.",
        "thanks": "Hvala vam na poverenju!",
        "plain": "Rezervacija #{bid} potvrđena. Datum: {date}, Vreme: {time}-{end}. Ukupno: {price} π.",
    },
    "en": {
        "subject": "Booking confirmation #{bid} - {salon}",
        "confirmation": "Booking Confirmation",
        "booking": "Booking",
        "id": "ID",
        "client": "Client",
        "date": "Date",
        "time": "Time",
        "duration": "Duration",
        "total": "Total",
        "services": "Services",
        "service": "Service",
        "worker": "Worker",
        "confirmed": "Booking confirmed",
        "confirmed_desc": "Your appointment has been successfully scheduled.",
        "thanks": "Thank you for your trust!",
        "plain": "Booking #{bid} confirmed. Date: {date}, Time: {time}-{end}. Total: {price} π.",
    },
    "id": {
        "subject": "Konfirmasi reservasi #{bid} - {salon}",
        "confirmation": "Konfirmasi Reservasi",
        "booking": "Reservasi",
        "id": "ID",
        "client": "Klien",
        "date": "Tanggal",
        "time": "Waktu",
        "duration": "Durasi",
        "total": "Total",
        "services": "Layanan",
        "service": "Layanan",
        "worker": "Pekerja",
        "confirmed": "Reservasi dikonfirmasi",
        "confirmed_desc": "Jadwal Anda telah berhasil dibuat.",
        "thanks": "Terima kasih atas kepercayaan Anda!",
        "plain": "Reservasi #{bid} dikonfirmasi. Tanggal: {date}, Waktu: {time}-{end}. Total: {price} π.",
    },
    "tl": {
        "subject": "Kumpirmasyon ng reserbasyon #{bid} - {salon}",
        "confirmation": "Kumpirmasyon ng Reserbasyon",
        "booking": "Reserbasyon",
        "id": "ID",
        "client": "Kliyente",
        "date": "Petsa",
        "time": "Oras",
        "duration": "Tagal",
        "total": "Kabuuan",
        "services": "Mga Serbisyo",
        "service": "Serbisyo",
        "worker": "Manggagawa",
        "confirmed": "Nakumpirma ang reserbasyon",
        "confirmed_desc": "Matagumpay na na-schedule ang iyong appointment.",
        "thanks": "Salamat sa iyong tiwala!",
        "plain": "Reserbasyon #{bid} nakumpirma. Petsa: {date}, Oras: {time}-{end}. Kabuuan: {price} π.",
    },
    "pt-BR": {
        "subject": "Confirmação de reserva #{bid} - {salon}",
        "confirmation": "Confirmação de Reserva",
        "booking": "Reserva",
        "id": "ID",
        "client": "Cliente",
        "date": "Data",
        "time": "Horário",
        "duration": "Duração",
        "total": "Total",
        "services": "Serviços",
        "service": "Serviço",
        "worker": "Profissional",
        "confirmed": "Reserva confirmada",
        "confirmed_desc": "Seu agendamento foi realizado com sucesso.",
        "thanks": "Obrigado pela sua confiança!",
        "plain": "Reserva #{bid} confirmada. Data: {date}, Horário: {time}-{end}. Total: {price} π.",
    },
    "es": {
        "subject": "Confirmación de reserva #{bid} - {salon}",
        "confirmation": "Confirmación de Reserva",
        "booking": "Reserva",
        "id": "ID",
        "client": "Cliente",
        "date": "Fecha",
        "time": "Hora",
        "duration": "Duración",
        "total": "Total",
        "services": "Servicios",
        "service": "Servicio",
        "worker": "Profesional",
        "confirmed": "Reserva confirmada",
        "confirmed_desc": "Su cita ha sido programada exitosamente.",
        "thanks": "¡Gracias por su confianza!",
        "plain": "Reserva #{bid} confirmada. Fecha: {date}, Hora: {time}-{end}. Total: {price} π.",
    },
    "fr": {
        "subject": "Confirmation de réservation #{bid} - {salon}",
        "confirmation": "Confirmation de Réservation",
        "booking": "Réservation",
        "id": "ID",
        "client": "Client",
        "date": "Date",
        "time": "Heure",
        "duration": "Durée",
        "total": "Total",
        "services": "Services",
        "service": "Service",
        "worker": "Professionnel",
        "confirmed": "Réservation confirmée",
        "confirmed_desc": "Votre rendez-vous a été programmé avec succès.",
        "thanks": "Merci pour votre confiance !",
        "plain": "Réservation #{bid} confirmée. Date : {date}, Heure : {time}-{end}. Total : {price} π.",
    },
}


def _get_email_strings(lang: str) -> dict:
    return EMAIL_STRINGS.get(lang, EMAIL_STRINGS["sr"])


def _get_smtp_config_sync(db_settings=None):
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
    lang: str = "sr",
):
    s = _get_email_strings(lang)

    service_rows = ""
    for svc in service_lines:
        service_rows += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #2A2A2D;color:#E5E7EB;font-size:14px;">{svc['service_name']}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #2A2A2D;color:#38BDF8;font-size:14px;text-align:right;">{svc['worker_name']}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background-color:#0A0D14;font-family:Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:24px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:500px;background-color:#131825;border-radius:16px;overflow:hidden;">

  <tr><td style="background:linear-gradient(135deg,#1E293B,#131825);padding:32px 24px;text-align:center;">
    <h1 style="margin:0;color:#F0F9FF;font-size:20px;font-weight:400;font-family:Georgia,serif;">{salon_name}</h1>
    <p style="margin:8px 0 0;color:#38BDF8;font-size:13px;">{s['confirmation']}</p>
  </td></tr>

  <tr><td style="padding:24px;">
    <p style="margin:0 0 8px;color:#94A3B8;font-size:12px;text-transform:uppercase;letter-spacing:0.1em;">{s['booking']}</p>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;">
      <tr>
        <td style="padding:12px 0;color:#94A3B8;font-size:13px;border-bottom:1px solid #2A2A2D;">{s['id']}</td>
        <td style="padding:12px 0;color:#F0F9FF;font-size:13px;text-align:right;border-bottom:1px solid #2A2A2D;">#{booking_id}</td>
      </tr>
      <tr>
        <td style="padding:12px 0;color:#94A3B8;font-size:13px;border-bottom:1px solid #2A2A2D;">{s['client']}</td>
        <td style="padding:12px 0;color:#F0F9FF;font-size:13px;text-align:right;border-bottom:1px solid #2A2A2D;">{client_name}</td>
      </tr>
      <tr>
        <td style="padding:12px 0;color:#94A3B8;font-size:13px;border-bottom:1px solid #2A2A2D;">{s['date']}</td>
        <td style="padding:12px 0;color:#F0F9FF;font-size:13px;text-align:right;border-bottom:1px solid #2A2A2D;">{date}</td>
      </tr>
      <tr>
        <td style="padding:12px 0;color:#94A3B8;font-size:13px;border-bottom:1px solid #2A2A2D;">{s['time']}</td>
        <td style="padding:12px 0;color:#F0F9FF;font-size:13px;text-align:right;border-bottom:1px solid #2A2A2D;">{time} - {end_time}</td>
      </tr>
      <tr>
        <td style="padding:12px 0;color:#94A3B8;font-size:13px;border-bottom:1px solid #2A2A2D;">{s['duration']}</td>
        <td style="padding:12px 0;color:#F0F9FF;font-size:13px;text-align:right;border-bottom:1px solid #2A2A2D;">{total_duration} min</td>
      </tr>
      <tr>
        <td style="padding:12px 0;color:#94A3B8;font-size:13px;">{s['total']}</td>
        <td style="padding:12px 0;color:#38BDF8;font-size:15px;font-weight:600;text-align:right;">{total_price} π</td>
      </tr>
    </table>

    <p style="margin:0 0 8px;color:#94A3B8;font-size:12px;text-transform:uppercase;letter-spacing:0.1em;">{s['services']}</p>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#0A0D14;border-radius:8px;overflow:hidden;">
      <tr>
        <th style="padding:10px 12px;text-align:left;color:#94A3B8;font-size:12px;font-weight:500;border-bottom:1px solid #2A2A2D;">{s['service']}</th>
        <th style="padding:10px 12px;text-align:right;color:#94A3B8;font-size:12px;font-weight:500;border-bottom:1px solid #2A2A2D;">{s['worker']}</th>
      </tr>
      {service_rows}
    </table>
  </td></tr>

  <tr><td style="padding:0 24px 20px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.25);border-radius:12px;">
      <tr><td style="padding:24px;text-align:center;">
        <p style="margin:0 0 4px;color:#4ADE80;font-size:16px;font-weight:600;">{s['confirmed']}</p>
        <p style="margin:0;color:#94A3B8;font-size:13px;">{s['confirmed_desc']}</p>
      </td></tr>
    </table>
  </td></tr>

  <tr><td style="padding:0 24px 32px;text-align:center;">
    <p style="margin:0;color:#64748B;font-size:12px;">{s['thanks']}</p>
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
    lang: str = "sr",
):
    logger.info(f"[EMAIL] Preparing to send booking #{booking_id} confirmation to: {to_email} (lang={lang})")

    try:
        db_settings = await db.settings.find_one({"type": "salon"})
    except Exception:
        db_settings = None

    smtp_cfg = _get_smtp_config_sync(db_settings)
    if not smtp_cfg["user"] or not smtp_cfg["password"]:
        logger.warning("SMTP credentials not configured, skipping email send")
        return

    s = _get_email_strings(lang)

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
            lang=lang,
        )

        subject = s["subject"].format(bid=booking_id, salon=salon_name)
        plain = s["plain"].format(bid=booking_id, date=date, time=time, end=end_time, price=total_price)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_cfg["user"]
        msg["To"] = to_email

        msg.attach(MIMEText(plain, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP(smtp_cfg["server"], smtp_cfg["port"], timeout=15) as server:
            server.starttls()
            server.login(smtp_cfg["user"], smtp_cfg["password"])
            server.sendmail(smtp_cfg["user"], to_email, msg.as_string())

        logger.info(f"[EMAIL] SUCCESS: Sent from {smtp_cfg['user']} to {to_email} for booking #{booking_id} (lang={lang})")

    except Exception as e:
        logger.error(f"[EMAIL] FAILED: Could not send to {to_email} for booking #{booking_id}: {type(e).__name__}: {e}")
