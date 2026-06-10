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
├── App.js           # AuthProvider, routing (/, /login, /super-admin, /:slug, /:slug/admin/*)
├── components/
│   └── PhoneInput.jsx  # Global country prefix + phone validator
└── pages/
    ├── LandingPage.jsx      # / - Hero, Country selection, Advice & Referral
    ├── AdminLogin.jsx       # /login - Centralized login with smart redirect
    ├── SuperAdminPage.jsx   # /super-admin - Standalone Super Admin panel
    ├── BookingPage.jsx      # /:slug - tenant-aware booking
    └── AdminDashboard.jsx   # /:slug/admin/* - tenant admin panel
```

## Routing Architecture
- `/` → Landing Page (Hero → Country Selection → Advice/Referral)
- `/login` → Centralized login (smart redirect: super_admin→/super-admin, admin→/<slug>/admin)
- `/super-admin` → Protected standalone Super Admin panel
- `/:slug` → Client booking page for specific salon
- `/:slug/admin/login` → Legacy login route (backward compatible, smart redirect)
- `/:slug/admin/*` → Tenant admin dashboard

## Auth Flow
- Login returns `slug` field alongside `role` and `tenant_id`
- Super Admin → redirected to `/super-admin` (standalone page)
- Salon Admin → redirected to `/<slug>/admin` based on their tenant's slug
- `/auth/me` also returns `slug` for session restoration

## Multitenant System
- **Primary Tenant**: Beauty Studio Bor (slug: beauty-studio-bor, id: tenant_bsb_001)
- **Data isolation**: `tenant_id` field on ALL documents
- **Super Admin**: bornaja23@gmail.com - manages all tenants via /super-admin
- **Feature Flags**: per tenant (viber, ips_qr, manual_booking, email, lazy_cancel)

## All Completed Features
- [x] Multi-step booking wizard, Smart Pairing, Anti-Conflict
- [x] JWT auth (admin + super_admin) + Multitenant isolation
- [x] CRUD services/workers/blacklist
- [x] IPS QR Payment (NBS standard), Email notifications
- [x] Payment Tracking (3 statuses), Lazy Cancel (3h)
- [x] Daily Timeline Grid, Manual Booking, Archive
- [x] Mobile optimized (touch targets, sticky columns)
- [x] Viber/WhatsApp direct chat links
- [x] MULTITENANT - Slug routing, data isolation, feature flags, God Mode
- [x] Global Landing Page with Country selection → Advice + Referral (no salon listing)
- [x] Centralized Login (/login) with smart redirect by role
- [x] Standalone Super Admin Panel (/super-admin) - Saloni, Feature Flags, Kategorije
- [x] Salon Name edit restricted to Super Admin (immutable slug)
- [x] PhoneInput with Country Prefix + Email validation
- [x] CSV Export for Super Admin
- [x] Tenant Creation via Super Admin Panel with auto-slug generation

## Backlog
- P3: Drag & drop on timeline grid for rescheduling
- P3: Refactor AdminDashboard.jsx (~2066 lines) into sub-components
- P3: Refactor routes.py (~1290 lines) into domain modules
