# Saltanat website rollout plan

## Product direction

Build a fast, mobile-first digital front door for Saltanat's Karachi audience, with three clear paths: browse the menu and order, plan a dine-in visit, or ask about a family/corporate event. The official site describes Saltanat as family-friendly and shows delivery and dine-in area selection; the refreshed experience should make those paths easier without claiming details the restaurant has not confirmed.

Verified public references:

- Official site and service-area selector: https://saltanatrestaurant.com/
- Official menu: https://saltanatrestaurant.com/menu
- Official Facebook: https://www.facebook.com/saltanatrestaurantpk/
- Official Instagram: https://instagram.com/saltanatrestaurantpk
- Official phone shown on the website: 021 111-111-771

The official menu includes BBQ, karahi, burgers, sandwiches, seafood, salads, pasta, kids' and family platters. Keep the online menu curated and manager-editable, and confirm current availability and prices with the restaurant before launch. Do not invent branch addresses, opening hours, founding history, or delivery coverage.

## Customer experience

1. **Home:** lead with food photography and concise links to menu, order, directions/contact, and events. Make phone ordering visible.
2. **Menu:** category navigation, search, clear PKR prices, item availability, descriptions, and accessible photos. Keep sold-out dishes visible as unavailable rather than accepting stale-cart submissions.
3. **Order:** retain cart through navigation; collect a phone number and pickup/delivery choice; for delivery require a manager-configured service area and show its flat fee. Server-calculated totals are estimates pending staff confirmation, not proof an order is accepted.
4. **Dine-in and family visits:** explain the request-versus-confirmation distinction for table requests. Publish hours/branch information only after the client verifies them.
5. **Events:** provide a short inquiry form and a clear follow-up expectation, not an unverified instant booking promise.
6. **Trust and access:** publish a customer-data notice, contact method, cancellation/refund policy, and accessibility-friendly keyboard/mobile behavior before public launch.

## Manager operations

The `/manager/` console is the daily operations workspace:

- **Orders:** review requests, set/confirm delivery fee where needed, move orders through confirmation/preparation/completion, and mark COD collected only on completion.
- **Menu items and categories:** create, edit, order, mark sold out, and deactivate records. Deactivation preserves historical order references.
- **Delivery areas:** maintain active Karachi service-area names and flat PKR fees. These are explicit zones, not calculated route distances; the client must supply actual zones/fees.
- **Reservations and event inquiries:** review and update request statuses. Status changes do not notify customers automatically.

Use individual manager accounts or an authenticated identity provider before multiple staff members share operations. Current staff access is environment-configured Basic authentication over HTTPS; use long unique credentials, restrict access at the hosting/WAF layer where possible, and do not embed credentials in browser storage.

## Launch phases

### 1. Confirm business rules

Obtain client approval for the exact menu/prices, areas and flat fees, pickup/delivery hours, order cutoff behavior, staff response SLA, cancellation/refund rules, and who owns the inbox. Confirm the correct branch/phone details and any official logo/photo usage.

### 2. Configure the system

Provision PostgreSQL, apply `artifacts/api-server/sql/create_restaurant_tables.sql`, import the curated menu, then review every product in `/manager/`. Configure delivery zones only from client-approved coverage data. Set production secrets, hosts, CORS, TLS/proxy settings, customer-data retention, backups, monitoring, and the scheduled notification worker.

### 3. Operational acceptance

Test the production domain on mobile and desktop. Verify category/product edits appear publicly, sold-out items cannot be ordered, area fees and totals are server-calculated, manager authentication and role procedures work, requests can be progressed, rate limits operate, alerts/retries work, database restore succeeds, and staff can follow documented fallback procedures.

### 4. Payment and messaging activation

Keep cards unavailable until the client chooses a Pakistan-eligible gateway, completes merchant onboarding, confirms settlement/fees/refunds, and provides credentials. Implement the provider's hosted checkout plus signed webhook verification and refund/reconciliation operations. Enable WhatsApp only after the client supplies Meta credentials, approved template, and recipient numbers; test delivery and opt-in/privacy requirements. Do not claim these integrations are live before testing.

### 5. Growth and iteration

After launch, review search queries, menu conversion, abandoned carts, order fulfillment time, unavailable items, and area-level demand. Improve Karachi-local search content around verified cuisine/service intent, optimize image weight and Core Web Vitals, and add campaigns only with client-approved offers and tracking consent. Keep review requests and social links tied to official accounts.

## Go-live gates

- Client-signed menu, service zones/fees, hours, branch/contact, customer policies, and staff workflow.
- Production API/database deployment, TLS, CORS, strong secrets, backup/restore evidence, monitoring, and access control.
- Manager acceptance test for product/category/area edits and requests; customer acceptance test on supported mobile browsers.
- SMTP/WhatsApp worker successfully tested if alerts are part of launch; otherwise a clearly assigned manual monitoring process.
- Gateway onboarding and end-to-end payment verification before advertising card payment.

This plan is an operational blueprint, not a statement that those deployment-dependent gates or external provider accounts are already complete.
