# Beauty Salon Booking App - PRD

## Originalni Problem Statement
Aplikacija za rezervaciju termina u beauty salonu. Klijenti biraju usluge i radnika bez registracije. Admin dashboard za upravljanje. Tamna tema, mobile-first dizajn, PWA.

## Korisnici
1. **Klijent** - Zakazuje termin bez registracije
2. **Salon-Admin** (admin@salon.com / Admin123!) - Upravlja salonom
3. **Super-Admin** (Bornaja23@gmail.com / Markonijus23!) - System Config, master kategorije

## Core Requirements — All Completed
- [x] Multi-step booking wizard (4 koraka)
- [x] Split-booking sa 15-min Social Buffer između usluga
- [x] Smart Pairing + Anti-Conflict validacija
- [x] All-or-Nothing lanac
- [x] JWT auth (admin + super_admin)
- [x] CRUD za usluge i radnike + Safe Delete
- [x] Booking ID, Uplatnica, Payment Status toggle
- [x] Blacklist telefona + Limit 3/dan
- [x] "Moje rezervacije" (24h otkazivanje)
- [x] Multi-Level Admin + Master Category Switch
- [x] Modularna arhitektura (server, database, models, auth, logic, routes)
- [x] Vizuelni Timeline + Add to Calendar (Google + ICS)
- [x] Admin: Worker filter + Social Buffer kartice + Cancel dialog
- [x] Admin: Manual Booking (3-step modal + force override)
- [x] Standardizacija formata telefona (+381, zero-strip)
- [x] Striktna provera radnog vremena (per-worker boundary check)
- [x] Admin boundary warning sa force-override opcijom

## Key Technical Details
- Boundary check: svaki radnik ima SVOJE radno vreme, provera ide per-worker
- 20:30+30min=21:00 → OK (tačno na granici)
- 20:45+30min=21:15 → NEDOSTUPAN (prelazi granicu)
- Admin vidi specifičnu poruku: "Suzana radi do 21:00, ali usluga se završava u 21:15"

## Backlog
- P2: Viber notifikacije (placeholder u logic.py)
- Budući zadaci po zahtevu korisnika
