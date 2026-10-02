import type { Metadata } from "next";
import { PageHero } from "@/components/page-hero";
import { EventForm } from "@/components/event-form";

export const metadata: Metadata = {
  title: "Private Events & Gatherings | Saltanat Restaurant Karachi",
  description: "Enquire about birthdays, corporate dinners and family gatherings at Saltanat Restaurant, Stadium Road Karachi.",
};

export default function EventsPage() {
  return <>
    <PageHero eyebrow="Bring everyone together" title={<>Make it a<br /><em>Saltanat evening.</em></>} copy="Planning a birthday, family gathering or corporate dinner? Share your plans and call us to discuss availability." />
    <section className="page-content"><div className="wrap form-layout">
      <aside className="form-aside"><div className="eyebrow">Gather around</div><h2 className="display">Good nights<br /><em>are shared.</em></h2><p>With open-air dining, live music four nights a week, a kids area and a wide-ranging menu, Saltanat makes a lively setting for getting together.</p><div className="aside-note">Share your occasion, guest count and preferred date. Call Saltanat to discuss availability and arrangements.</div></aside>
      <EventForm />
    </div></section>
  </>;
}