# Salon Booking PWA - Product Requirements Document

## Original Problem Statement
Multi-tenant salon booking PWA within the Pi Network ecosystem. Full i18n support (7 languages).

## Architecture
- **Frontend**: React 18 + Tailwind + Shadcn/UI + localForage + i18n
- **Backend**: FastAPI + Motor (MongoDB async) + bcrypt + JWT
- **Database**: MongoDB (multi-tenant via `tenant_id`)

## Completed Features
- [x] Multi-tenant with slug resolution + 7 CSS themes + SVG patterns
- [x] Pi SDK auth + Pi payment flow (sandbox/production)
- [x] Admin modular dashboard with Drag-and-Drop scheduling
- [x] RBAC: Worker read-only dashboard (7-day, own column)
- [x] Worker account management (create/delete/reset-password)
- [x] Forced password change on first login
- [x] Backend routes.py split into 4 domain modules
- [x] SalonWorkers.jsx split into 4 component files
- [x] N+1 bulk optimization, brute-force (persistent), CORS cleanup
- [x] Tenant-aware logout redirect
- [x] OwnersPage interactive guide with modals
- [x] Booking flow: multi-service selection on Step 1
- [x] **Full i18n (7 languages)**: sr, en, id, tl, pt-BR, es, fr
  - Category and service name translation with fuzzy matching
  - date-fns locale per language
  - Language selector in header AND My Reservations modal
  - localStorage persistence
  - Global phone codes (ID, PH, BR, ES, US, FR)
  - PhoneInput error message translated

## Supported Languages
sr (Srpski), en (English), id (Bahasa Indonesia), tl (Filipino/Tagalog), pt-BR (Português BR), es (Español), fr (Français)

## Backlog
- [ ] P4: Store service translations in DB (admin-editable per tenant)

## 2026-06 Owners page Feature Showcase
- /vlasnici: video placeholders replaced with browser-frame mockup showcase (4 tabs), images at /frontend/public/mockups/{settings,services,workers,calendar}.png with fallback placeholder; activation card with Pi @Markonijus23 + bornaja23@gmail.com
- Demo salon renamed to Beauty Studio Bor; Pi wallet seeded
- Admin Usluge: categories as collapsible sections (first open by default), "Otvori sve"/"Zatvori sve" buttons
- /vlasnici: mockup lightbox (Uvećaj / click image), auto-rotating tabs every 5s (pauses on hover & while lightbox open), progress dots; settings.png cropped (browser bar removed)
- /vlasnici: phone-frame mockup with *-mobile.png screenshots on screens <640px (desktop keeps browser frame); lightbox uses matching image. Script: /app/scripts/capture_mobile_mockups.py (needs playwright, PLAYWRIGHT_BROWSERS_PATH=/pw-browsers)
- Fix: admin <main> min-w-0 — services page no longer overflows horizontally on mobile when categories expanded
- Admin Usluge: delete confirmation dialog (reuses DeleteWorkerDialog with itemLabel prop)
- Pi SDK script tag in index.html; PiAuthContext: mock Pi user only on preview hosts (localhost/emergentagent.com); production requires Pi Browser (UA PiBrowser) else BookingPage shows PiBrowserRequired screen (7 langs). Pi.init sandbox:false (Testnet chosen via Dev Portal app registration). Backend is_sandbox mock payment path kept per user choice.
