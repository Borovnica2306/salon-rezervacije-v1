# Beauty Salon Booking App - PRD

## Originalni Problem Statement
Aplikacija za rezervaciju termina u beauty salonu sa sledećim zahtevima:
- Klijenti biraju usluge i radnika bez registracije
- Admin dashboard za upravljanje
- Sistem avansa (24h pre termina)
- Blacklist telefona
- Max 3 rezervacije dnevno po telefonu
- Tamna tema, mobile-first dizajn

## User Personas
1. **Klijent** - Želi brzo da zakaže termin bez registracije
2. **Vlasnik/Admin** - Upravlja salonom, radnicima, uslugama i rezervacijama

## Admin Kredencijali
- **Email:** admin@salon.com
- **Password:** Admin123!

## Core Requirements
- [x] Multi-step booking wizard (4 koraka)
- [x] Izbor usluga sa automatskim sabiranjem trajanja
- [x] Izbor radnika po usluzi (split-booking)
- [x] Kalendar sa slobodnim terminima
- [x] Potvrda rezervacije bez registracije
- [x] Admin JWT autentifikacija
- [x] CRUD za usluge (naziv, kategorija, trajanje, cena)
- [x] CRUD za radnike (ime, radno vreme, pauze, slobodni dani)
- [x] Pregled rezervacija po datumu (tabela)
- [x] Oslobađanje avansa
- [x] Blacklist telefona (zasebna stranica)
- [x] Limit 3 rezervacije dnevno po telefonu
- [x] Podešavanja salona (ime, radno vreme)
- [x] "Moje rezervacije" za klijente (pretraga po telefonu)
- [x] Klijent može sam otkazati termin (24h+ ranije)
- [x] Automatsko seeding početnih podataka
- [x] Split-booking: sekvencijalna dostupnost sa max 15-min gap između usluga
- [x] Per-worker conflict detection sa worker_time_blocks
- [x] Admin tabela prikazuje sve parove usluga-radnik
- [x] Safe Delete radnika: hard delete sa referential integrity check

## What's Been Implemented

### Backend (FastAPI + MongoDB)
- JWT autentifikacija sa httpOnly cookies
- Admin seeding na startup
- Auto-seeding usluga i radnika
- Services CRUD (`/api/services`)
- Workers CRUD (`/api/workers`) — **Safe Delete**: hard delete sa proverom budućih termina
- Reservations (`/api/reservations`)
- Split-booking: Sequential availability with max 15-min gap
- Per-worker blocking: `worker_time_blocks` stored per reservation
- Blacklist management (`/api/blacklist`)
- Settings (`/api/settings`)
- Client reservations (`/api/my-reservations`)
- Client cancellation with 24h rule

### Frontend (React + Tailwind + Shadcn)
- Tamna elegantna tema (Cormorant Garamond + Outfit fonts)
- Mobile-first responsive dizajn
- 4-step booking wizard with per-service worker selection
- "Moje rezervacije" modal za klijente
- Admin dashboard:
  - Rezervacije tabela sa split-booking prikazom
  - Crna Lista (zasebna stranica)
  - Radnici (CRUD) — error poruka za blokirano brisanje
  - Usluge (CRUD)
  - Podešavanja

## API Endpoints
- `POST /api/auth/login` - Admin login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Current user
- `GET/POST/PUT/DELETE /api/services` - Services CRUD
- `GET/POST/PUT/DELETE /api/workers` - Workers CRUD (delete = hard delete with future booking check)
- `POST /api/reservations` - Create reservation
- `GET /api/reservations` - List reservations (admin)
- `POST /api/reservations/available-slots` - Get available slots
- `PUT /api/reservations/{id}/release-advance` - Release advance
- `PUT /api/reservations/{id}/cancel` - Cancel reservation (admin)
- `GET/POST/DELETE /api/blacklist` - Blacklist management
- `GET/PUT /api/settings` - Salon settings
- `POST /api/my-reservations` - Client's reservations by phone
- `PUT /api/my-reservations/{id}/cancel` - Client cancels (24h rule)

## Backlog
- P2: SMS/Email notifikacije za potvrde i podsetnike
- P3: Refaktorisanje server.py u manje module
