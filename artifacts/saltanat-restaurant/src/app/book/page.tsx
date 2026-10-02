import type { Metadata } from "next";
import { Phone } from "lucide-react";
import { PageHero } from "@/components/page-hero";
import { VisitForm } from "@/components/visit-form";

export const metadata: Metadata = {
  title: "Request a Table | Saltanat Restaurant Karachi",
  description: "Send a table request to Saltanat Restaurant on Stadium Road, Karachi. Requests are subject to staff confirmation.",
};

export default function BookPage() {
  return <>
    <PageHero eyebrow="Make an evening of it" title={<>Your table,<br /><em>your people.</em></>} copy="Share your preferred date and time. Call the restaurant to confirm availability before your visit." />
    <section className="page-content"><div className="wrap form-layout">
      <aside className="form-aside"><div className="eyebrow">A note before you send</div><h2 className="display">Let us set<br /><em>the table.</em></h2><p>Tell us how many are joining and when you would like to visit. Call us to confirm availability.</p><div className="aside-note">A request is not a confirmed reservation. For a same-evening enquiry, call us directly at <a href="tel:021111111771">021 111-111-771</a>.</div><a className="text-link" href="tel:021111111771"><Phone size={15} /> Call the restaurant</a></aside>
      <VisitForm />
    </div></section>
  </>;
}