# Beauty Salon Booking App - PRD

## Originalni Problem Statement
Aplikacija za rezervaciju termina u beauty salonu. Klijenti biraju usluge i radnika bez registracije. Admin dashboard za upravljanje. Tamna tema, mobile-first dizajn, PWA.

## Core Requirements — All Completed
- [x] Multi-step booking wizard (4 koraka)
- [x] Split-booking sa 15-min Social Buffer + All-or-Nothing
- [x] Smart Pairing + Anti-Conflict (po telefonu)
- [x] JWT auth (admin + super_admin) + Multi-Level Admin
- [x] CRUD za usluge/radnike + Safe Delete + Confirmation dialogs
- [x] Booking ID, Uplatnica, Payment Status toggle
- [x] Blacklist + Limit 3/dan + "Moje rezervacije" (24h otkazivanje)
- [x] Master Category Switch (7 kategorija)
- [x] Modularna arhitektura
- [x] Vizuelni Timeline + Add to Calendar (Google + ICS)
- [x] Standardizacija formata telefona (+381, zero-strip)
- [x] Striktna per-worker boundary provera radnog vremena
- [x] Admin Manual Booking (3-step modal + force override)
- [x] Daily Timeline Grid + Auto-Scroll + Detail Dialog + Archive Tab
- [x] Mobile Timeline Grid — horizontalni skrol, sticky time kolona
- [x] Touch Targets 48px, Edit Mode, Visual Category Cards
- [x] IPS QR Kod — NBS standard: pipe separator, comma decimal
- [x] Email notifikacija — async SMTP, QR fault-tolerant, DB-first credentials
- [x] Payment Tracking System — 3 statusa
- [x] Lazy Cancel — Auto-otkazivanje neplaćenih rezervacija posle 3h
- [x] Daily Reminders — Admin trigger endpoint (summary counts)
- [x] SMTP Admin Settings — DB-first, env fallback
- [x] **Viber Direct Chat** — viber://chat?number={phone}&draft={msg} umesto Bot API

## Architecture
```
/app/backend/
├── server.py, database.py, models.py, auth.py
├── logic.py         # Smart Pairing, IPS QR, Lazy Cancel, Reminders (NO Viber Bot)
├── routes.py        # API endpoints
└── mail_service.py  # Async SMTP email with QR CID
```

## Backlog
- P3: Drag & drop na admin timeline gridu za preraspoređivanje
