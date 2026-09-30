import type { Metadata } from "next";
import Link from "next/link";
import { Clock3, Mail, MapPin, Phone, ArrowUpRight } from "lucide-react";
import { PageHero } from "@/components/page-hero";

export const metadata: Metadata = {
  title: "Contact & Directions | Saltanat Restaurant Stadium Road Karachi",
  description: "Find Saltanat Restaurant at Plot 118, near Old Drive Inn Cinema, Stadium Road, Karachi. See opening hours, phone and directions.",
};

export default function ContactPage() {
  return <>
    <PageHero eyebrow="Find your way to us" title={<>Meet us<br /><em>on Stadium Road.</em></>} copy="A lively family restaurant in Karachi, with dinner under the stars. We look forward to welcoming you." />
    <section className="page-content"><div className="wrap contact-grid">
      <div className="contact-stack">
        <article className="contact-card"><div className="contact-card-head"><MapPin size={19} /><h2>Come by</h2></div><p>Plot 118, near Old Drive Inn Cinema,<br />Stadium Road, Karachi</p><a className="inline-link" href="https://maps.google.com/?q=Saltanat+Restaurant+Plot+118+Stadium+Road+Karachi" target="_blank" rel="noreferrer">Get directions <ArrowUpRight size={13} /></a></article>
        <article className="contact-card"><div className="contact-card-head"><Clock3 size={19} /><h2>Evening hours</h2></div><p>Monday–Friday · 6:30 PM–1:00 AM<br />Saturday–Sunday · 6:30 PM–1:30 AM</p><p className="notice">Hours and availability can change. Please call ahead for the latest information.</p></article>
        <article className="contact-card"><div className="contact-card-head"><Phone size={19} /><h2>Call the restaurant</h2></div><a className="inline-link" href="tel:021111111771">021 111-111-771</a></article>
        <article className="contact-card"><div className="contact-card-head"><Mail size={19} /><h2>Write to us</h2></div><a className="inline-link" href="mailto:order@saltanatrestaurant.com">order@saltanatrestaurant.com</a></article>
      </div>
      <div className="map-panel"><div className="eyebrow">Stadium Road · Karachi</div><h2>See you<br />under the stars.</h2><p>Find Saltanat near Old Drive Inn Cinema. Get directions before you set off.</p><a className="button" href="https://maps.google.com/?q=Saltanat+Restaurant+Plot+118+Stadium+Road+Karachi" target="_blank" rel="noreferrer">Open directions <ArrowUpRight size={15} /></a></div>
    </div>
      <div className="wrap" style={{ marginTop: 42, display: "flex", flexWrap: "wrap", gap: 15 }}><Link className="text-link" href="/book">Request a table <ArrowUpRight size={15} /></Link><Link className="text-link" href="/events">Ask about a gathering <ArrowUpRight size={15} /></Link></div>
    </section>
  </>;
}