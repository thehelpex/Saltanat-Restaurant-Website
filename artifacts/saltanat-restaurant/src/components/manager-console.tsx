"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { LogIn, LogOut, RefreshCw, Save, Trash2 } from "lucide-react";
import { StaffOrders } from "@/components/staff-orders";

type Category = { id: number; name: string; sortOrder: number; isActive: boolean };
type MenuItem = {
  id: number;
  name: string;
  categoryId: number;
  categoryName: string;
  description: string | null;
  pricePkr: number;
  imageUrl: string | null;
  isFeatured: boolean;
  isAvailable: boolean;
  isActive: boolean;
  sortOrder: number;
};
type DeliveryArea = {
  id: number;
  name: string;
  deliveryFeePkr: number;
  isActive: boolean;
  sortOrder: number;
};
type RequestRecord = {
  id: string;
  name: string;
  phone: string;
  status: string;
  createdAt: string;
  preferredDate?: string | null;
  preferredTime?: string;
  guestCount: number;
  eventType?: string;
  email?: string | null;
  notes?: string | null;
};
type Tab = "orders" | "products" | "categories" | "delivery" | "reservations" | "events";

const apiOrigin = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
const tabs: { id: Tab; label: string }[] = [
  { id: "orders", label: "Orders" },
  { id: "products", label: "Menu items" },
  { id: "categories", label: "Categories" },
  { id: "delivery", label: "Delivery areas" },
  { id: "reservations", label: "Reservations" },
  { id: "events", label: "Event inquiries" },
];

async function readResponse(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return undefined;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

function responseError(payload: unknown, fallback: string): string {
  if (typeof payload === "string" && payload.trim()) return payload;
  if (!payload || typeof payload !== "object") return fallback;
  const record = payload as Record<string, unknown>;
  if (typeof record.error === "string") return record.error;
  if (typeof record.detail === "string") return record.detail;
  for (const value of Object.values(record)) {
    if (typeof value === "string" && value.trim()) return value;
    if (Array.isArray(value)) {
      const message = value.find((entry) => typeof entry === "string" && entry.trim());
      if (typeof message === "string") return message;
    }
  }
  return fallback;
}

function makeBasicToken(username: string, password: string) {
  const bytes = new TextEncoder().encode(`${username}:${password}`);
  let binary = "";
  bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
  return `Basic ${btoa(binary)}`;
}

function ManagerConsole() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [authorization, setAuthorization] = useState("");
  const [tab, setTab] = useState<Tab>("products");
  const [categories, setCategories] = useState<Category[]>([]);
  const [items, setItems] = useState<MenuItem[]>([]);
  const [areas, setAreas] = useState<DeliveryArea[]>([]);
  const [reservations, setReservations] = useState<RequestRecord[]>([]);
  const [events, setEvents] = useState<RequestRecord[]>([]);
  const [editItem, setEditItem] = useState<MenuItem | null>(null);
  const [editCategory, setEditCategory] = useState<Category | null>(null);
  const [editArea, setEditArea] = useState<DeliveryArea | null>(null);
  const [loading, setLoading] = useState(false);
  const [authenticating, setAuthenticating] = useState(false);
  const [mutating, setMutating] = useState(false);
  const [hasLoadedData, setHasLoadedData] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const request = useCallback(async <T,>(path: string, method = "GET", body?: unknown): Promise<T> => {
    const response = await fetch(`${apiOrigin}${path}`, {
      method,
      headers: {
        Authorization: authorization,
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      cache: "no-store",
    });
    if (response.status === 401) {
      setAuthorization("");
      throw new Error("Your manager credentials were rejected. Sign in again.");
    }
    if (response.status === 204) return undefined as T;
    const result = await readResponse(response);
    if (!response.ok) {
      throw new Error(responseError(result, "The manager request failed."));
    }
    return result as T;
  }, [authorization]);

  const loadData = useCallback(async (token = authorization): Promise<boolean> => {
    if (!token) return false;
    setLoading(true);
    setError("");
    try {
      const load = async <T,>(path: string): Promise<T> => {
        const response = await fetch(`${apiOrigin}${path}`, {
          headers: { Authorization: token },
          cache: "no-store",
        });
        const result = await readResponse(response);
        if (response.status === 401) {
          setAuthorization("");
          setHasLoadedData(false);
          setCategories([]);
          setItems([]);
          setAreas([]);
          setReservations([]);
          setEvents([]);
          throw new Error("Your manager credentials were rejected. Sign in again.");
        }
        if (!response.ok) {
          throw new Error(responseError(result, "Could not load manager data."));
        }
        return result as T;
      };
      const [categoryRows, itemRows, areaRows, reservationRows, eventRows] = await Promise.all([
        load<Category[]>("/api/manager/menu/categories"),
        load<MenuItem[]>("/api/manager/menu/items"),
        load<DeliveryArea[]>("/api/manager/delivery-areas"),
        load<RequestRecord[]>("/api/manager/reservations"),
        load<RequestRecord[]>("/api/manager/event-inquiries"),
      ]);
      setCategories(categoryRows);
      setItems(itemRows);
      setAreas(areaRows);
      setReservations(reservationRows);
      setEvents(eventRows);
      setHasLoadedData(true);
      return true;
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Could not load manager data.");
      return false;
    } finally {
      setLoading(false);
    }
  }, [authorization]);

  useEffect(() => {
    if (authorization) void loadData();
  }, [authorization, loadData]);

  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");
    setAuthenticating(true);
    const token = makeBasicToken(username, password);
    try {
      const response = await fetch(`${apiOrigin}/api/manager/menu/categories`, {
        headers: { Authorization: token },
        cache: "no-store",
      });
      const result = await readResponse(response);
      if (!response.ok) {
        setError(response.status === 401
          ? "Credentials rejected. Check the manager username and password."
          : responseError(result, "Could not sign in to the manager API."));
        return;
      }
      setCategories(result as Category[]);
      setAuthorization(token);
    } catch {
      setError("Could not reach the API. Check that the Django service is running.");
    } finally {
      setAuthenticating(false);
    }
  }

  async function mutate(action: () => Promise<unknown>, success: string): Promise<boolean> {
    setError("");
    setMessage("");
    setMutating(true);
    try {
      await action();
      setMessage(success);
      await loadData();
      return true;
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "The change could not be saved.");
      return false;
    } finally {
      setMutating(false);
    }
  }

  async function saveItem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const values = {
      name: String(form.get("name")).trim(),
      categoryId: Number(form.get("categoryId")),
      description: String(form.get("description")).trim() || null,
      pricePkr: Number(form.get("pricePkr")),
      imageUrl: String(form.get("imageUrl")).trim() || null,
      isFeatured: form.has("isFeatured"),
      isAvailable: form.has("isAvailable"),
      isActive: form.has("isActive"),
      sortOrder: Number(form.get("sortOrder") || 0),
    };
    const saved = await mutate(() => request(
      editItem ? `/api/manager/menu/items/${editItem.id}` : "/api/manager/menu/items",
      editItem ? "PATCH" : "POST",
      values,
    ), editItem ? "Menu item updated." : "Menu item added.");
    if (saved) {
      setEditItem(null);
      formElement.reset();
    }
  }

  async function saveCategory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const saved = await mutate(() => request(
      editCategory ? `/api/manager/menu/categories/${editCategory.id}` : "/api/manager/menu/categories",
      editCategory ? "PATCH" : "POST",
      {
        name: String(form.get("name")).trim(),
        sortOrder: Number(form.get("sortOrder") || 0),
        isActive: form.has("isActive"),
      },
    ), editCategory ? "Category updated." : "Category added.");
    if (saved) {
      setEditCategory(null);
      formElement.reset();
    }
  }

  async function saveArea(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const saved = await mutate(() => request(
      editArea ? `/api/manager/delivery-areas/${editArea.id}` : "/api/manager/delivery-areas",
      editArea ? "PATCH" : "POST",
      {
        name: String(form.get("name")).trim(),
        deliveryFeePkr: Number(form.get("deliveryFeePkr")),
        sortOrder: Number(form.get("sortOrder") || 0),
        isActive: form.has("isActive"),
      },
    ), editArea ? "Delivery area updated." : "Delivery area added.");
    if (saved) {
      setEditArea(null);
      formElement.reset();
    }
  }

  function changeRequestStatus(path: string, id: string, status: string, success: string) {
    return mutate(() => request(`${path}/${id}`, "PATCH", { status }), success);
  }

  const signOut = useCallback(() => {
    setAuthorization("");
    setPassword("");
    setHasLoadedData(false);
    setCategories([]);
    setItems([]);
    setAreas([]);
    setReservations([]);
    setEvents([]);
    setMessage("");
    setError("");
  }, []);

  if (!authorization) {
    return (
      <main className="page-content manager-content">
        <div className="wrap manager-wrap">
          <div className="eyebrow">Saltanat operations</div>
          <h1 className="display">Manager <em>sign in.</em></h1>
          <form className="form-card manager-login" onSubmit={signIn}>
            <h2>Staff credentials</h2>
            <div className="form-grid">
              <div className="field full"><label htmlFor="manager-user">Username</label><input id="manager-user" autoComplete="username" required value={username} onChange={(event) => setUsername(event.target.value)} /></div>
              <div className="field full"><label htmlFor="manager-password">Password</label><input id="manager-password" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} /></div>
            </div>
            {error && <div className="form-error" role="alert">{error}</div>}
            <button className="button form-submit" type="submit" disabled={authenticating}>
              {authenticating ? <><RefreshCw size={15} className="spin" /> Signing in…</> : <><LogIn size={15} /> Sign in</>}
            </button>
          </form>
        </div>
      </main>
    );
  }

  return (
    <main className="page-content manager-content">
      <div className="wrap manager-wrap">
        <header className="manager-header">
          <div><div className="eyebrow">Saltanat operations</div><h1 className="display">Manager <em>console.</em></h1><p>Maintain the live menu, service areas, and customer requests.</p></div>
          <div className="manager-actions">
            <button type="button" className="button button-outline" onClick={() => void loadData()} disabled={loading}><RefreshCw size={15} /> Refresh</button>
            <button type="button" className="button button-outline" onClick={signOut} disabled={mutating}><LogOut size={15} /> Sign out</button>
          </div>
        </header>
        <nav className="manager-tabs" aria-label="Manager sections">
          {tabs.map((entry) => <button type="button" key={entry.id} className={tab === entry.id ? "manager-tab active" : "manager-tab"} onClick={() => setTab(entry.id)}>{entry.label}</button>)}
        </nav>
        {error && <div className="form-error" role="alert">{error}</div>}
        {message && <div className="manager-success" role="status">{message}</div>}
        {loading && <p role="status">{hasLoadedData ? "Refreshing manager data…" : "Loading manager data…"}</p>}
        {!hasLoadedData && !loading && error && <button type="button" className="button button-outline" onClick={() => void loadData()}><RefreshCw size={15} /> Try loading again</button>}

        {hasLoadedData && <>
        {tab === "orders" && <StaffOrders authorizationToken={authorization} onUnauthorized={signOut} />}

        {tab === "products" && <>
          <div className="manager-section-heading"><div><h2>{editItem ? "Edit menu item" : "Add menu item"}</h2><p>Changes appear on the public menu after saving.</p></div></div>
          {!categories.some((category) => category.isActive) && <p className="notice">Create an active category before adding products.</p>}
          {categories.some((category) => category.isActive) && <form key={editItem?.id ?? "new-item"} className="form-card manager-editor" onSubmit={saveItem}>
            <div className="form-grid">
              <div className="field"><label htmlFor="item-name">Name</label><input id="item-name" name="name" required minLength={2} maxLength={120} defaultValue={editItem?.name ?? ""} /></div>
              <div className="field"><label htmlFor="item-category">Category</label><select id="item-category" name="categoryId" required defaultValue={editItem?.categoryId ?? ""}>{categories.filter((category) => category.isActive).map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></div>
              <div className="field"><label htmlFor="item-price">Price (PKR)</label><input id="item-price" name="pricePkr" type="number" min="0" max="1000000" step="1" required defaultValue={editItem?.pricePkr ?? ""} /></div>
              <div className="field"><label htmlFor="item-image">Image path or HTTPS URL</label><input id="item-image" name="imageUrl" maxLength={500} defaultValue={editItem?.imageUrl ?? ""} placeholder="/brand/menu/item.jpg" /></div>
              <div className="field full"><label htmlFor="item-description">Description</label><textarea id="item-description" name="description" maxLength={1000} defaultValue={editItem?.description ?? ""} /></div>
              <div className="field"><label htmlFor="item-sort">Display order</label><input id="item-sort" name="sortOrder" type="number" min="0" step="1" defaultValue={editItem?.sortOrder ?? 0} /></div>
              <label className="choice-option"><input name="isFeatured" type="checkbox" defaultChecked={editItem?.isFeatured ?? false} /> Featured</label>
              <label className="choice-option"><input name="isAvailable" type="checkbox" defaultChecked={editItem?.isAvailable ?? true} /> Available to order</label>
              <label className="choice-option"><input name="isActive" type="checkbox" defaultChecked={editItem?.isActive ?? true} /> Visible on public menu</label>
            </div>
            <div className="manager-actions"><button className="button" type="submit" disabled={mutating}><Save size={15} /> {mutating ? "Saving…" : editItem ? "Save item" : "Add item"}</button>{editItem && <button type="button" className="button button-outline" onClick={() => setEditItem(null)} disabled={mutating}>Cancel edit</button>}</div>
          </form>}
            {!items.length ? <p className="empty-panel">No menu items yet. Add the first item above.</p> : <div className="manager-list">{items.map((item) => <article className="manager-row" key={item.id}><div><strong>{item.name}</strong><span>{item.categoryName} · PKR {item.pricePkr} · {item.isAvailable ? "Available" : "Sold out"} · {item.isActive ? "Live" : "Hidden"}</span></div><div className="manager-actions"><button type="button" className="button button-outline" onClick={() => { setEditItem(item); window.scrollTo({ top: 0, behavior: "smooth" }); }} disabled={mutating}>Edit</button>{item.isActive && <button type="button" aria-label={`Deactivate ${item.name}`} className="icon-button" disabled={mutating} onClick={() => void mutate(() => request(`/api/manager/menu/items/${item.id}`, "DELETE"), "Menu item hidden from the public menu.")}><Trash2 size={16} /></button>}</div></article>)}</div>}
        </>}

        {tab === "categories" && <>
          <div className="manager-section-heading"><div><h2>Menu categories</h2><p>Inactive categories stay attached to historical items but disappear from the public menu.</p></div></div>
            <form key={editCategory?.id ?? "new-category"} className="form-card manager-inline-form" onSubmit={saveCategory}><div className="field"><label htmlFor="category-name">Category name</label><input id="category-name" name="name" required minLength={2} maxLength={80} defaultValue={editCategory?.name ?? ""} /></div><div className="field"><label htmlFor="category-sort">Display order</label><input id="category-sort" name="sortOrder" type="number" min="0" step="1" defaultValue={editCategory?.sortOrder ?? 0} /></div><label className="choice-option"><input name="isActive" type="checkbox" defaultChecked={editCategory?.isActive ?? true} /> Active</label><button className="button" type="submit" disabled={mutating}>{mutating ? "Saving…" : editCategory ? "Save category" : "Add category"}</button>{editCategory && <button type="button" className="button button-outline" onClick={() => setEditCategory(null)} disabled={mutating}>Cancel</button>}</form>
            {!categories.length ? <p className="empty-panel">No categories yet. Add one before creating menu items.</p> : <div className="manager-list">{categories.map((category) => <article className="manager-row" key={category.id}><div><strong>{category.name}</strong><span>Order {category.sortOrder} · {category.isActive ? "Active" : "Inactive"}</span></div><div className="manager-actions"><button type="button" className="button button-outline" onClick={() => { setEditCategory(category); window.scrollTo({ top: 0, behavior: "smooth" }); }} disabled={mutating}>Edit</button>{category.isActive && <button type="button" className="icon-button" aria-label={`Deactivate ${category.name}`} disabled={mutating} onClick={() => void mutate(() => request(`/api/manager/menu/categories/${category.id}`, "DELETE"), "Category deactivated.")}><Trash2 size={16} /></button>}</div></article>)}</div>}
        </>}

        {tab === "delivery" && <>
          <div className="manager-section-heading">
            <div>
              <h2>Delivery areas and flat fees</h2>
              <p>Configure the areas customers can select at checkout; set actual coverage and fees before publishing.</p>
            </div>
          </div>
          <form key={editArea?.id ?? "new-area"} className="form-card manager-inline-form" onSubmit={saveArea}>
            <div className="field">
              <label htmlFor="area-name">Area name</label>
              <input id="area-name" name="name" required minLength={2} maxLength={120} defaultValue={editArea?.name ?? ""} />
            </div>
            <div className="field">
              <label htmlFor="area-fee">Delivery fee (PKR)</label>
              <input id="area-fee" name="deliveryFeePkr" type="number" min="0" max="100000" step="1" required defaultValue={editArea?.deliveryFeePkr ?? ""} />
            </div>
            <div className="field">
              <label htmlFor="area-sort">Display order</label>
              <input id="area-sort" name="sortOrder" type="number" min="0" step="1" defaultValue={editArea?.sortOrder ?? 0} />
            </div>
            <label className="choice-option">
              <input name="isActive" type="checkbox" defaultChecked={editArea?.isActive ?? true} /> Active at checkout
            </label>
            <button className="button" type="submit" disabled={mutating}>
              {mutating ? "Saving…" : editArea ? "Save area" : "Add area"}
            </button>
            {editArea && <button type="button" className="button button-outline" onClick={() => setEditArea(null)} disabled={mutating}>Cancel</button>}
          </form>
          {!areas.length ? (
            <p className="empty-panel">No delivery areas yet. Add the zones and flat fees customers can choose at checkout.</p>
          ) : (
            <div className="manager-list">
              {areas.map((area) => (
                <article className="manager-row" key={area.id}>
                  <div>
                    <strong>{area.name}</strong>
                    <span>PKR {area.deliveryFeePkr} · {area.isActive ? "Available at checkout" : "Inactive"}</span>
                  </div>
                  <div className="manager-actions">
                    <button type="button" className="button button-outline" onClick={() => {
                      setEditArea(area);
                      window.scrollTo({ top: 0, behavior: "smooth" });
                    }} disabled={mutating}>Edit</button>
                    {area.isActive && (
                      <button
                        type="button"
                        className="icon-button"
                        aria-label={`Deactivate ${area.name}`}
                        disabled={mutating}
                        onClick={() => void mutate(
                          () => request(`/api/manager/delivery-areas/${area.id}`, "DELETE"),
                          "Delivery area deactivated.",
                        )}
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                </article>
              ))}
            </div>
          )}
        </>}

          {tab === "reservations" && <RequestList title="Reservation requests" rows={reservations} statuses={["awaiting_confirmation", "confirmed", "declined", "cancelled"]} disabled={mutating} onStatus={(id, status) => changeRequestStatus("/api/manager/reservations", id, status, "Reservation status updated.")} />}
          {tab === "events" && <RequestList title="Event inquiries" rows={events} statuses={["received", "contacted", "completed", "declined"]} disabled={mutating} onStatus={(id, status) => changeRequestStatus("/api/manager/event-inquiries", id, status, "Event inquiry status updated.")} />}
          </>}
      </div>
    </main>
  );
}

function RequestList({ title, rows, statuses, disabled, onStatus }: {
  title: string;
  rows: RequestRecord[];
  statuses: string[];
  disabled: boolean;
  onStatus: (id: string, status: string) => void;
}) {
  return <section className="manager-requests"><div className="manager-section-heading"><div><h2>{title}</h2><p>Latest 200 requests; update each status as staff follows up.</p></div></div>
    {!rows.length ? <p className="empty-panel">No requests yet.</p> : rows.map((row) => <article className="manager-request" key={row.id}><div className="manager-request-info"><strong>{row.name}</strong><span>{row.phone}{row.email ? ` · ${row.email}` : ""}</span><span>{row.eventType ?? `${row.preferredDate ?? "Date not set"}${row.preferredTime ? ` at ${row.preferredTime}` : ""}`} · {row.guestCount} guests</span>{row.notes && <p>{row.notes}</p>}</div><label className="field">Status<select value={row.status} disabled={disabled} onChange={(event) => onStatus(row.id, event.target.value)}>{statuses.map((status) => <option key={status} value={status}>{status.replaceAll("_", " ")}</option>)}</select></label></article>)}
  </section>;
}

export { ManagerConsole };
