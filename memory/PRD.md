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
├── App.js           # TenantProvider, slug routing, AuthProvider
├── components/
│   └── PhoneInput.jsx  # Global country prefix + phone validator
└── pages/
    ├── LandingPage.jsx      # / - Hero & Country selector
    ├── BookingPage.jsx      # /:slug - tenant-aware booking
    ├── AdminLogin.jsx       # /:slug/admin/login
    └── AdminDashboard.jsx   # /:slug/admin/* - tenant-aware admin
```

## Multitenant System
- **Tenant ID**: `tenant_bsb_001` (Primary: Beauty Studio Bor)
- **Slug routing**: `/:slug` for client, `/:slug/admin` for admin
- **Data isolation**: `tenant_id` field on ALL documents (services, workers, reservations, settings, blacklist, categories)
- **Auth**: JWT includes `tenant_id` + `role`, admin restricted to own tenant
- **Super Admin**: `bornaja23@gmail.com` - can access all tenants, manage feature flags
- **Feature Flags**: `enabled_features` per tenant (viber_notifications, ips_qr_payment, manual_booking, email_notifications, lazy_cancel)

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
- [x] Global Landing Page with Country selection
- [x] Super Admin Panel: Feature Flags, Kategorije, Saloni (Tenant Creation)
- [x] Salon Name edit restricted to Super Admin (immutable slug)
- [x] PhoneInput with Country Prefix + Email validation
- [x] CSV Export for Super Admin

## Backlog
- P3: Drag & drop on timeline grid for rescheduling
- P3: Refactor AdminDashboard.jsx (>2200 lines) into sub-components
- P3: Refactor routes.py (>1200 lines) into domain modules
