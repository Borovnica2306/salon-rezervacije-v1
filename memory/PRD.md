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

## Core Requirements
- [x] Multi-step booking wizard (4 koraka)
- [x] Izbor usluga sa automatskim sabiranjem trajanja
- [x] Izbor radnika ili "Bilo ko"
- [x] Kalendar sa slobodnim terminima
- [x] Potvrda rezervacije bez registracije
- [x] Admin JWT autentifikacija
- [x] CRUD za usluge (naziv, kategorija, trajanje, cena)
- [x] CRUD za radnike (ime, radno vreme, pauze, slobodni dani)
- [x] Pregled rezervacija po datumu
- [x] Oslobađanje avansa
- [x] Blacklist telefona
- [x] Limit 3 rezervacije dnevno po telefonu
- [x] Podešavanja salona (ime, radno vreme)

## What's Been Implemented (April 3, 2026)

### Backend (FastAPI + MongoDB)
- JWT autentifikacija sa httpOnly cookies
- Admin seeding na startup
- Services CRUD (`/api/services`)
- Workers CRUD (`/api/workers`)
- Reservations (`/api/reservations`)
- Available slots calculation (`/api/reservations/available-slots`)
- Blacklist management (`/api/blacklist`)
- Settings (`/api/settings`)
- Phone normalization za konzistentno poređenje

### Frontend (React + Tailwind + Shadcn)
- Tamna elegantna tema (Cormorant Garamond + Outfit fonts)
- Mobile-first responsive dizajn
- 4-step booking wizard
- Admin login stranica
- Admin dashboard sa navigacijom:
  - Rezervacije (timeline po datumu)
  - Radnici (CRUD)
  - Usluge (CRUD)
  - Podešavanja

## Prioritized Backlog

### P0 (Critical) - DONE
- [x] Booking flow
- [x] Admin auth
- [x] Services/Workers CRUD
- [x] Blacklist
- [x] Daily limit

### P1 (High)
- [ ] SMS/Email notifikacije
- [ ] Automatski podsjetnik 24h prije termina
- [ ] Detaljniji pregled statistike

### P2 (Nice to Have)
- [ ] Multiple admin accounts
- [ ] Worker self-service portal
- [ ] Customer history po telefonu
- [ ] Export rezervacija (CSV)
- [ ] Online payment integration (Stripe)

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Shadcn UI, Sonner (toasts)
- **Backend**: FastAPI, Motor (async MongoDB), PyJWT, bcrypt
- **Database**: MongoDB

## Admin Credentials
- Email: admin@salon.com
- Password: Admin123!

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
- `PUT /api/reservations/{id}/cancel` - Cancel reservation
- `GET/POST/DELETE /api/blacklist` - Blacklist management
- `GET/PUT /api/settings` - Salon settings
