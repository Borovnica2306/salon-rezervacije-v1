# Salon Booking PWA - Product Requirements Document

## Original Problem Statement
Multi-tenant salon booking PWA within the Pi Network ecosystem. Clients book appointments without registration via direct tenant links. Pi SDK authentication and payment integration. Admin dashboard with modular architecture, drag-and-drop scheduling, and RBAC.

## Architecture
- **Frontend**: React (CRA) + Tailwind + Shadcn/UI + localForage (IndexedDB)
- **Backend**: FastAPI + Motor (MongoDB async) + bcrypt + JWT
- **Database**: MongoDB (multi-tenant via `tenant_id`)
- **Backend Modules**:
  - `routes.py` — Orchestrator (includes 4 sub-routers)
  - `auth_routes.py` — Login, logout, me, change-password
  - `worker_routes.py` — Workers CRUD, account management, bulk statuses, reset-password
  - `admin_routes.py` — Tenants, categories, services, blacklist, settings, reminders
  - `booking_routes.py` — Reservations, client-facing, reschedule, Pi payments
  - `route_utils.py` — Shared helpers
- **Frontend Components** (admin/):
  - `SalonWorkers.jsx` — Main worker management page
  - `WorkerFormDialog.jsx` — Add/Edit worker form
  - `WorkerAccountDialog.jsx` — Create account + Reset password (shared)
  - `DeleteWorkerDialog.jsx` — Delete worker confirmation

## Completed Features
- [x] Multi-tenant with slug resolution + 7 CSS variable themes
- [x] Pi SDK auth (PiAuthContext with sandbox) + Pi payment flow
- [x] Admin modular dashboard (CalendarView, SalonWorkers, SalonServices, AdminSettings)
- [x] Drag-and-drop scheduling with double-booking protection
- [x] RBAC: Worker read-only dashboard (7-day, own column, no DnD)
- [x] Worker account management (create/delete/reset-password)
- [x] Forced password change on first login (must_change_password flow)
- [x] Admin "Resetuj lozinku" button in worker cards
- [x] Backend routes.py split into 4 domain modules
- [x] SalonWorkers.jsx split into 4 component files
- [x] **Bulk account-statuses endpoint (N+1 optimization)**
- [x] **Worker role guard on admin routes (redirect to reservations)**
- [x] **Confirmation dialog for "Ukloni nalog"**

## Backlog
- [ ] P4: Worker logout redirect to tenant-specific login page
- [ ] P4: Brute-force protection on login endpoint
- [ ] P4: Fix CORS wildcard with credentials
