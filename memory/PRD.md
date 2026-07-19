# Salon Booking PWA - Product Requirements Document

## Original Problem Statement
Multi-tenant salon booking PWA within the Pi Network ecosystem. Clients book appointments without registration via direct tenant links. Pi SDK authentication and payment integration. Admin dashboard with modular architecture, drag-and-drop scheduling, and RBAC.

## Architecture
- **Frontend**: React (CRA) + Tailwind + Shadcn/UI + localForage (IndexedDB)
- **Backend**: FastAPI + Motor (MongoDB async) + bcrypt + JWT
- **Database**: MongoDB (multi-tenant via `tenant_id`)
- **Backend Modules** (refactored):
  - `routes.py` — Thin orchestrator (includes 4 sub-routers)
  - `auth_routes.py` — Login, logout, me, change-password
  - `worker_routes.py` — Workers CRUD + account management
  - `admin_routes.py` — Tenants, categories, services, blacklist, settings, reminders
  - `booking_routes.py` — Reservations, client-facing, reschedule, Pi payments
  - `route_utils.py` — Shared helpers (_get_tid, _get_salon_today, etc.)

## Completed Features
- [x] Multi-tenant with slug resolution + 7 CSS variable themes
- [x] Pi SDK auth (PiAuthContext with sandbox) + Pi payment flow
- [x] Admin modular dashboard (CalendarView, SalonWorkers, SalonServices, AdminSettings)
- [x] Drag-and-drop scheduling with double-booking protection
- [x] IndexedDB token persistence (localForage)
- [x] Purged Viber/WhatsApp/Fiat/QR integrations
- [x] Smart login redirects (single /login endpoint)
- [x] RBAC: Worker read-only dashboard (7-day, own column, no DnD, pointer-events disabled)
- [x] Worker account management (create/delete) with auto-generated temp passwords
- [x] Admin UI for worker accounts in SalonWorkers.jsx (create, copy password, delete)
- [x] Backend refactoring: routes.py split into 4 domain-specific modules
- [x] Timezone-aware reservation filtering for workers

## Key API Endpoints
- Auth: `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`, `/api/auth/change-password`
- Workers: `/api/workers` (CRUD), `/api/workers/{id}/create-account`, `/api/workers/{id}/account`
- Reservations: `/api/reservations`, `/api/reservations/{id}/reschedule`, `/api/admin/reservations`
- Payments: `/api/payments/approve`, `/api/payments/complete`
- Admin: `/api/settings`, `/api/blacklist`, `/api/categories`, `/api/services`
- Super: `/api/super/tenants` (CRUD)

## Backlog
- [ ] P3: Worker UI for changing temporary password on first login (must_change_password flow)
- [ ] P3: Extract SalonWorkers sub-dialogs into separate components (~645 lines)
- [ ] P3: Bulk endpoint GET /api/workers/accounts to replace N+1 queries
