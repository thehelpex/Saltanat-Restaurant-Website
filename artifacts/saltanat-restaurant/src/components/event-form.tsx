"use client";

import { EventInquiryInputEventType, useCreateEventInquiry } from "@workspace/api-client-react";
import type { EventInquiryInput, EventInquiryReceipt } from "@workspace/api-client-react";
import { ArrowRight, Check, RotateCw } from "lucide-react";
import { useState, type FormEvent } from "react";

type EventFields = { name: string; phone: string; email: string; eventType: EventInquiryInput["eventType"]; preferredDate: string; guestCount: string; notes: string };
const defaults: EventFields = { name: "", phone: "", email: "", eventType: EventInquiryInputEventType["family-gathering"], preferredDate: "", guestCount: "20", notes: "" };

export function EventForm() {
  const inquiry = useCreateEventInquiry();
  const [form, setForm] = useState(defaults);
  const [errors, setErrors] = useState<Partial<Record<keyof EventFields, string>>>({});
  const [receipt, setReceipt] = useState<EventInquiryReceipt | null>(null);
  const [apiError, setApiError] = useState("");
  function update(field: keyof EventFields, value: string) { setForm((old) => ({ ...old, [field]: value })); setErrors((old) => ({ ...old, [field]: undefined })); }
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const next: typeof errors = {};
    if (form.name.trim().length < 2 || form.name.trim().length > 120) next.name = "Enter a name between 2 and 120 characters.";
    if (!/^[+]?[\d\s().-]{7,30}$/.test(form.phone.trim())) next.phone = "Enter a valid phone number, including area code.";
    if (form.email && (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email) || form.email.length > 254)) next.email = "Enter a valid email address.";
    const guests = Number(form.guestCount);
    if (!Number.isInteger(guests) || guests < 1 || guests > 500) next.guestCount = "Choose between 1 and 500 guests.";
    if (form.notes.length > 2000) next.notes = "Keep your note under 2,000 characters.";
    setErrors(next);
    if (Object.keys(next).length) return;
    const data: EventInquiryInput = { name: form.name.trim(), phone: form.phone.trim(), email: form.email.trim() || null, eventType: form.eventType, preferredDate: form.preferredDate || null, guestCount: guests, notes: form.notes.trim() || null };
    setApiError("");
    inquiry.mutate({ data }, { onSuccess: (result) => setReceipt(result), onError: () => setApiError("We could not send your enquiry. Please try again or call us at 021 111-111-771.") });
  }
  if (receipt) return <div className="receipt" role="status" aria-live="polite"><div className="receipt-mark"><Check size={20} /></div><h3>Enquiry received</h3><p>{receipt.message}</p><a className="text-link" href="tel:021111111771">Call the restaurant</a><p style={{ marginTop: 12 }}>Reference: {receipt.id}</p><button className="text-link" type="button" onClick={() => { setReceipt(null); setForm(defaults); }}>Send another enquiry <ArrowRight size={15} /></button></div>;
  return (
    <form className="form-card" onSubmit={submit} noValidate>
      <h2>Tell us about your gathering</h2><p>Share a few details, then call Saltanat to discuss your event.</p>
      <div className="form-grid">
        <EventField label="Your name" name="name" value={form.name} error={errors.name} onChange={(value) => update("name", value)} autoComplete="name" />
        <EventField label="Phone number" name="phone" value={form.phone} error={errors.phone} onChange={(value) => update("phone", value)} type="tel" autoComplete="tel" placeholder="e.g. 03xx xxxxxxx" />
        <div className="field"><label htmlFor="event-type">Gathering type</label><select id="event-type" value={form.eventType} onChange={(event) => update("eventType", event.target.value)}><option value="birthday">Birthday</option><option value="corporate">Corporate</option><option value="family-gathering">Family gathering</option><option value="other">Other</option></select></div>
        <EventField label="Guest count" name="guestCount" value={form.guestCount} error={errors.guestCount} onChange={(value) => update("guestCount", value)} type="number" min="1" max="500" />
        <EventField label="Email (optional)" name="email" value={form.email} error={errors.email} onChange={(value) => update("email", value)} type="email" autoComplete="email" />
        <EventField label="Preferred date (optional)" name="preferredDate" value={form.preferredDate} error={errors.preferredDate} onChange={(value) => update("preferredDate", value)} type="date" min={new Date().toISOString().slice(0, 10)} />
        <div className="field full"><label htmlFor="event-notes">A little more about it <span style={{ color: "#8e887a" }}>(optional)</span></label><textarea id="event-notes" maxLength={2000} value={form.notes} onChange={(event) => update("notes", event.target.value)} placeholder="Timing, seating or other details that will help us plan" /></div>
      </div>
      {apiError && <div className="form-error" role="alert">{apiError}</div>}
      <button className="button form-submit" type="submit" disabled={inquiry.isPending}>{inquiry.isPending ? <><RotateCw size={15} /> Sending enquiry…</> : <>Send event enquiry <ArrowRight size={15} /></>}</button>
      <p className="form-fineprint">Sending an enquiry does not confirm an event booking. Please call Saltanat to discuss availability.</p>
    </form>
  );
}

function EventField({ label, name, value, error, onChange, ...props }: { label: string; name: string; value: string; error?: string; onChange: (value: string) => void; type?: string; placeholder?: string; autoComplete?: string; min?: string; max?: string }) {
  const id = `event-${name}`;
  return <div className="field"><label htmlFor={id}>{label}</label><input id={id} name={name} data-testid={`input-event-${name}`} value={value} onChange={(event) => onChange(event.target.value)} aria-invalid={!!error} aria-describedby={error ? `${id}-error` : undefined} {...props} />{error && <span className="field-error" id={`${id}-error`}>{error}</span>}</div>;
}