# Salon Booking PWA - Product Requirements Document

## Original Problem Statement
Multi-tenant salon booking PWA within the Pi Network ecosystem. Clients book appointments without registration via direct tenant links. Pi SDK authentication and payment integration. Admin dashboard with modular architecture, drag-and-drop scheduling, and RBAC.

## Architecture
- **Frontend**: React (CRA) + Tailwind + Shadcn/UI + localForage (IndexedDB)
- **Backend**: FastAPI + Motor (MongoDB async) + bcrypt + JWT
- **Database**: MongoDB (multi-tenant via `tenant_id`)
- **Auth**: JWT with httpOnly cookies + Bearer token fallback
- **Payments**: Pi Network SDK (sandbox mode on emergentagent.com)

## User Personas
- **Client**: Books via `/:slug`, Pi SDK auth, no registration needed
- **Worker**: Limited read-only view of their own schedule (7 days)
- **Admin**: Full salon management (bookings, workers, services, settings)
- **Super Admin**: God mode across all tenants

## Core Requirements

### Multi-Tenant System
- Tenant resolution via slug
- CSS variable theming (7 themes: Sahara, MidnightVelvet, etc.)
- Feature toggles per tenant
- X-Tenant-ID header isolation

### Booking System
- Multi-service split-booking with Smart Pairing
- 15-min fixed gaps between services
- Anti-conflict/double-booking validation
- Pi payment flow: pending_pi_payment -> confirmed

### Admin Dashboard (Modular)
- CalendarView with Drag-and-Drop rescheduling
- ReservationsTable, AdminSettings, SalonWorkers, SalonServices
- ManualBookingModal for admin-created bookings
- CSV Export (super admin only)

### RBAC (Role-Based Access Control) - COMPLETED
- Roles: super_admin, admin, worker
- Worker accounts created by admins with auto-generated temp passwords
- Workers: read-only CalendarView, own column only, 7-day window
- Workers: no drag-and-drop, no cancel, no blacklist, no manual booking
- Workers: pointer-events disabled on grid blocks
- Workers: date navigation restricted (today -> today+7)
- Timezone-aware date filtering using salon's country

### Pi Network Integration
- PiAuthContext with Sandbox/Production modes
- Payment approval/completion via backend Pi API
- Pi wallet address in salon settings

## API Endpoints (Key)
- `POST /api/auth/login` - Returns role, worker_id, slug
- `GET /api/auth/me` - Returns user with worker_id, language_preference
- `PUT /api/auth/change-password` - Worker temp password change
- `POST /api/workers/{id}/create-account` - Admin creates worker login
- `GET /api/workers/{id}/account` - Check worker account status
- `DELETE /api/workers/{id}/account` - Remove worker login
- `GET /api/reservations` - Filtered by role (worker=own+7day, admin=all)
- `PUT /api/reservations/{id}/reschedule` - Drag-and-drop update
- `POST /api/payments/approve` & `complete` - Pi API hooks

## DB Schema (Key Fields)
- `users`: email, password_hash, role, worker_id, tenant_id, language_preference, must_change_password
- `tenants`: slug, tenant_id, theme, country, enabled_features
- `workers`: name, services, work_start/end, break_start/end, days_off, tenant_id
- `reservations`: date, time, end_time, worker_time_blocks, service_worker_pairs, pi_*, payment_status

## Completed Features
- [x] Multi-tenant with slug resolution
- [x] 7 CSS variable themes with dynamic application
- [x] Pi SDK auth (PiAuthContext with sandbox)
- [x] Pi payment flow in booking
- [x] Admin modular dashboard refactoring
- [x] Drag-and-drop scheduling with double-booking protection
- [x] IndexedDB token persistence (localForage)
- [x] Purged Viber/WhatsApp/Fiat/QR integrations
- [x] Smart login redirects (single /login endpoint)
- [x] Worker hours bounded by salon hours
- [x] RBAC: Worker read-only dashboard (7-day, own column, no DnD)
- [x] Worker account management endpoints (create/get/delete)
- [x] Temp password flow with must_change_password flag
- [x] Timezone-aware reservation filtering for workers
- [x] Test worker seed (Marija / worker@salon.com)

## Backlog
- [ ] P2: Refactor routes.py (>1500 lines) into domain-specific files
- [ ] P3: Worker UI for changing temporary password on first login
- [ ] P3: Admin UI for managing worker accounts (in SalonWorkers.jsx)
