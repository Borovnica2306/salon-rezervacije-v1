# Beauty Salon Booking App - PRD

## Originalni Problem Statement
Aplikacija za rezervaciju termina u beauty salonu. Klijenti biraju usluge i radnika bez registracije. Admin dashboard za upravljanje. Tamna tema, mobile-first dizajn, PWA.

## Korisnici
1. **Klijent** - Zakazuje termin bez registracije
2. **Salon-Admin** (admin@salon.com / Admin123!) - Upravlja salonom
3. **Super-Admin** (Bornaja23@gmail.com / Markonijus23!) - System Config, master kategorije

## Core Requirements — All Completed
- [x] Multi-step booking wizard (4 koraka)
- [x] Izbor usluga sa automatskim sabiranjem trajanja
- [x] Izbor radnika po usluzi (split-booking)
- [x] Kalendar sa slobodnim terminima
- [x] Potvrda rezervacije bez registracije
- [x] JWT autentifikacija (admin + super_admin)
- [x] CRUD za usluge i radnike
- [x] Safe Delete radnika + Confirmation dialog
- [x] Booking ID (#A1B2) za svaku rezervaciju
- [x] Success page sa uplatnicom
- [x] Admin kolona "Status uplate" (Čeka uplatu / Plaćeno)
- [x] Blacklist telefona + Limit 3 dnevno
- [x] "Moje rezervacije" za klijente (24h otkazivanje)
- [x] Multi-Level Admin (super_admin + admin)
- [x] Master Category Switch (7 kategorija)
- [x] System Config stranica (samo za super_admin)
- [x] Smart Pairing Logic — Fiksni 15-min Social Buffer
- [x] Anti-Conflict validacija (po telefonu)
- [x] All-or-Nothing lanac
- [x] Refaktorisanje server.py u module
- [x] Vizuelni Timeline na confirmation stranici
- [x] "Dodaj u kalendar" (Google Calendar + ICS)
- [x] Admin: Worker filter bar
- [x] Admin: Visual Social Buffer u karticama
- [x] Admin: Cancel confirmation dialog
- [x] Admin: Manual Booking (Ručna Rezervacija) — 3-step modal sa force-override

## Arhitektura
```
/app/backend/
├── server.py, database.py, models.py, auth.py, logic.py, routes.py
/app/frontend/src/pages/
├── BookingPage.jsx, AdminDashboard.jsx, AdminLogin.jsx
```

## API Endpoints
- POST /api/admin/reservations — Admin manual booking (sa force override)
- POST /api/reservations — Client booking
- POST /api/reservations/available-slots — Slot availability
- GET /api/reservations — Admin listing (filter by date + worker_id)
- GET /api/services, /api/workers, /api/settings, /api/categories

## Backlog
- P2: Viber notifikacije (placeholder u logic.py)
- Budući zadaci: po zahtevu korisnika
