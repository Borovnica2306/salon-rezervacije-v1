# Beauty Salon Booking App - PRD

## Originalni Problem Statement
Multitenant platforma za rezervaciju termina u beauty salonima. Jedan codebase, neogranicen broj salona. God Mode za Super Admina.

## Architecture
```
/app/backend/
├── server.py        # App init, tenant seed, data migration
├── database.py      # MongoDB connection
├── models.py        # Pydantic schemas
├── auth.py          # JWT with tenant_id + role
├── tenant.py        # Tenant resolution + access control
├── logic.py         # Smart Pairing, IPS QR, Lazy Cancel (tenant-aware)
├── routes.py        # All endpoints with X-Tenant-ID filter
└── mail_service.py  # Async SMTP email

/app/frontend/src/
├── App.js           # AuthProvider, routing
├── components/
│   └── PhoneInput.jsx
└── pages/
    ├── LandingPage.jsx      # / - Hero, Advice & Referral
    ├── AdminLogin.jsx       # /login - Centralized login
    ├── SuperAdminPage.jsx   # /super-admin - Salon list only
    ├── SalonGodMode.jsx     # /super-admin/salon/:slug - God Mode per salon
    ├── BookingPage.jsx      # /:slug - booking
    └── AdminDashboard.jsx   # /:slug/admin/* - tenant admin
```

## Super Admin Flow
- `/super-admin` → Lista salona sa pretragom/filterom (BEZ Feature Flags/Kategorije tabova)
- `/super-admin/salon/<slug>` → God Mode panel za specifičan salon:
  - Feature Flags (per-tenant)
  - Kategorije (per-tenant)
  - Sistemski podaci (status, owner email, password change)
- Stroga izolacija: promene utiču SAMO na taj tenant_id
- Security guard: password change blokiran za super_admin naloge

## All Completed Features
- [x] Multi-step booking wizard, Smart Pairing, Anti-Conflict
- [x] JWT auth + Multitenant isolation
- [x] CRUD services/workers/blacklist
- [x] IPS QR Payment, Email notifications, Payment Tracking, Lazy Cancel
- [x] Daily Timeline Grid, Manual Booking, Archive
- [x] Mobile optimized, Viber/WhatsApp links
- [x] MULTITENANT - Slug routing, data isolation, feature flags
- [x] Landing Page → Advice + Referral (no salon listing)
- [x] Centralized Login (/login) with smart redirect
- [x] Super Admin: Salon list with search/filter
- [x] God Mode Panel per salon (Feature Flags, Kategorije, Sistemski podaci)
- [x] Salon status (active/suspended), Owner password change with guard
- [x] Super Admin Banner in tenant admin

## Backlog
- P3: Drag & drop on timeline grid
- P3: Refactor AdminDashboard.jsx and routes.py
