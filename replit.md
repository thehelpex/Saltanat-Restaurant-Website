# Saltanat Restaurant

A public website for Saltanat Restaurant in Karachi, with its menu, visit information, table-request form, and event-inquiry form.

## Run & Operate

- `pnpm --filter @workspace/saltanat-restaurant run dev` — run the Next.js website
- `pnpm --filter @workspace/api-server run dev` — run the Django REST Framework API
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-server run test` — run the Django API tests
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- The API server uses `DATABASE_URL` and `SESSION_SECRET` from the environment. Set `DJANGO_ALLOWED_HOSTS` to any production hostnames not provided through Replit's domain variables.
- Set `NEXT_PUBLIC_API_BASE_URL` to the Django API origin when the static frontend and API are served from different origins. Because the frontend is statically exported, this value must be present at build time. Set `CORS_ALLOWED_ORIGINS` on Django to the exact frontend origin(s); debug mode additionally allows the local `localhost:23336` origins.
- For local Windows development, run Django on port `8081` with `SESSION_SECRET`, `DATABASE_URL`, `STAFF_DASHBOARD_USERNAME`, `STAFF_DASHBOARD_PASSWORD`, `DJANGO_DEBUG=true`, and `CORS_ALLOWED_ORIGINS=http://localhost:23336,http://127.0.0.1:23336`. Apply `artifacts/api-server/sql/create_restaurant_tables.sql` and run `python artifacts/api-server/manage.py import_menu_seed` once to initialize the editable catalog. In a second PowerShell terminal, set `PORT=23336` and `NEXT_PUBLIC_API_BASE_URL=http://localhost:8081`, then run the Next.js dev command above. Visit `/order/` or `/manager/`.
- Do not run Django migrations or Drizzle schema pushes as part of the API replacement; the Django models map the existing tables without managing their schema.

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- Website: Next.js App Router
- API: Django 6.1, Django REST Framework, Gunicorn, and Python 3.13
- DB: Existing PostgreSQL tables accessed through Django ORM models (`managed = False`)
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from the shared OpenAPI spec; frontend client contract is unchanged)
- API build: Django system check; Python source compile check

## Where things live

- `artifacts/saltanat-restaurant/src/app` — App Router pages for home, menu, about, book, events, contact, ordering, and the private manager console.
- `artifacts/saltanat-restaurant/src/components` and `src/app/globals.css` — shared UI, menu cart, and pickup/delivery order checkout.
- `artifacts/saltanat-restaurant/public/brand` — downloaded official wordmark, venue banners, and menu imagery.
- `artifacts/api-server/saltanat_api/urls.py` and `views.py` — Django routes and API handlers for public orders and menu, manager catalog and delivery-area CRUD, and staff request inboxes.
- `artifacts/api-server/saltanat_api/notifications.py` and `management/commands/deliver_order_notifications.py` — queued order email and Meta WhatsApp alerts with retry handling.
- `artifacts/api-server/saltanat_api/serializers.py` — request/query validation and menu response serialization.
- `artifacts/api-server/saltanat_api/models.py` — unmanaged Django mappings for catalog, delivery areas, reservations, event inquiries, and orders.
- `artifacts/api-server/sql/create_restaurant_tables.sql` — idempotent PostgreSQL schema setup for these unmanaged tables.
- `artifacts/api-server/saltanat_api/payments.py` — hosted card gateway interface; no provider is configured yet.
- `artifacts/api-server/menu_data.json` — curated public menu data; verify it against the official menu before changing prices or dishes.
- `lib/db/src/schema/restaurant.ts` — original Drizzle table definitions and reference for the existing database structure; Django does not run these migrations.
- `lib/api-spec/openapi.yaml` — source of truth for the generated API client and validation schemas.
- `docs/brand-research.md` — verified brand facts, visual cues, content guardrails, and local search themes.

## Architecture decisions

- The website uses Next.js static export (`out/`) because this web artifact's production service publishes static files; dynamic behavior belongs in the Django API artifact.
- The Django API preserves existing `/api` routes and extends the OpenAPI contract for menu, delivery-area, and order requests.
- Django models use `managed = False`; provision schema with the reviewed SQL script, not `manage.py migrate` or the old Drizzle push flow.
- Manager catalog endpoints require the configured staff Basic credentials. Category, menu-item, and delivery-area deletes only mark rows inactive; manager listings retain those rows, public menu/area listings hide inactive rows, and unavailable menu items remain visible with `isAvailable: false` but cannot be ordered. Each delivery order snapshots the selected active area's name and flat fee and stores a server-calculated total. Requests with inactive/missing areas or unavailable/hidden menu items are rejected before an order is saved.
- Run `pnpm --filter @workspace/api-server run test` against a PostgreSQL test database. Django creates/uses its separate test database for the suite; successful order-submission tests mock the order insert, so the suite does not create public orders in the configured local database. Keep `DATABASE_URL` pointed at the intended development database and ensure its role can create the test database (or configure Django's `TEST.NAME` to a disposable database).
- Public order, reservation, and event-inquiry submissions are rate-limited by client IP. Production throttles use a shared PostgreSQL cache table created by the SQL setup script; local debug uses in-memory cache. The built-in throttle is a baseline, not a substitute for platform-level DDoS/WAF protection.
- COD orders are saved as unpaid requests. Managers can manage orders, catalog, categories, delivery areas/flat fees, reservation requests, and event inquiries at `/manager`; order handling uses the existing staff workflow. The API uses environment-configured Basic authentication. Production redirects HTTP to HTTPS, and staff endpoints reject non-HTTPS traffic. Use a `SESSION_SECRET` of at least 50 random characters, strong staff credentials, explicit allowed hosts/origins, and configure trusted HTTPS proxy headers correctly. Delivery fees are selected from manager-configured service areas and calculated by the server.
- Card payment remains unavailable until a real hosted gateway integration and merchant credentials are activated. Never treat a browser redirect as proof of payment.
- Menu prices and item names are taken from Saltanat's public menu and may change; the displayed set is a curated selection, not a claim that every menu item is listed.
- Reservation and event submissions are stored as requests, not confirmed bookings. Managers can review them in their respective inboxes; automated customer/staff messaging for these request types is not configured.
- Preserve factual history: the official site provides no verifiable founding year or timeline.

## Product

- A photo-led restaurant website with a searchable menu, manager-editable products/categories, configurable delivery areas and flat charges, order workflow, reservations, and event inquiry handling.
- Table requests and event inquiries validate through Django REST Framework and persist in the existing PostgreSQL tables. The visitor is asked to call the restaurant to confirm availability.
- Menu orders can be requested for pickup or delivery with COD. Staff can confirm, progress, complete, or decline orders and mark COD paid on completion. Email and Meta WhatsApp order alerts are queued for delivery after their provider secrets are configured. Live card checkout remains disabled.

## Production go-live checklist

- Provision the production PostgreSQL database and apply `artifacts/api-server/sql/create_restaurant_tables.sql`. Verify the database cache table exists so API throttles are shared across Gunicorn workers.
- Configure a unique `SESSION_SECRET` (at least 50 random characters), `STAFF_DASHBOARD_USERNAME`, `STAFF_DASHBOARD_PASSWORD`, `DJANGO_ALLOWED_HOSTS`, and exact `CORS_ALLOWED_ORIGINS` in deployment secrets. Do not enable `DJANGO_DEBUG`.
- Terminate TLS at a trusted proxy that sets `X-Forwarded-Proto: https`; confirm HTTPS redirects and staff API access through the actual production host before opening orders.
- Set up automated PostgreSQL backups and test restoring one. Monitor API error logs, database capacity, and structured `saltanat.orders` events. Assign a person to watch `/staff/orders` and notification-worker results.
- Configure SMTP secrets: `ORDER_ALERT_SMTP_HOST`, `ORDER_ALERT_SMTP_PORT` (STARTTLS, normally `587`), `ORDER_ALERT_SMTP_USERNAME`, `ORDER_ALERT_SMTP_PASSWORD`, `ORDER_ALERT_FROM_EMAIL`, and comma-separated `ORDER_ALERT_EMAIL_RECIPIENTS`.
- Configure Meta WhatsApp Cloud API secrets: `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_GRAPH_API_VERSION`, `WHATSAPP_ORDER_TEMPLATE_NAME`, optional `WHATSAPP_TEMPLATE_LANGUAGE` (default `en`), and up to 20 comma-separated E.164 `WHATSAPP_ALERT_RECIPIENTS` (the optional leading `+` is removed for the API request). Meta must approve a template whose body has three text placeholders, in this order: short order reference, fulfillment type, and food subtotal.
- Run `python manage.py deliver_order_notifications` every minute as a separately scheduled worker using the same production environment and database. The checked-in Replit API artifact config does not define a scheduled worker, so create that job in the hosting platform before relying on alerts. It reports missing configuration or provider failures and retries transient failures with backoff. WhatsApp retries skip recipients already accepted by Meta. Delivery is at-least-once, so an alert may be duplicated if a worker stops after provider acceptance but before saving success.
- Confirm accepted delivery areas, delivery fee policy, pickup/delivery hours, and staff response procedure with the restaurant. Keep card checkout disabled until the client selects and provisions a gateway.
- Import the curated menu seed only after applying the SQL schema; the default importer preserves manager edits. Use `--update-existing` only when intentionally replacing existing product/category values with seed values.
- Confirm customer-data notice, retention, and deletion procedures before collecting live customer details.

## User preferences

Keep restaurant history, menu claims, hours, and prices grounded in official sources. Never present a reservation request as confirmed.

## Gotchas

- Keep `next.config.ts` configured for static export and `artifact.toml` pointed at `artifacts/saltanat-restaurant/out`.
- Django is configured for the existing PostgreSQL schema; keep model table and column names aligned with `lib/db/src/schema/restaurant.ts`.
- Do not use Django's migration commands for the unmanaged reservation and event tables.
- Before deploying a new database, apply `artifacts/api-server/sql/create_restaurant_tables.sql` to the intended production PostgreSQL database (for example, `psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f artifacts/api-server/sql/create_restaurant_tables.sql`); it creates the unmanaged request and order tables, notification outbox, and shared throttle cache table. This is additive/idempotent for the included schema, but does not automatically repair arbitrary schema drift.
- New delivery requests require a manager-configured active service area; the server calculates and stores that area's flat fee and snapshots its name on the order. Staff status, payment, and any later fee changes are recorded in `restaurant_order_audit`; reapply the idempotent schema script to upgrade an existing database.
- Successful order creation emits a structured log event containing the reference, fulfillment type, and item count (not customer contact/address data); route this to monitored production logs. Go-live still requires the production database upgrade, verified backup/restore and monitoring, validated email/WhatsApp credentials and approved template, a scheduled notification worker, and deployment-specific HTTPS/CORS/host configuration. HSTS subdomain and preload flags should only be enabled after confirming every affected hostname supports HTTPS. The card gateway and merchant credentials remain client decisions.
- Recheck official hours and prices before publishing; they can change.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
- See `docs/brand-research.md` before changing the restaurant's public copy or visual direction
