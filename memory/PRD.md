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
- [x] Izbor radnika po usluzi (split-booking sa max 15-min gap)
- [x] Kalendar sa slobodnim terminima
- [x] Potvrda rezervacije bez registracije
- [x] JWT autentifikacija (admin + super_admin)
- [x] CRUD za usluge i radnike
- [x] Safe Delete radnika (hard delete + referential integrity check)
- [x] Confirmation dialog pre brisanja radnika
- [x] Booking ID (#A1B2) za svaku rezervaciju
- [x] Success page sa uplatnicom
- [x] Admin kolona "Status uplate" (Čeka uplatu / Plaćeno)
- [x] Blacklist telefona + Limit 3 dnevno
- [x] "Moje rezervacije" za klijente (24h otkazivanje)
- [x] Multi-Level Admin (super_admin + admin)
- [x] Master Category Switch (7 kategorija, soft-hide logika)
- [x] System Config stranica (samo za super_admin)
- [x] Seed_completed flag (sprečava re-seeding radnika nakon restarta)
- [x] Smart Pairing Logic — Fiksni 15-min Social Buffer između vezanih usluga
- [x] Anti-Conflict validacija — Sprečava preklapanje termina istog klijenta (po telefonu)
- [x] All-or-Nothing lanac — Termin se prikazuje samo ako je ceo niz izvodljiv
- [x] Frontend totalDuration uključuje bufere (15min x broj prelaza)
- [x] Refaktorisanje server.py u module (database, models, auth, logic, routes)
- [x] Vizuelni Timeline na confirmation stranici (emoji, usluge, pauze, cene)
- [x] "Dodaj u kalendar" dugmad (Google Calendar link + ICS download za Apple/Outlook)
- [x] Admin Dashboard: Worker filter bar (pill dugmad za filtriranje po radniku)
- [x] Admin Dashboard: Visual Social Buffer u karticama (mini-timeline sa ☕ pauzom)
- [x] Admin Dashboard: Cancel confirmation dialog (sa detaljima rezervacije)
- [x] Backend: Multi-worker $or query za filtriranje rezervacija po radniku

## Arhitektura (Modularna)
```
/app/backend/
├── server.py      # App init, CORS, startup/shutdown
├── database.py    # MongoDB konekcija, MASTER_CATEGORIES
├── models.py      # Svi Pydantic modeli
├── auth.py        # JWT, lozinke, get_current_user
├── logic.py       # Smart Pairing, slotovi, Viber placeholder
└── routes.py      # Svi API endpoint-i
/app/frontend/src/pages/
├── BookingPage.jsx      # Klijentski booking wizard + confirmation timeline
├── AdminDashboard.jsx   # Admin panel sa filterima i timeline-om
└── AdminLogin.jsx       # JWT login forma
```

## Current Active Workers
- Suzana (hair), Milena (nails), Slobodan (massage)
- Dragana (makeup), Dobrila (depilation), Jovana (cosmetics), Dejan (eyebrows)

## Backlog
- P2: Viber notifikacije (placeholder funkcije već postoje u logic.py)
- Budući zadaci: po zahtevu korisnika
