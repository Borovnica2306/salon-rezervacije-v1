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
- [x] Daily Timeline Grid — Worker kolone, 30-min redovi, obojeni blokovi
- [x] Auto-Scroll na current_time, Detail Dialog, Archive Tab
- [x] Mobile Timeline Grid — horizontalni skrol, sticky time kolona
- [x] Touch Targets 48px, Dalje Button Fix, Edit Mode
- [x] Visual Category Cards — realistične Unsplash slike sa gradient overlay
- [x] IPS QR Kod Plaćanje — NBS standard, QRCodeSVG (frontend + backend)
- [x] Email polje klijenta — obavezan input, regex validacija, čuva se lowercase
- [x] Email notifikacija — BackgroundTasks, SMTP, HTML template sa QR CID
- [x] **Payment Tracking System** — 3 statusa (pending → sent_for_verification → confirmed)
  - Klijent: "Potvrdi uplatu avansa" dugme u Moje Rezervacije
  - Admin: "Potvrdi uplatu" zeleno dugme u Detail Dialog
  - Grid blokovi: žuta za čekanje provere, zelena za potvrđeno

## Backlog
- P1: Viber notifikacije (placeholder u logic.py)
- P3: Drag & drop na admin timeline gridu za preraspoređivanje
