# Beauty Salon Booking App - PRD

## Originalni Problem Statement
Multitenant platforma za rezervaciju termina u beauty salonima. God Mode za Super Admina.

## Architecture
```
/app/frontend/src/pages/
├── LandingPage.jsx      # / - Hero sa 3 puta (info, vlasnici, login)
├── InfoPage.jsx         # /info - Savet za klijente
├── OwnersPage.jsx       # /vlasnici - Placeholder za vlasnike
├── AdminLogin.jsx       # /login - Centralizovani login
├── SuperAdminPage.jsx   # /super-admin - Lista salona
├── SalonGodMode.jsx     # /super-admin/salon/:slug - God Mode per salon
├── BookingPage.jsx      # /:slug - Javni booking wizard
└── AdminDashboard.jsx   # /:slug/admin/* - Tenant admin panel
```

## Routing
- `/` → Landing (3 puta: info, vlasnici, login)
- `/info` → Info za klijente (saveti, referral)
- `/vlasnici` → Placeholder za vlasnike salona
- `/login` → Centralizovani login sa smart redirect
- `/super-admin` → Lista salona (search/filter)
- `/super-admin/salon/:slug` → God Mode panel (Feature Flags, Kategorije, Sistemski podaci)
- `/:slug` → **100% JAVNI** booking wizard
- `/:slug/admin/*` → Tenant admin dashboard

## Completed Features
- [x] Multi-step booking wizard, Smart Pairing, Anti-Conflict
- [x] JWT auth + Multitenant isolation
- [x] CRUD services/workers/blacklist
- [x] IPS QR, Email, Payment Tracking, Lazy Cancel
- [x] Daily Timeline Grid, Manual Booking, Archive
- [x] Mobile optimized, Viber/WhatsApp links
- [x] Landing Page sa 3 izolovana puta
- [x] Centralizovani Login sa smart redirect
- [x] God Mode Panel per salon (izolovan po tenant_id)
- [x] Salon status (active/suspended), Owner password change
- [x] FIX: Manual booking slots (X-Tenant-ID header)

## Backlog
- P3: Drag & drop on timeline grid
- P3: Refactor AdminDashboard.jsx and routes.py
