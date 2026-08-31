# Development Log — Salon Booking PWA

Hronološki zapis ključnih tehničkih izazova, odluka i optimizacija tokom razvoja.

---

## Faza 1 — Osnovna platforma

### Multi-tenant arhitektura
- Implementiran tenant resolution putem slug-a u URL-u (`/:slug`)
- Svaki tenant ima izolovan `tenant_id` u svim kolekcijama
- `X-Tenant-ID` header za API izolaciju

### Smart Pairing booking engine
- Multi-service split-booking: klijent bira više usluga sa različitim radnicima
- 15-minutni fiksni gap bufferi između usluga
- `worker_time_blocks` niz čuva tačan raspored po radniku unutar jedne rezervacije
- Anti-conflict: dvostruka provera (klijent overlap + worker overlap) pri kreiranju

### CSS Variable Theming (7 tema)
- Teme definisane kao JSON u `config.js` → mapiraju se na CSS varijable
- `applyTheme()` dinamički menja `--color-primary`, `--color-background`, itd.
- Radijalni gradijent pozadina + SVG patern overlay (`body::after`) po temi
- Tema se čuva na nivou tenanta i primenjuje pri učitavanju

---

## Faza 2 — Pi Network integracija

### PiAuthContext (Sandbox + Production)
- `window.Pi.init()` za produkciju, faker za sandbox
- Sandbox automatski detektuje `emergentagent.com` URL
- Simulira korisnika `MarkoDev` sa fake UID-om i auto-approve platnog toka
- Frontend `BookingPage.jsx` koristi Pi SDK za kreiranje plaćanja umesto manuelnog unosa imena

### Backend Pi API
- `POST /api/payments/approve` — Poziva Pi API za odobrenje ili sandbox auto-approve
- `POST /api/payments/complete` — Finalizira plaćanje sa `txid`
- `payment_status` tok: `pending_pi_payment` → `confirmed`
- Uklonjeni svi fiat elementi: RSD, NBS IPS QR, Viber, WhatsApp

---

## Faza 3 — Admin Dashboard refaktoring

### Modularna dekompozicija
**Problem**: `AdminDashboard.jsx` bio je monolitan (~2000 linija).
**Rešenje**: Razbijen u 9 komponenti:
- `CalendarView.jsx` — Timeline grid sa drag-and-drop
- `SalonWorkers.jsx`, `SalonServices.jsx`, `AdminSettings.jsx`
- `ManualBookingModal.jsx`, `BlacklistPage.jsx`
- `WorkerFormDialog.jsx`, `WorkerAccountDialog.jsx`, `DeleteWorkerDialog.jsx`

### Drag-and-Drop scheduling
- React state-based DnD (bez eksternih biblioteka)
- `handleDragStart` → `handleDragOver` (sa worker service kompatibilnošću) → `handleDrop`
- Backend `PUT /api/reservations/:id/reschedule` striktno proverava overlap pre ažuriranja
- Reschedule modal sa potvrdom pre izvršenja

### Double-booking zaštita
**Problem**: Backend nije proveravao overlap pri reschedulingu.
**Rešenje**: Dodat MongoDB upit koji traži preklapajuće rezervacije istog radnika na isti datum pre ažuriranja. Vraća 400 ako je termin zauzet.

---

## Faza 4 — RBAC i Worker nalozi

### Role-Based Access Control
- 3 uloge u `users` kolekciji: `super_admin`, `admin`, `worker`
- Worker-specifična polja: `worker_id`, `language_preference`, `must_change_password`
- Backend: `GET /api/reservations` za workere filtrira po `worker_id` i 7-dnevnom prozoru
- Frontend: `CalendarView.jsx` potpuno onemogućava interakciju za workere (`pointer-events: none`, `draggable: false`)
- `AdminDashboard.jsx`: navigacija filtrirana — worker vidi samo "Rezervacije"
- Route guard: worker koji pokuša `/employees` ili `/settings` putem URL-a biva preusmeren nazad

### Timezone-aware filtriranje
**Problem**: Server u UTC, salon u Europe/Belgrade — "danas" može biti različit datum.
**Rešenje**: `_get_salon_today()` koristi `zoneinfo.ZoneInfo` i `country` polje tenanta za određivanje lokalne vremenske zone salona.

### Worker account management
- Admin kreira nalog: `POST /api/workers/:id/create-account` → auto-generisana lozinka (10 char)
- Admin resetuje lozinku: `PUT /api/workers/:id/reset-password` → nova temp lozinka + `must_change_password: true`
- Temp lozinka prikazana samo jednom sa Copy dugmetom

### Must-change-password flow
**Problem**: Worker sa temp lozinkom ne sme pristupiti dashboardu dok ne postavi svoju.
**Rešenje**:
- `ProtectedRoute` u `App.js` proverava `user.must_change_password` — ako je `true`, redirect na login
- `AdminLogin.jsx` detektuje flag i prikazuje full-screen formu za promenu lozinke
- `AuthContext.updateUser()` ažurira state bez ponovnog login-a nakon uspešne promene
- Nema infinite redirect loop: AdminLogin proverava flag pre auto-redirect logike

---

## Faza 5 — Backend refaktoring

### routes.py dekompozicija
**Problem**: `routes.py` narastao na 1691 liniju — neodrživ.
**Rešenje**: Razbijen u 4 domena + shared helpers:
| Modul | Odgovornost | Rute |
|---|---|---|
| `auth_routes.py` | Autentifikacija | 4 |
| `worker_routes.py` | Radnici + nalozi | 9 |
| `admin_routes.py` | Tenanti, usluge, kategorije, podešavanja, crna lista | 21 |
| `booking_routes.py` | Rezervacije, klijenti, plaćanja | 14 |
| `route_utils.py` | Deljeni helperi | - |

`routes.py` sveden na ~15 linija (orchestrator sa `include_router`).

---

## Faza 6 — Optimizacije i bezbednost

### N+1 upit optimizacija
**Problem**: `SalonWorkers.jsx` slao N pojedinačnih `GET /workers/:id/account` poziva.
**Rešenje**: Novi bulk endpoint `GET /api/workers/account-statuses` — jedan MongoDB upit vraća statusni rečnik za sve radnike tenanta.
```
Bilo: 8 radnika × 1 poziv = 8 HTTP zahteva
Sada: 1 HTTP zahtev (bulk)
```

### Tenant-specific logout redirect
**Problem**: `ProtectedRoute` hardkodovao `/login` — worker gubio kontekst salona.
**Rešenje**: `ProtectedRoute` koristi `useParams().slug` za konstrukciju `/${slug}/admin/login`. `handleLogout` čuva slug pre `await logout()`.

### Brute-force zaštita (persistentna)
**Problem**: In-memory `dict` se gubio na restart servera.
**Rešenje**: Prebačeno u MongoDB kolekciju `failed_logins`:
- 5 neuspelih pokušaja → 15-min lockout (HTTP 429 sa tajmerom)
- TTL indeks (`expireAfterSeconds: 1800`) za automatsko čišćenje
- Unique indeks na `email` za atomičnost
- Uspešan login briše zapis

### CORS hardening
- Uklonjen wildcard `"*"` iz `allow_origins`
- Samo eksplicitni `FRONTEND_URL` dozvoljen sa `allow_credentials: True`

### SVG pozadinski paterne
- 7 unikatnih inline SVG patterna (dine, listovi, talasi, geometrija, tačke, konstelacije)
- Opacity max 0.08, `body::after` overlay sa `pointer-events: none`
- `#root` na `z-index: 1` da sadržaj ostane iznad

---

## Konvencije koda

### Backend
- Async MongoDB operacije putem Motor drivera
- Pydantic modeli za request/response validaciju
- `_get_tid(request)` za tenant izolaciju u svakom endpointu
- `check_tenant_access(user, tid)` za RBAC proveru
- ISO 8601 datumi, `datetime.now(timezone.utc)` (nikad `utcnow()`)

### Frontend
- Shadcn/UI komponente iz `/components/ui/`
- `data-testid` na svakom interaktivnom elementu
- `useAuth()` hook za user state, `useTenant()` za tenant context
- Sonner toast za notifikacije
- CSS varijable za theming (nikad hardkodirane boje)
