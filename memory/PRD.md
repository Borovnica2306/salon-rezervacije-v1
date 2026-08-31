# Salon Booking PWA - Product Requirements Document

## Original Problem Statement
Multi-tenant salon booking PWA within the Pi Network ecosystem. Clients book appointments without registration via direct tenant links. Pi SDK authentication and payment integration. Admin dashboard with modular architecture, drag-and-drop scheduling, and RBAC.

## Architecture
- **Frontend**: React (CRA) + Tailwind + Shadcn/UI + localForage (IndexedDB)
- **Backend**: FastAPI + Motor (MongoDB async) + bcrypt + JWT
- **Database**: MongoDB (multi-tenant via `tenant_id`)
- **Backend Modules**:
  - `routes.py` — Orchestrator (includes 4 sub-routers)
  - `auth_routes.py` — Login (with brute-force), logout, me, change-password
  - `worker_routes.py` — Workers CRUD, account management, bulk statuses, reset-password
  - `admin_routes.py` — Tenants, categories, services, blacklist, settings, reminders
  - `booking_routes.py` — Reservations, client-facing, reschedule, Pi payments
  - `route_utils.py` — Shared helpers

## Completed Features
- [x] Multi-tenant with slug resolution + 7 CSS variable themes
- [x] Pi SDK auth (PiAuthContext with sandbox) + Pi payment flow
- [x] Admin modular dashboard with Drag-and-Drop scheduling
- [x] RBAC: Worker read-only dashboard (7-day, own column, no DnD)
- [x] Worker account management (create/delete/reset-password)
- [x] Forced password change on first login (must_change_password flow)
- [x] Backend routes.py split into 4 domain modules
- [x] SalonWorkers.jsx split into 4 component files
- [x] Bulk account-statuses endpoint (N+1 optimization)
- [x] Worker role guard on admin routes
- [x] Confirmation dialog for "Ukloni nalog"
- [x] **Tenant-aware logout redirect** (worker/admin → /:slug/admin/login)
- [x] **Brute-force login protection** (5 attempts → 15 min lockout, 429 status)

## Backlog
- [ ] P4: Remove wildcard "*" from CORS allow_origins
- [ ] P4: Persist brute-force tracker (Mongo/Redis) for multi-worker durability
