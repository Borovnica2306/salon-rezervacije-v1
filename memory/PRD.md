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
    ├── SuperAdminPage.jsx   # /super-admin - Standalone Super Admin panel (Search, Filters)
    ├── BookingPage.jsx      # /:slug - tenant-aware booking
    └── AdminDashboard.jsx   # /:slug/admin/* - tenant admin panel + Super Admin banner
```

## Routing Architecture
- `/` → Landing Page (Hero → Country Selection → Advice/Referral, no salon listing)
- `/login` → Centralized login (smart redirect: super_admin→/super-admin, admin→/<slug>/admin)
- `/super-admin` → Protected standalone Super Admin panel with Search & Country filters
- `/:slug` → Client booking page for specific salon
- `/:slug/admin/login` → Legacy login route (backward compatible, smart redirect)
- `/:slug/admin/*` → Tenant admin dashboard (with Super Admin banner if SA is viewing)

## Auth Flow
- Login returns `slug` field alongside `role` and `tenant_id`
- Super Admin → redirected to `/super-admin`
- Salon Admin → redirected to `/<slug>/admin`
- `/auth/me` also returns `slug` for session restoration
- Super Admin viewing tenant admin sees banner: "Pregledate salon kao Super Admin. [Nazad na Super Panel]"

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
- [x] Super Admin Panel: Search & Country filter on Saloni tab
- [x] Super Admin Panel: "Panel >" links to navigate to tenant admin dashboards
- [x] Super Admin Banner in tenant admin: "Pregledate salon kao Super Admin. [Nazad na Super Panel]"
- [x] Salon Name edit restricted to Super Admin (immutable slug)
- [x] PhoneInput with Country Prefix + Email validation
- [x] CSV Export for Super Admin
- [x] Tenant Creation via Super Admin Panel with auto-slug generation

## Backlog
- P3: Drag & drop on timeline grid for rescheduling
- P3: Refactor AdminDashboard.jsx (~2067 lines) into sub-components
- P3: Refactor routes.py (~1290 lines) into domain modules
