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

## Master Categories
| Key | Label | Default |
|-----|-------|---------|
| hair | Frizura | ON |
| massage | Masaža | ON |
| nails | Nokti | ON |
| makeup | Šminkanje | ON |
| depilation | Depilacija | ON |
| cosmetics | Kozmetika | ON |
| eyebrows | Obrve/Trepavice | ON |

## API Endpoints
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Current user
- `GET /api/categories` - Public enabled categories
- `GET /api/categories/config` - All categories with toggle (super_admin)
- `PUT /api/categories/config` - Toggle category (super_admin)
- `GET/POST/PUT/DELETE /api/services` - Services CRUD
- `GET/POST/PUT/DELETE /api/workers` - Workers CRUD
- `POST /api/reservations` - Create reservation
- `GET /api/reservations` - List reservations (admin)
- `POST /api/reservations/available-slots` - Available slots
- `PUT /api/reservations/{id}/payment-status` - Toggle payment
- `PUT /api/reservations/{id}/cancel` - Cancel
- `GET/POST/DELETE /api/blacklist` - Blacklist
- `GET/PUT /api/settings` - Settings (incl. bank_account)
- `POST /api/my-reservations` - Client's reservations
- `PUT /api/my-reservations/{id}/cancel` - Client cancel

## Backlog
- P2: SMS/Email notifikacije
- P3: Refaktorisanje server.py u module
