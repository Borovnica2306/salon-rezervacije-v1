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
- [x] Modularna arhitektura (server, database, models, auth, logic, routes)
- [x] Vizuelni Timeline + Add to Calendar (Google + ICS)
- [x] Standardizacija formata telefona (+381, zero-strip)
- [x] Striktna per-worker boundary provera radnog vremena
- [x] Admin Manual Booking (3-step modal + force override)
- [x] **Daily Timeline Grid** — Worker kolone, 30-min redovi, obojeni blokovi
- [x] **Auto-Scroll** na current_time
- [x] **Detail Dialog** — klik na blok otvara detalje sa akcijama (uplata/otkaži/blokiraj)
- [x] **Archive Tab** — klasična tabela za prošle termine sa pretragom
- [x] **Connected blocks** — ista boja ivice za povezane usluge istog booking-a
- [x] **Mobile Timeline Grid** — horizontalni skrol, sticky time kolona (z-30/z-10), min-w-[120px] kolone
- [x] **Dalje Button Fix** — auto-dodaje pending uslugu/radnika bez potrebe za klikom na "+Dodaj uslugu"
- [x] **Touch Targets 48px** — svi inputi, selecti i dugmad u modalu imaju min-h-[48px]

## Backlog
- P1: Viber notifikacije (placeholder u logic.py)
- P3: Drag & drop na admin timeline gridu za preraspoređivanje
