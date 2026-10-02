---
name: Next.js artifact publishing
description: Why the Saltanat public website uses Next.js static export with the shared Express API.
---

**Rule:** Keep the website on Next.js App Router with `output: "export"` and publish the generated `out/` directory. Put runtime behavior in the shared Express API rather than Next.js server routes or server actions.

**Why:** The Replit web artifact's production service is configured as a static handler. The artifact validator rejected a custom Node server command, while Next.js static export builds successfully and the separate API artifact provides dynamic endpoints.

**How to apply:** When adding website features, preserve static-export compatibility and use the generated client hooks against `/api`. If the artifact deployment model changes, reassess this constraint before adopting SSR.