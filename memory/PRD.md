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
- [x] Izbor radnika ili "Bilo ko"
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

## What's Been Implemented (April 3, 2026)

### Backend (FastAPI + MongoDB)
- JWT autentifikacija sa httpOnly cookies
- Admin seeding na startup
- Auto-seeding 5 usluga i 1 radnika (Ana)
- Duplikat detekcija i čišćenje
- Services CRUD (`/api/services`)
- Workers CRUD (`/api/workers`)
- Reservations (`/api/reservations`)
- Available slots calculation sa kontinuiranim blokom trajanja
- Blacklist management (`/api/blacklist`)
- Settings (`/api/settings`)
- **NEW:** Client reservations (`/api/my-reservations`)
- **NEW:** Client cancellation with 24h rule

### Seeded Data
**Usluge:**
1. Šišanje - 30 min - 2,000 RSD (hair)
2. Farbanje kose - 90 min - 5,000 RSD (hair)
3. Manikir - 45 min - 2,500 RSD (nails)
4. Pedikir - 60 min - 3,000 RSD (nails)
5. Relax masaža - 60 min - 4,000 RSD (massage)

**Radnik:**
- Ana - 09:00-21:00, pauza 13:00-14:00, slobodna nedelja

### Frontend (React + Tailwind + Shadcn)
- Tamna elegantna tema (Cormorant Garamond + Outfit fonts)
- Mobile-first responsive dizajn
- 4-step booking wizard
- **NEW:** "Moje rezervacije" modal za klijente
- **NEW:** Admin link uklonjen iz headera (diskretni footer link)
- Admin login stranica
- Admin dashboard sa navigacijom:
  - Rezervacije (TABELA sa kolonama)
  - **NEW:** Crna Lista (zasebna stranica)
  - Radnici (CRUD)
  - Usluge (CRUD)
  - Podešavanja

## API Endpoints
- `POST /api/auth/login` - Admin login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Current user
- `GET/POST/PUT/DELETE /api/services` - Services CRUD
- `GET/POST/PUT/DELETE /api/workers` - Workers CRUD
- `POST /api/reservations` - Create reservation
- `GET /api/reservations` - List reservations (admin)
- `POST /api/reservations/available-slots` - Get available slots
- `PUT /api/reservations/{id}/release-advance` - Release advance
- `PUT /api/reservations/{id}/cancel` - Cancel reservation (admin)
- `GET/POST/DELETE /api/blacklist` - Blacklist management
- `GET/PUT /api/settings` - Salon settings
- **NEW:** `POST /api/my-reservations` - Client's reservations by phone
- **NEW:** `PUT /api/my-reservations/{id}/cancel` - Client cancels (24h rule)
