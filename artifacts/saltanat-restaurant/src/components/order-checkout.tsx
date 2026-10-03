"use client";

import {
  useCreateRestaurantOrder,
  type RestaurantOrderInput,
  type RestaurantOrderReceipt,
} from "@workspace/api-client-react";
import { ArrowRight, Check, Minus, Plus, RotateCw, Trash2 } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { useCart } from "@/components/cart";

type FulfillmentType = "pickup" | "delivery";
type DeliveryArea = {
  id: number;
  name: string;
  deliveryFeePkr: number;
  isActive: boolean;
  sortOrder: number;
};
const apiOrigin = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

const formatPrice = (amount: number) =>
  new Intl.NumberFormat("en-PK", { maximumFractionDigits: 0 }).format(amount);

export function OrderCheckout() {
  const cart = useCart();
  const orderRequest = useCreateRestaurantOrder();
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [fulfillmentType, setFulfillmentType] = useState<FulfillmentType>("pickup");
  const [deliveryAddress, setDeliveryAddress] = useState("");
  const [deliveryAreaId, setDeliveryAreaId] = useState("");
  const [notes, setNotes] = useState("");
  const [receipt, setReceipt] = useState<RestaurantOrderReceipt | null>(null);
  const [error, setError] = useState("");
  const [deliveryAreas, setDeliveryAreas] = useState<DeliveryArea[]>([]);
  const [areasLoading, setAreasLoading] = useState(false);
  const [areasError, setAreasError] = useState(false);
  const [areasAttempt, setAreasAttempt] = useState(0);
  const selectedArea = deliveryAreas.find((area) => String(area.id) === deliveryAreaId);

  useEffect(() => {
    let cancelled = false;
    setAreasLoading(true);
    setAreasError(false);
    fetch(`${apiOrigin}/api/restaurant/delivery-areas`, { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) throw new Error("Could not load delivery areas.");
        const result: unknown = await response.json();
        if (!Array.isArray(result) || result.some((area) =>
          !area || typeof area !== "object" ||
          !Number.isInteger((area as DeliveryArea).id) ||
          typeof (area as DeliveryArea).name !== "string" ||
          !Number.isInteger((area as DeliveryArea).deliveryFeePkr) ||
          typeof (area as DeliveryArea).isActive !== "boolean"
        )) {
          throw new Error("Invalid delivery areas response.");
        }
        if (!cancelled) {
          const activeAreas = (result as DeliveryArea[]).filter((area) => area.isActive);
          setDeliveryAreas(activeAreas);
          setDeliveryAreaId((current) =>
            activeAreas.some((area) => String(area.id) === current) ? current : ""
          );
        }
      })
      .catch(() => {
        if (!cancelled) {
          setDeliveryAreas([]);
          setDeliveryAreaId("");
          setAreasError(true);
        }
      })
      .finally(() => {
        if (!cancelled) setAreasLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [areasAttempt]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!cart.items.length) {
      setError("Your cart is empty. Add dishes from the menu first.");
      return;
    }
    if (fulfillmentType === "delivery" && !selectedArea) {
      setError("Choose an available delivery area before submitting your request.");
      return;
    }
    if (fulfillmentType === "delivery" && areasError) {
      setError("We could not load delivery areas. Please try again.");
      return;
    }
    setError("");
    const data: RestaurantOrderInput = {
      name: name.trim(),
      phone: phone.trim(),
      fulfillmentType,
      paymentMethod: "cod",
      deliveryAddress: fulfillmentType === "delivery" ? deliveryAddress.trim() : undefined,
      deliveryAreaId: fulfillmentType === "delivery" ? selectedArea?.id : undefined,
      notes: notes.trim() || null,
      items: cart.items.map(({ id, quantity }) => ({ menuItemId: id, quantity })),
    };
    orderRequest.mutate({ data }, {
      onSuccess(result) {
        setReceipt(result);
        cart.clear();
      },
      onError() {
        setError("We could not submit your order request. Please try again or call the restaurant.");
      },
    });
  }

  if (receipt) {
    return (
      <div className="wrap order-content">
        <section className="receipt order-receipt" role="status" aria-live="polite">
          <div className="receipt-mark"><Check size={20} /></div>
          <h2>Order request received</h2>
          <p>{receipt.message}</p>
          <p>Reference: {receipt.id}</p>
          <p>Food subtotal: PKR {formatPrice(receipt.subtotalPkr)}</p>
          {receipt.deliveryFeePkr !== null && <p>Delivery fee: PKR {formatPrice(receipt.deliveryFeePkr)}</p>}
          {receipt.totalPkr !== null && <p>Request total: PKR {formatPrice(receipt.totalPkr)}</p>}
          <a className="text-link" href="tel:021111111771">Call Saltanat</a>
        </section>
      </div>
    );
  }

  return (
    <section className="page-content order-content">
      <div className="wrap">
        <div className="order-heading">
          <div className="eyebrow">Pickup or delivery</div>
          <h1 className="display">Your order,<br /><em>your way.</em></h1>
          <p>Submit an order request, then call Saltanat to confirm availability. Delivery fees are calculated from the selected service area.</p>
        </div>
        {!cart.items.length ? (
          <div className="empty-panel">
            <h2>Your cart is empty</h2>
            <p>Browse the menu and add a few favourites to get started.</p>
            <a className="button" href="/menu">Browse the menu <ArrowRight size={15} /></a>
          </div>
        ) : (
          <div className="order-layout">
            <section className="form-card cart-card" aria-labelledby="cart-title">
              <h2 id="cart-title">Your dishes</h2>
              <ul className="cart-items">
                {cart.items.map((item) => (
                  <li className="cart-line" key={item.id}>
                    <div className="cart-line-info">
                      <strong>{item.name}</strong>
                      <span>PKR {formatPrice(item.pricePkr)} each</span>
                    </div>
                    <div className="cart-quantity" aria-label={`${item.name} quantity`}>
                      <button type="button" aria-label={`Remove one ${item.name}`} onClick={() => cart.setQuantity(item.id, item.quantity - 1)}><Minus size={15} /></button>
                      <span>{item.quantity}</span>
                      <button type="button" aria-label={`Add one ${item.name}`} onClick={() => cart.setQuantity(item.id, item.quantity + 1)} disabled={item.quantity >= 20}><Plus size={15} /></button>
                    </div>
                    <strong className="cart-line-total">PKR {formatPrice(item.pricePkr * item.quantity)}</strong>
                  </li>
                ))}
              </ul>
              <div className="cart-subtotal"><span>Food subtotal</span><strong>PKR {formatPrice(cart.subtotalPkr)}</strong></div>
              {fulfillmentType === "delivery" && <>
                <div className="cart-subtotal"><span>Delivery fee{selectedArea ? ` · ${selectedArea.name}` : ""}</span><strong>{selectedArea ? `PKR ${formatPrice(selectedArea.deliveryFeePkr)}` : "Choose an area"}</strong></div>
                <div className="cart-subtotal"><span>Estimated total</span><strong>{selectedArea ? `PKR ${formatPrice(cart.subtotalPkr + selectedArea.deliveryFeePkr)}` : "Choose an area"}</strong></div>
              </>}
              <button type="button" className="text-link cart-clear" onClick={cart.clear}><Trash2 size={15} /> Clear cart</button>
            </section>

            <form className="form-card" onSubmit={submit}>
              <h2>Contact and fulfillment</h2>
              <div className="form-grid">
                <div className="field"><label htmlFor="order-name">Your name</label><input id="order-name" autoComplete="name" required minLength={2} maxLength={120} value={name} onChange={(event) => setName(event.target.value)} /></div>
                <div className="field"><label htmlFor="order-phone">Phone number</label><input id="order-phone" type="tel" autoComplete="tel" required minLength={7} maxLength={30} placeholder="e.g. 03xx xxxxxxx" value={phone} onChange={(event) => setPhone(event.target.value)} /></div>
                <fieldset className="field full choice-field">
                  <legend>How would you like your order?</legend>
                  <label className="choice-option"><input type="radio" name="fulfillment" value="pickup" checked={fulfillmentType === "pickup"} onChange={() => setFulfillmentType("pickup")} /> Pickup</label>
                  <label className="choice-option"><input type="radio" name="fulfillment" value="delivery" checked={fulfillmentType === "delivery"} onChange={() => setFulfillmentType("delivery")} /> Delivery</label>
                </fieldset>
                {fulfillmentType === "delivery" && <>
                  <div className="field full"><label htmlFor="order-address">Full delivery address</label><textarea id="order-address" required maxLength={500} autoComplete="street-address" value={deliveryAddress} onChange={(event) => setDeliveryAddress(event.target.value)} placeholder="House/flat, street, block and nearby landmark" /></div>
                  <div className="field full"><label htmlFor="order-area">Delivery area</label>
                    <select id="order-area" required value={deliveryAreaId} onChange={(event) => setDeliveryAreaId(event.target.value)} disabled={areasLoading || areasError || deliveryAreas.length === 0}>
                      <option value="">{areasLoading ? "Loading areas…" : areasError ? "Could not load areas" : deliveryAreas.length ? "Choose your area" : "No delivery areas available"}</option>
                      {deliveryAreas.map((area) => <option key={area.id} value={area.id}>{area.name} — PKR {formatPrice(area.deliveryFeePkr)}</option>)}
                    </select>
                    {areasError && <span role="alert">Delivery areas could not be loaded. <button type="button" className="text-link" onClick={() => setAreasAttempt((attempt) => attempt + 1)}>Try again</button></span>}
                    {!areasLoading && !areasError && deliveryAreas.length === 0 && <span>Call Saltanat to check delivery availability in your area.</span>}
                  </div>
                </>}
                <fieldset className="field full choice-field">
                  <legend>Payment method</legend>
                  <label className="choice-option"><input type="radio" name="payment" checked readOnly /> Cash on delivery / pickup</label>
                  <label className="choice-option choice-disabled"><input type="radio" name="payment" disabled /> Online card payment <span>Not available until a payment gateway is activated</span></label>
                </fieldset>
                <div className="field full"><label htmlFor="order-notes">Order notes <span>(optional)</span></label><textarea id="order-notes" maxLength={1000} value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Anything staff should know about this order" /></div>
              </div>
              {error && <div className="form-error" role="alert">{error}</div>}
              <button className="button form-submit" type="submit" disabled={orderRequest.isPending}>
                {orderRequest.isPending ? <><RotateCw size={15} className="spin" /> Sending order…</> : <>Send order request <ArrowRight size={15} /></>}
              </button>
              <p className="form-fineprint">Your contact details and, if provided, delivery address are shared with Saltanat staff to review and fulfill this request.</p>
              <p className="form-fineprint">This is a request, not a confirmed order. Please call Saltanat to confirm it and, for delivery, the final fee and total.</p>
            </form>
          </div>
        )}
      </div>
    </section>
  );
}
