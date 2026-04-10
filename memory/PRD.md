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
- [x] Frontend totalDuration uključuje bufere (15min × broj prelaza)

## Bug Fixes
- BUG #002: Worker desync — Ana se vraćala nakon restarta jer seed logika nije imala completion flag. Fix: `seed_completed` document u settings kolekciji.

## Current Active Workers
- Suzana (hair)
- Milena (nails)
- Slobodan (massage)
- Dragana (makeup)
- Dobrila (depilation)
- Jovana (cosmetics)
- Dejan (eyebrows)

## Backlog
- P2: SMS/Email notifikacije za potvrde i podsetnike
- P3: Refaktorisanje server.py u module (routes, models, db)
