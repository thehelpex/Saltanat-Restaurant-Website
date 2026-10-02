# Saltanat Restaurant

A public website for Saltanat Restaurant in Karachi, with its menu, visit information, table-request form, and event-inquiry form.

## Run & Operate

- `pnpm --filter @workspace/saltanat-restaurant run dev` — run the Next.js website
- `pnpm --filter @workspace/api-server run dev` — run the Express API server
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- The API server uses the workspace PostgreSQL connection supplied at runtime.

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- Website: Next.js App Router
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)

## Where things live

- `artifacts/saltanat-restaurant/src/app` — App Router pages for home, menu, about, book, events, and contact.
- `artifacts/saltanat-restaurant/src/components` and `src/app/globals.css` — shared UI and visual system.
- `artifacts/saltanat-restaurant/public/brand` — downloaded official wordmark, venue banners, and menu imagery.
- `artifacts/api-server/src/routes/restaurant.ts` — menu, reservation, and event-inquiry endpoints.
- `artifacts/api-server/src/lib/menu-data.ts` — curated public menu data; verify it against the official menu before changing prices or dishes.
- `lib/db/src/schema/restaurant.ts` — persisted reservation and event-inquiry tables.
- `lib/api-spec/openapi.yaml` — source of truth for the generated API client and validation schemas.
- `docs/brand-research.md` — verified brand facts, visual cues, content guardrails, and local search themes.

## Architecture decisions

- The website uses Next.js static export (`out/`) because this web artifact's production service publishes static files; dynamic behavior belongs in the shared Express API.
- Menu prices and item names are taken from Saltanat's public menu and may change; the displayed set is a curated selection, not a claim that every menu item is listed.
- Reservation and event submissions are stored as pending requests. They are not bookings, and there is not yet a staff inbox or automatic notification flow.
- Preserve factual history: the official site provides no verifiable founding year or timeline.

## Product

- A photo-led restaurant website with local SEO copy, menu search/category filters, venue information, opening hours, directions, and contact details.
- Table requests and event inquiries validate against the generated API contract and persist in PostgreSQL. The visitor is asked to call the restaurant to confirm availability.

## User preferences

Keep restaurant history, menu claims, hours, and prices grounded in official sources. Never present a reservation request as confirmed.

## Gotchas

- Keep `next.config.ts` configured for static export and `artifact.toml` pointed at `artifacts/saltanat-restaurant/out`.
- After a database schema change, run `pnpm --filter @workspace/db run push` in development.
- Recheck official hours and prices before publishing; they can change.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
- See `docs/brand-research.md` before changing the restaurant's public copy or visual direction
