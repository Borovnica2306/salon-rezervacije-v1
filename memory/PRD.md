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
- [x] IPS QR Kod Plaćanje — NBS standard, **dot decimal** (RSD2000.00)
- [x] Email polje + Async email notifikacija (QR in separate try-except)
- [x] Payment Tracking System — 3 statusa (pending → sent_for_verification → confirmed)
- [x] Viber Notifikacije + Daily Reminders + Lazy Cancel (3h)
- [x] Admin "Podsetnici za sutra" dugme + Viber CTA na potvrdi
- [x] SMTP & Viber Admin Settings — DB-first, env fallback
- [x] **IPS QR Fix** — dot decimal (RSD2000.00), async email, QR fault-tolerant

## Backlog
- P3: Drag & drop na admin timeline gridu za preraspoređivanje
