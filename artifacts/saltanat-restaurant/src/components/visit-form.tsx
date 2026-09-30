"use client";

import { useCreateReservationRequest } from "@workspace/api-client-react";
import type { ReservationInput, ReservationReceipt } from "@workspace/api-client-react";
import { ArrowRight, Check, RotateCw } from "lucide-react";
import { useState, type FormEvent } from "react";

type Fields = { name: string; phone: string; preferredDate: string; preferredTime: string; guestCount: string; notes: string };
const initial: Fields = { name: "", phone: "", preferredDate: "", preferredTime: "", guestCount: "2", notes: "" };

export function VisitForm() {
  const request = useCreateReservationRequest();
  const [fields, setFields] = useState(initial);
  const [errors, setErrors] = useState<Partial<Record<keyof Fields, string>>>({});
  const [receipt, setReceipt] = useState<ReservationReceipt | null>(null);
  const [apiError, setApiError] = useState("");
  function update(field: keyof Fields, value: string) { setFields((old) => ({ ...old, [field]: value })); setErrors((old) => ({ ...old, [field]: undefined })); }
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const next: typeof errors = {};
    if (fields.name.trim().length < 2 || fields.name.trim().length > 120) next.name = "Enter a name between 2 and 120 characters.";
    if (!/^[+]?[\d\s().-]{7,30}$/.test(fields.phone.trim())) next.phone = "Enter a valid phone number, including area code.";
    if (!fields.preferredDate) next.preferredDate = "Choose your preferred date.";
    if (!fields.preferredTime) next.preferredTime = "Choose your preferred time.";
    const guests = Number(fields.guestCount);
    if (!Number.isInteger(guests) || guests < 1 || guests > 50) next.guestCount = "Choose between 1 and 50 guests.";
    setErrors(next);
    if (Object.keys(next).length) return;
    const data: ReservationInput = {
      name: fields.name.trim(), phone: fields.phone.trim(), preferredDate: fields.preferredDate,
      preferredTime: fields.preferredTime, guestCount: guests, notes: fields.notes.trim() || null,
    };
    setApiError("");
    request.mutate({ data }, { onSuccess: (result) => setReceipt(result), onError: () => setApiError("Your request could not be sent. Please try again, or call us at 021 111-111-771.") });
  }
  if (receipt) return <div className="receipt" role="status" aria-live="polite"><div className="receipt-mark"><Check size={20} /></div><h3>Request received</h3><p>{receipt.message} Your table request is awaiting staff confirmation. We will be in touch using the details you provided.</p><p style={{ marginTop: 12 }}>Reference: {receipt.id}</p><button className="text-link" type="button" onClick={() => { setReceipt(null); setFields(initial); }}>Make another request <ArrowRight size={15} /></button></div>;
  return (
    <form className="form-card" onSubmit={submit} noValidate>
      <h2>Tell us when you are coming</h2><p>Send a table request and our team will follow up to confirm availability.</p>
      <div className="form-grid">
        <Field label="Your name" name="name" value={fields.name} error={errors.name} onChange={(value) => update("name", value)} autoComplete="name" />
        <Field label="Phone number" name="phone" value={fields.phone} error={errors.phone} onChange={(value) => update("phone", value)} autoComplete="tel" type="tel" placeholder="e.g. 03xx xxxxxxx" />
        <Field label="Preferred date" name="preferredDate" value={fields.preferredDate} error={errors.preferredDate} onChange={(value) => update("preferredDate", value)} type="date" min={new Date().toISOString().slice(0, 10)} />
        <Field label="Preferred time" name="preferredTime" value={fields.preferredTime} error={errors.preferredTime} onChange={(value) => update("preferredTime", value)} type="time" />
        <Field label="Guests" name="guestCount" value={fields.guestCount} error={errors.guestCount} onChange={(value) => update("guestCount", value)} type="number" min="1" max="50" />
        <div className="field full"><label htmlFor="reservation-notes">Anything we should know? <span style={{ color: "#8e887a" }}>(optional)</span></label><textarea id="reservation-notes" maxLength={1000} value={fields.notes} onChange={(event) => update("notes", event.target.value)} placeholder="A special occasion, seating preference or other note" /></div>
      </div>
      {apiError && <div className="form-error" role="alert">{apiError}</div>}
      <button className="button form-submit" type="submit" disabled={request.isPending}>{request.isPending ? <><RotateCw size={15} className="spin" /> Sending request…</> : <>Send table request <ArrowRight size={15} /></>}</button>
      <p className="form-fineprint">This is a request, not a confirmed reservation. Our team will contact you about availability.</p>
    </form>
  );
}

function Field({ label, name, value, error, onChange, ...props }: { label: string; name: string; value: string; error?: string; onChange: (value: string) => void; type?: string; placeholder?: string; autoComplete?: string; min?: string; max?: string }) {
  const id = `reservation-${name}`;
  return <div className="field"><label htmlFor={id}>{label}</label><input id={id} name={name} data-testid={`input-${name}`} value={value} onChange={(event) => onChange(event.target.value)} aria-invalid={!!error} aria-describedby={error ? `${id}-error` : undefined} {...props} />{error && <span className="field-error" id={`${id}-error`}>{error}</span>}</div>;
}