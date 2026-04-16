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
- [x] **Mobile Timeline Grid** — horizontalni skrol, sticky time kolona, min-w-[120px] kolone
- [x] **Dalje Button Fix** — auto-dodaje pending uslugu/radnika bez klika na "+Dodaj uslugu"
- [x] **Touch Targets 48px** — svi inputi, selecti i dugmad u modalu min-h-[48px]
- [x] **Visual Category Cards** — realistične Unsplash slike sa gradient overlay-om za svih 7 kategorija
- [x] **Prominent Back Button** — "Nazad na kategorije" full-width, centriran, sa borderom i strelicom
- [x] **Edit Mode Step 4** — X dugme za uklanjanje usluge, "Izmeni usluge" link, auto-povratak na Step 1
- [x] **Admin Edit Mode Step 3** — Isto za admin modal: X po paru, "Izmeni usluge" link

## Backlog
- P1: Viber notifikacije (placeholder u logic.py)
- P3: Drag & drop na admin timeline gridu za preraspoređivanje
