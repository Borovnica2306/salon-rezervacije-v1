# Salon Booking PWA — Pi Network Ecosystem

Multi-tenant Progressive Web App za rezervaciju termina u salonima, izgrađena na Pi Network ekosistemu. Klijenti zakazuju bez registracije putem direktnog linka salona (`/:slug`), a plaćanja se vrše isključivo putem Pi Network API-ja.

---

## Arhitektura sistema

```
┌──────────────────────────────────────────────────────────┐
│  Frontend — React 18 + Tailwind CSS + Shadcn/UI          │
│  PWA shell, localForage (IndexedDB), PiAuthContext        │
│  Port: 3000 (dev) → Kubernetes ingress (prod)             │
├──────────────────────────────────────────────────────────┤
│  Backend — FastAPI + Motor (async MongoDB driver)         │
│  Modularni routeri, JWT auth, bcrypt, brute-force guard   │
│  Port: 8001 → /api/* prefix routing                      │
├──────────────────────────────────────────────────────────┤
│  Database — MongoDB                                       │
│  Multi-tenant izolacija putem tenant_id polja             │
│  TTL indeks za failed_logins (auto-cleanup 30 min)        │
└──────────────────────────────────────────────────────────┘
```

### Ključne karakteristike
- **Multi-tenant**: Svaki salon = zaseban tenant sa slugom, temom, feature toggle-ima
- **7 vizuelnih tema**: Sahara, Amazon, Ubud, Copacabana, Kente, Batik, MidnightVelvet — CSS varijable + SVG pozadinski paterne
- **Pi Network integracija**: Sandbox dev mod sa auto-approve, produkcioni Pi API (`/payments/approve`, `/complete`)
- **Smart Pairing**: Multi-service split-booking sa 15-min gap bufferima i anti-conflict validacijom

---

## Bezbednost

### RBAC (Role-Based Access Control)
| Uloga | Pristup |
|---|---|
| **Super Admin** | Potpuna kontrola svih tenanta, tema, feature togglea |
| **Admin** | Upravljanje salonom: radnici, usluge, podešavanja, crna lista, rezervacije |
| **Worker** | Read-only pregled svojih rezervacija (7 dana), bez drag-and-drop, bez otkazivanja |
| **Client** | Javni booking putem `/:slug`, Pi SDK autentifikacija |

### Brute-Force zaštita
- 5 neuspelih pokušaja → 15-minutno zaključavanje naloga (HTTP 429)
- Persistentno u MongoDB kolekciji `failed_logins` (preživljava restart servera)
- TTL indeks: automatsko čišćenje starih zapisa posle 30 minuta
- Uspešan login resetuje brojač

### CORS
- Striktni `allow_origins` — samo `FRONTEND_URL` iz `.env`
- `allow_credentials: True` za httpOnly cookie auth

### Autentifikacija
- JWT access token (24h) + refresh token (7 dana) u httpOnly cookie-ima
- Bearer token fallback za API pozive
- `must_change_password` flow: worker mora promeniti temp lozinku pre pristupa dashboardu

---

## Struktura koda

### Backend (`/app/backend/`)
```
server.py              ← App init, DB seeding, indeksi, CORS
routes.py              ← Tanak orchestrator (uključuje 4 sub-routera)
auth_routes.py         ← Login (brute-force), logout, /me, change-password
worker_routes.py       ← Workers CRUD, account management, bulk statuses, reset-password
admin_routes.py        ← Tenants, kategorije, usluge, crna lista, podešavanja, podsetnici
booking_routes.py      ← Rezervacije, klijent-facing, reschedule, Pi plaćanja
route_utils.py         ← Deljeni helperi (_get_tid, _get_salon_today, temp password gen)
auth.py                ← JWT kreiranje/verifikacija, bcrypt hash/verify
models.py              ← Pydantic modeli (request/response šeme)
logic.py               ← Smart Pairing, slot kalkulacija, validacija granica
tenant.py              ← Tenant izolacija i pristupna kontrola
database.py            ← MongoDB konekcija (Motor async client)
mail_service.py        ← SMTP async email slanje
tests/                 ← 30+ pytest fajlova
```

### Frontend (`/app/frontend/src/`)
```
App.js                 ← Router, AuthContext, TenantContext, ProtectedRoute
config.js              ← Teme (7), SVG paterne, applyTheme()
authStorage.js         ← localForage wrapper za IndexedDB token persistenciju
context/
  PiAuthContext.jsx    ← Pi SDK injection, sandbox simulator (MarkoDev)
pages/
  AdminLogin.jsx       ← Login + forced password change screen
  AdminDashboard.jsx   ← Shell layout, RBAC nav filtering, worker banner
  BookingPage.jsx      ← Klijentski booking sa Pi Payment integracijom
  SuperAdminPage.jsx   ← Master tenant lista
  SalonGodMode.jsx     ← Tenant-specific system settings
components/admin/
  CalendarView.jsx     ← Drag-and-Drop timeline grid, read-only za workere
  SalonWorkers.jsx     ← Worker management, account status, bulk fetch
  WorkerFormDialog.jsx ← Add/Edit worker dijalog
  WorkerAccountDialog.jsx ← Create account / Reset password (shared)
  DeleteWorkerDialog.jsx  ← Potvrda brisanja radnika
  SalonServices.jsx    ← CRUD za usluge
  AdminSettings.jsx    ← Salon podešavanja
  ManualBookingModal.jsx ← Admin ručno bukiranje
  BlacklistPage.jsx    ← Crna lista telefona
```

---

## API rute

### Autentifikacija (`auth_routes.py`)
| Metod | Ruta | Opis |
|---|---|---|
| POST | `/api/auth/login` | Login sa brute-force zaštitom |
| POST | `/api/auth/logout` | Brisanje cookie-ja |
| GET | `/api/auth/me` | Trenutni korisnik (+ worker_id, must_change_password) |
| PUT | `/api/auth/change-password` | Promena lozinke (worker temp → nova) |

### Radnici (`worker_routes.py`)
| Metod | Ruta | Opis |
|---|---|---|
| GET | `/api/workers` | Lista radnika (public) |
| POST | `/api/workers` | Kreiranje radnika (admin) |
| PUT | `/api/workers/:id` | Ažuriranje radnika (admin) |
| DELETE | `/api/workers/:id` | Brisanje radnika (admin) |
| GET | `/api/workers/account-statuses` | Bulk status naloga svih radnika (admin) |
| POST | `/api/workers/:id/create-account` | Kreiranje login naloga za radnika (admin) |
| GET | `/api/workers/:id/account` | Provera statusa naloga radnika (admin) |
| DELETE | `/api/workers/:id/account` | Brisanje naloga radnika (admin) |
| PUT | `/api/workers/:id/reset-password` | Resetovanje lozinke radnika (admin) |

### Rezervacije (`booking_routes.py`)
| Metod | Ruta | Opis |
|---|---|---|
| POST | `/api/reservations/available-slots` | Dostupni slotovi (Smart Pairing) |
| POST | `/api/reservations` | Klijentska rezervacija |
| POST | `/api/admin/reservations` | Admin ručna rezervacija (sa force opcijom) |
| GET | `/api/reservations` | Lista (admin: po datumu, worker: 7-dnevni prozor) |
| PUT | `/api/reservations/:id/cancel` | Otkazivanje (admin) |
| PUT | `/api/reservations/:id/reschedule` | Drag-and-drop premeštanje (admin) |
| POST | `/api/payments/approve` | Pi API payment approval |
| POST | `/api/payments/complete` | Pi API payment completion |
| POST | `/api/my-reservations` | Klijentski pregled po telefonu |

### Admin (`admin_routes.py`)
| Metod | Ruta | Opis |
|---|---|---|
| GET | `/api/tenants/by-slug/:slug` | Tenant resolution |
| GET/POST | `/api/super/tenants` | Super admin tenant management |
| PUT | `/api/super/tenants/:id/theme` | Promena teme |
| GET/POST/PUT/DELETE | `/api/services` | CRUD za usluge |
| GET/POST/DELETE | `/api/blacklist` | Crna lista telefona |
| GET/PUT | `/api/settings` | Salon podešavanja |
| GET/PUT | `/api/categories/config` | Kategorije usluga |

---

## Lokalno pokretanje

### Preduslovi
- Python 3.10+, Node.js 18+, MongoDB 6+
- yarn (za frontend)

### Setup

```bash
# 1. Backend
cd /app/backend
cp .env.example .env   # Popuniti MONGO_URL, JWT_SECRET, FRONTEND_URL
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# 2. Frontend
cd /app/frontend
cp .env.example .env   # Popuniti REACT_APP_BACKEND_URL
yarn install
yarn start
```

### Environment varijable

**Backend (`/app/backend/.env`)**
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=salon_booking
JWT_SECRET=your-secret-key-here
FRONTEND_URL=http://localhost:3000
PI_API_KEY=your-pi-api-key     # Opciono, za produkcione Pi plaćanja
ADMIN_EMAIL=admin@salon.com
ADMIN_PASSWORD=Admin123!
```

**Frontend (`/app/frontend/.env`)**
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

### Test kredencijali (seed pri startupu)
| Uloga | Email | Lozinka |
|---|---|---|
| Super Admin | Bornaja23@gmail.com | Markonijus23! |
| Salon Admin | admin@salon.com | Admin123! |
| Worker (Marija) | worker@salon.com | Worker123! |

### Pokretanje testova
```bash
cd /app/backend
python -m pytest tests/ -v
```

---

## DB kolekcije

| Kolekcija | Opis | Ključna polja |
|---|---|---|
| `tenants` | Salon konfiguracija | slug, tenant_id, theme, country, enabled_features |
| `users` | Login nalozi | email, role, worker_id, tenant_id, must_change_password |
| `workers` | Radnici salona | name, services, work_start/end, days_off, tenant_id |
| `services` | Usluge | name, category, duration, price, tenant_id |
| `reservations` | Rezervacije | booking_id, date, time, worker_time_blocks, payment_status |
| `settings` | Salon podešavanja | salon_name, work_start/end, pi_wallet_address |
| `blacklisted_phones` | Crna lista | phone, tenant_id |
| `failed_logins` | Brute-force tracker | email, count, locked_until (TTL 30 min) |
| `categories_config` | Kategorije toggle | category, enabled, tenant_id |
