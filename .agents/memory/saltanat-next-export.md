---
name: Saltanat web/API deployment
description: Why the Saltanat public website uses Next.js static export and Django for dynamic API routes.
---

**Rule:** Keep the website on Next.js App Router with `output: "export"` and publish the generated `out/` directory. Put runtime behavior in the Django API artifact, preserving the existing `/api` routes and OpenAPI response contract.

**Why:** The Replit web artifact's production service is configured as a static handler. Next.js static export handles the public site, while the separate Django API artifact provides dynamic endpoints. The existing PostgreSQL reservation and event tables are mapped with unmanaged Django models so the backend replacement does not rewrite their schema or data.

**How to apply:** When adding website features, preserve static-export compatibility and use the generated client hooks against `/api`. Keep Django model table/column names aligned with the original Drizzle schema. Do not run Django migrations or Drizzle schema pushes for these existing unmanaged tables. If the artifact deployment model changes, reassess this constraint before adopting SSR.