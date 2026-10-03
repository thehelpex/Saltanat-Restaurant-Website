"use client";

import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { Check, LogIn, LogOut, RefreshCw } from "lucide-react";

type OrderStatus =
  | "awaiting_confirmation"
  | "confirmed"
  | "preparing"
  | "ready"
  | "completed"
  | "cancelled";

type OrderItem = {
  menuItemId: number;
  name: string;
  quantity: number;
  unitPricePkr: number;
};

type StaffOrder = {
  id: string;
  name: string;
  phone: string;
  fulfillmentType: "pickup" | "delivery";
  deliveryAddress: string | null;
  deliveryArea: string | null;
  paymentMethod: "cod" | "card";
  orderStatus: OrderStatus;
  paymentStatus: "unpaid" | "paid";
  subtotalPkr: number;
  deliveryFeePkr: number | null;
  totalPkr: number | null;
  notes: string | null;
  createdAt: string;
  items: OrderItem[];
};

const apiOrigin = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
const formatPrice = (amount: number) =>
  new Intl.NumberFormat("en-PK", { maximumFractionDigits: 0 }).format(amount);
const statusLabels: Record<OrderStatus, string> = {
  awaiting_confirmation: "Needs confirmation",
  confirmed: "Confirmed",
  preparing: "Preparing",
  ready: "Ready",
  completed: "Completed",
  cancelled: "Cancelled",
};

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

function basicToken(username: string, password: string) {
  const bytes = new TextEncoder().encode(`${username}:${password}`);
  let binary = "";
  bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
  return `Basic ${btoa(binary)}`;
}

export function StaffOrders({ authorizationToken, onUnauthorized }: {
  authorizationToken?: string;
  onUnauthorized?: () => void;
}) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [authorization, setAuthorization] = useState(authorizationToken ?? "");
  const [orders, setOrders] = useState<StaffOrder[]>([]);
  const [filter, setFilter] = useState("awaiting_confirmation");
  const [deliveryFees, setDeliveryFees] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [savingOrderId, setSavingOrderId] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const knownOrderIds = useRef<Set<string> | null>(null);

  useEffect(() => {
    if (authorizationToken) setAuthorization(authorizationToken);
  }, [authorizationToken]);

  const loadOrders = useCallback(async (token: string, orderFilter: string): Promise<boolean> => {
    setLoading(true);
    setError("");
    try {
      const params = orderFilter ? `?status=${encodeURIComponent(orderFilter)}` : "";
      const response = await fetch(`${apiOrigin}/api/staff/orders${params}`, {
        headers: { Authorization: token },
        cache: "no-store",
      });
      const result = await readResponse(response);
      if (response.status === 401) {
        setAuthorization("");
        setOrders([]);
        setError("Those staff credentials were rejected. Sign in again.");
        onUnauthorized?.();
        return false;
      }
      if (!response.ok) {
        throw new Error(responseError(result, "Could not load staff orders."));
      }
      if (!Array.isArray(result)) throw new Error("The staff orders response was invalid.");
      const receivedOrders = result as StaffOrder[];
      const knownIds = knownOrderIds.current;
      const newRequests = knownIds
        ? receivedOrders.filter(
            (order) =>
              order.orderStatus === "awaiting_confirmation" &&
              !knownIds.has(order.id),
          )
        : [];
      knownOrderIds.current = new Set([
        ...(knownIds ?? []),
        ...receivedOrders.map((order) => order.id),
      ]);
      if (newRequests.length) {
        setMessage(
          `${newRequests.length} new order request${newRequests.length === 1 ? "" : "s"} received. Review the confirmation queue.`,
        );
      }
      setOrders(receivedOrders);
      return true;
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Could not load staff orders.");
      return false;
    } finally {
      setLoading(false);
    }
  }, [onUnauthorized]);

  useEffect(() => {
    if (authorization) void loadOrders(authorization, filter);
  }, [authorization, filter, loadOrders]);

  useEffect(() => {
    if (!authorization) return;
    const intervalId = window.setInterval(() => {
      void loadOrders(authorization, filter);
    }, 30_000);
    return () => window.clearInterval(intervalId);
  }, [authorization, filter, loadOrders]);

  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");
    const token = basicToken(username, password);
    if (await loadOrders(token, filter)) {
      setAuthorization(token);
      setPassword("");
    }
  }

  async function updateOrder(order: StaffOrder, changes: Record<string, string | number>) {
    setSavingOrderId(order.id);
    setError("");
    setMessage("");
    try {
      const response = await fetch(`${apiOrigin}/api/staff/orders/${order.id}`, {
        method: "PATCH",
        headers: {
          Authorization: authorization,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(changes),
      });
      const result = await readResponse(response);
      if (response.status === 401) {
        setAuthorization("");
        setOrders([]);
        throw new Error("Your staff session is no longer valid. Sign in again.");
      }
      if (!response.ok) {
        throw new Error(responseError(result, "Could not update the order."));
      }
      setMessage(`Order ${order.id.slice(0, 8)} updated.`);
      await loadOrders(authorization, filter);
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : "Could not update the order.");
    } finally {
      setSavingOrderId("");
    }
  }

  function signOut() {
    setAuthorization("");
    setPassword("");
    setOrders([]);
    knownOrderIds.current = null;
    setMessage("");
    setError("");
  }

  return (
    <main className="staff-page">
      <div className="wrap staff-wrap">
        <header className="staff-header">
          <div>
            <div className="eyebrow">Saltanat operations</div>
            <h1 className="display">Order <em>desk.</em></h1>
            <p>Private staff workspace. Customer orders are requests until your team confirms them.</p>
          </div>
          {authorization && !authorizationToken && <button type="button" className="button button-outline" onClick={signOut}><LogOut size={15} /> Sign out</button>}
        </header>

        {!authorization ? (
          <form className="form-card staff-login" onSubmit={signIn}>
            <h2>Staff sign in</h2>
            <p>Use the dashboard credentials configured on the Django API.</p>
            <div className="form-grid">
              <div className="field full"><label htmlFor="staff-username">Username</label><input id="staff-username" autoComplete="username" required value={username} onChange={(event) => setUsername(event.target.value)} /></div>
              <div className="field full"><label htmlFor="staff-password">Password</label><input id="staff-password" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} /></div>
            </div>
            {error && <div className="form-error" role="alert">{error}</div>}
            <button className="button form-submit" type="submit" disabled={loading}>{loading ? "Signing in…" : <><LogIn size={15} /> Sign in</>}</button>
          </form>
        ) : (
          <>
            <div className="staff-toolbar">
              <label className="field"><span className="sr-only">Filter orders</span>
                <select value={filter} onChange={(event) => setFilter(event.target.value)}>
                  <option value="awaiting_confirmation">Needs confirmation</option>
                  <option value="confirmed">Confirmed</option>
                  <option value="preparing">Preparing</option>
                  <option value="ready">Ready</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                  <option value="">All recent orders</option>
                </select>
              </label>
              <button type="button" className="button button-outline" onClick={() => void loadOrders(authorization, filter)} disabled={loading}><RefreshCw size={15} className={loading ? "spin" : ""} /> Refresh</button>
            </div>
            <p className="staff-refresh-note">Order list refreshes automatically every 30 seconds while this page is open.</p>
            {message && <p className="staff-message" role="status"><Check size={15} /> {message}</p>}
            {error && <div className="form-error" role="alert">{error}</div>}
            {loading && !orders.length ? <p className="staff-empty">Loading orders…</p> : orders.length ? (
              <div className="staff-orders">
                {orders.map((order) => <StaffOrderCard
                  key={order.id}
                  order={order}
                  fee={deliveryFees[order.id] ?? (order.deliveryFeePkr === null ? "" : String(order.deliveryFeePkr))}
                  onFeeChange={(value) => setDeliveryFees((current) => ({ ...current, [order.id]: value }))}
                  onUpdate={(changes) => void updateOrder(order, changes)}
                  saving={savingOrderId === order.id}
                />)}
              </div>
            ) : <p className="staff-empty">No orders match this filter.</p>}
          </>
        )}
      </div>
    </main>
  );
}

function StaffOrderCard({
  order,
  fee,
  onFeeChange,
  onUpdate,
  saving,
}: {
  order: StaffOrder;
  fee: string;
  onFeeChange: (value: string) => void;
  onUpdate: (changes: Record<string, string | number>) => void;
  saving: boolean;
}) {
  const nextStep: Partial<Record<OrderStatus, { label: string; status: OrderStatus }>> = {
    awaiting_confirmation: { label: "Confirm order", status: "confirmed" },
    confirmed: { label: "Start preparing", status: "preparing" },
    preparing: { label: "Mark ready", status: "ready" },
    ready: { label: "Complete order", status: "completed" },
  };
  const next = nextStep[order.orderStatus];
  const canConfirm = order.fulfillmentType !== "delivery" || fee.trim() !== "";

  return (
    <article className="staff-order">
      <header className="staff-order-head">
        <div><span className={`staff-status status-${order.orderStatus}`}>{statusLabels[order.orderStatus]}</span><h2>{order.name}</h2></div>
        <span className="staff-order-date">{new Date(order.createdAt).toLocaleString("en-PK", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Karachi" })}</span>
      </header>
      <div className="staff-order-contact">
        <a href={`tel:${order.phone.replace(/[^\d+]/g, "")}`}>{order.phone}</a>
        <span>{order.fulfillmentType === "delivery" ? "Delivery" : "Pickup"} · COD · {order.paymentStatus}</span>
      </div>
      <ul className="staff-order-items">
        {order.items.map((item, index) => <li key={`${item.menuItemId}-${index}`}><span>{item.quantity} × {item.name}</span><strong>PKR {formatPrice(item.quantity * item.unitPricePkr)}</strong></li>)}
      </ul>
      <div className="staff-order-total"><span>Food subtotal</span><strong>PKR {formatPrice(order.subtotalPkr)}</strong></div>
      {order.fulfillmentType === "delivery" && <>
        <p className="staff-address"><strong>Delivery address:</strong> {order.deliveryAddress}{order.deliveryArea ? ` · ${order.deliveryArea}` : ""}</p>
        {order.orderStatus !== "completed" && order.orderStatus !== "cancelled" && <div className="staff-fee-row"><label className="field"><span>Delivery fee (PKR)</span><input type="number" min="0" max="100000" step="1" value={fee} onChange={(event) => onFeeChange(event.target.value)} /></label><button type="button" className="button button-outline" disabled={saving || fee.trim() === ""} onClick={() => onUpdate({ deliveryFeePkr: Number(fee) })}>Save fee</button></div>}
      </>}
      {order.totalPkr !== null && <div className="staff-order-total"><span>Customer total</span><strong>PKR {formatPrice(order.totalPkr)}</strong></div>}
      {order.notes && <p className="staff-notes"><strong>Customer note:</strong> {order.notes}</p>}
      <footer className="staff-order-actions">
        {next && <button type="button" className="button" disabled={saving || (order.orderStatus === "awaiting_confirmation" && !canConfirm)} onClick={() => onUpdate({ orderStatus: next.status, ...(order.orderStatus === "awaiting_confirmation" && order.fulfillmentType === "delivery" && order.deliveryFeePkr === null ? { deliveryFeePkr: Number(fee) } : {}) })}>{saving ? "Saving…" : next.label}</button>}
        {order.orderStatus === "ready" && order.paymentStatus === "unpaid" && <button type="button" className="button button-outline" disabled={saving} onClick={() => onUpdate({ orderStatus: "completed", paymentStatus: "paid" })}>Complete & confirm cash received</button>}
        {order.orderStatus === "awaiting_confirmation" && <button type="button" className="staff-cancel" disabled={saving} onClick={() => onUpdate({ orderStatus: "cancelled" })}>Decline request</button>}
      </footer>
      <p className="staff-order-reference">Order ref: {order.id}</p>
    </article>
  );
}
