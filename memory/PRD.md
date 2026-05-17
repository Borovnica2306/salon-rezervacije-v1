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
- [x] Daily Timeline Grid — Worker kolone, 30-min redovi, obojeni blokovi
- [x] Auto-Scroll na current_time
- [x] Detail Dialog — klik na blok otvara detalje sa akcijama
- [x] Archive Tab — klasična tabela za prošle termine sa pretragom
- [x] Mobile Timeline Grid — horizontalni skrol, sticky time kolona, min-w-[120px]
- [x] Dalje Button Fix — auto-dodaje pending uslugu/radnika
- [x] Touch Targets 48px — svi inputi u modalu
- [x] Visual Category Cards — realistične Unsplash slike sa gradient overlay
- [x] Prominent Back Button — "Nazad na kategorije" full-width
- [x] Edit Mode Step 4 — X dugme za uklanjanje, "Izmeni usluge" link
- [x] Admin Edit Mode Step 3 — X po paru, "Izmeni usluge" link
- [x] **IPS QR Kod Plaćanje** — NBS standard, srpska transliteracija, QRCodeSVG (220px), fallback tekst

## Backlog
- P1: Viber notifikacije (placeholder u logic.py)
- P3: Drag & drop na admin timeline gridu za preraspoređivanje
