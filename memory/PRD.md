# Beauty Salon Booking App - PRD

## Originalni Problem Statement
Aplikacija za rezervaciju termina u beauty salonu sa sledećim zahtevima:
- Klijenti biraju usluge i radnika bez registracije
- Admin dashboard za upravljanje
- Sistem avansa (24h pre termina)
- Blacklist telefona
- Max 3 rezervacije dnevno po telefonu
- Tamna tema, mobile-first dizajn

## Admin Kredencijali
- **Email:** admin@salon.com
- **Password:** Admin123!

## Core Requirements — All Completed
- [x] Multi-step booking wizard (4 koraka)
- [x] Izbor usluga sa automatskim sabiranjem trajanja
- [x] Izbor radnika po usluzi (split-booking)
- [x] Kalendar sa slobodnim terminima
- [x] Potvrda rezervacije bez registracije
- [x] Admin JWT autentifikacija
- [x] CRUD za usluge i radnike
- [x] Safe Delete radnika (hard delete + referential integrity check)
- [x] Confirmation dialog pre brisanja radnika
- [x] Pregled rezervacija po datumu (tabela)
- [x] Kratki booking_id (#A1B2) za svaku rezervaciju
- [x] Success page sa uplatnicom (bank account, primalac, svrha uplate, Viber/Instagram instrukcija)
- [x] Admin kolona "Status uplate" (Čeka uplatu / Plaćeno toggle)
- [x] Blacklist telefona
- [x] Limit 3 rezervacije dnevno po telefonu
- [x] Podešavanja salona (ime, radno vreme, tekući račun, primalac uplate)
- [x] "Moje rezervacije" za klijente
- [x] Klijent može sam otkazati termin (24h+ ranije)
- [x] Split-booking: sekvencijalna dostupnost sa max 15-min gap
- [x] Per-worker conflict detection sa worker_time_blocks

## API Endpoints
- `POST /api/auth/login` - Admin login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Current user
- `GET/POST/PUT/DELETE /api/services` - Services CRUD
- `GET/POST/PUT/DELETE /api/workers` - Workers CRUD (hard delete + future booking check)
- `POST /api/reservations` - Create reservation (with booking_id, payment_status)
- `GET /api/reservations` - List reservations (admin)
- `POST /api/reservations/available-slots` - Get available slots
- `PUT /api/reservations/{id}/release-advance` - Release advance
- `PUT /api/reservations/{id}/cancel` - Cancel reservation
- `PUT /api/reservations/{id}/payment-status` - Toggle payment status (pending/paid)
- `GET/POST/DELETE /api/blacklist` - Blacklist management
- `GET/PUT /api/settings` - Salon settings (incl. bank_account, payment_recipient)
- `POST /api/my-reservations` - Client's reservations by phone
- `PUT /api/my-reservations/{id}/cancel` - Client cancels (24h rule)

## Backlog
- P2: SMS/Email notifikacije za potvrde i podsetnike
- P3: Refaktorisanje server.py u manje module
