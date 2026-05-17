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
- [x] Modularna arhitektura (server, database, models, auth, logic, routes, mail_service)
- [x] Vizuelni Timeline + Add to Calendar (Google + ICS)
- [x] Standardizacija formata telefona (+381, zero-strip)
- [x] Striktna per-worker boundary provera radnog vremena
- [x] Admin Manual Booking (3-step modal + force override)
- [x] Daily Timeline Grid + Auto-Scroll + Detail Dialog + Archive Tab
- [x] Mobile Timeline Grid — horizontalni skrol, sticky time kolona
- [x] Touch Targets 48px, Edit Mode, Visual Category Cards
- [x] IPS QR Kod Plaćanje — NBS standard, QRCodeSVG
- [x] Email polje klijenta + Email notifikacija (BackgroundTasks, SMTP, QR CID)
- [x] Payment Tracking System — 3 statusa (pending → sent_for_verification → confirmed)
- [x] **Viber Notifikacije** — httpx + Viber Bot API, graceful fallback bez tokena
- [x] **Lazy Cancel** — Auto-otkazivanje neplaćenih rezervacija posle 3h (UNPAID_CANCEL_HOURS=3)
- [x] **Daily Reminders** — Admin trigger endpoint, Beograd timezone, 3 tipa poruka

## Architecture
```
/app/backend/
├── server.py        # App init, CORS, seed
├── database.py      # MongoDB connection
├── models.py        # Pydantic schemas
├── auth.py          # JWT logic
├── logic.py         # Smart Pairing, IPS QR, Viber, Lazy Cancel, Reminders
├── routes.py        # API endpoints
└── mail_service.py  # SMTP email with QR CID
```

## Backlog
- Frontend: Dodaj dugme "Pošalji podsetnike" na Admin Dashboard
- Konfiguracija VIBER_TOKEN (korisnik još nije dao token)
- Konfiguracija SMTP kredencijala (korisnik odložio)
- P3: Drag & drop na admin timeline gridu za preraspoređivanje
