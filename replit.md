# Saltanat Restaurant

A public website for Saltanat Restaurant in Karachi, with its menu, visit information, table-request form, and event-inquiry form.

## Run & Operate

- `pnpm --filter @workspace/saltanat-restaurant run dev` — run the Next.js website
- `pnpm --filter @workspace/api-server run dev` — run the Django REST Framework API
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-server run test` — run the Django API tests
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- The API server uses `DATABASE_URL` and `SESSION_SECRET` from the environment.
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

- `artifacts/saltanat-restaurant/src/app` — App Router pages for home, menu, about, book, events, and contact.
- `artifacts/saltanat-restaurant/src/components` and `src/app/globals.css` — shared UI and visual system.
- `artifacts/saltanat-restaurant/public/brand` — downloaded official wordmark, venue banners, and menu imagery.
- `artifacts/api-server/saltanat_api/urls.py` and `views.py` — Django routes and API handlers.
- `artifacts/api-server/saltanat_api/serializers.py` — request/query validation and menu response serialization.
- `artifacts/api-server/saltanat_api/models.py` — unmanaged Django mappings to the existing PostgreSQL tables.
- `artifacts/api-server/menu_data.json` — curated public menu data; verify it against the official menu before changing prices or dishes.
- `lib/db/src/schema/restaurant.ts` — original Drizzle table definitions and reference for the existing database structure; Django does not run these migrations.
- `lib/api-spec/openapi.yaml` — source of truth for the generated API client and validation schemas.
- `docs/brand-research.md` — verified brand facts, visual cues, content guardrails, and local search themes.

## Architecture decisions

- The website uses Next.js static export (`out/`) because this web artifact's production service publishes static files; dynamic behavior belongs in the Django API artifact.
- The Django API preserves the existing `/api` routes and OpenAPI response contract so the generated frontend client remains unchanged.
- Django models use `managed = False` to preserve existing PostgreSQL tables and rows. Do not run `manage.py migrate` or the old Drizzle push flow for this conversion.
- Menu prices and item names are taken from Saltanat's public menu and may change; the displayed set is a curated selection, not a claim that every menu item is listed.
- Reservation and event submissions are stored as pending requests. They are not bookings, and there is not yet a staff inbox or automatic notification flow.
- Preserve factual history: the official site provides no verifiable founding year or timeline.

## Product

- A photo-led restaurant website with local SEO copy, menu search/category filters, venue information, opening hours, directions, and contact details.
- Table requests and event inquiries validate through Django REST Framework and persist in the existing PostgreSQL tables. The visitor is asked to call the restaurant to confirm availability.

## User preferences

Keep restaurant history, menu claims, hours, and prices grounded in official sources. Never present a reservation request as confirmed.

## Gotchas

- Keep `next.config.ts` configured for static export and `artifact.toml` pointed at `artifacts/saltanat-restaurant/out`.
- Django is configured for the existing PostgreSQL schema; keep model table and column names aligned with `lib/db/src/schema/restaurant.ts`.
- Do not use Django's migration commands for the unmanaged reservation and event tables.
- Recheck official hours and prices before publishing; they can change.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
- See `docs/brand-research.md` before changing the restaurant's public copy or visual direction
