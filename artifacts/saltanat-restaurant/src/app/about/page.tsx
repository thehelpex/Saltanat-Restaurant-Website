import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Baby, MonitorPlay, Music2, Utensils } from "lucide-react";
import { PageHero } from "@/components/page-hero";

export const metadata: Metadata = {
  title: "Our Story | Saltanat Restaurant Karachi",
  description: "Discover Saltanat ki shahi kahani: family connection, warm service, an open kitchen and dining under the stars on Stadium Road, Karachi.",
};

export default function AboutPage() {
  return (
    <>
      <PageHero eyebrow="Saltanat ki shahi kahani" title={<>A little more<br /><em>than a meal.</em></>} copy="A welcoming evening on Stadium Road, built around good food, warm service and the people around your table." />
      <section className="page-content">
        <div className="wrap">
          <div className="two-col">
            <div className="story-copy">
              <div className="eyebrow">The Saltanat feeling</div>
              <h2 className="display">A generous table.<br /><em>A shared moment.</em></h2>
              <p>Saltanat ki shahi kahani is a story told in the way a table comes together: with care in the ingredients, consistency in the kitchen and warmth in the welcome.</p>
              <p>From Pakistani BBQ and karahi to dishes from across the menu, the invitation is simple: bring your family, make yourself at home, and enjoy the evening under the stars.</p>
              <p>We believe in family connection, community impact, respect and joy—values that make every guest part of the gathering.</p>
              <Link className="text-link" href="/book">Plan your visit <ArrowRight size={16} /></Link>
            </div>
            <div className="story-photo"><img src="/brand/banner-01.jpg" alt="Saltanat's open-air dining area lit for an evening under the stars" /></div>
          </div>
          <div className="values">
            <div className="value"><strong>Premium</strong><span>Ingredients chosen with care</span></div>
            <div className="value"><strong>Consistent</strong><span>Quality across every visit</span></div>
            <div className="value"><strong>Warm</strong><span>Service with genuine welcome</span></div>
            <div className="value"><strong>Together</strong><span>Family, community and joy</span></div>
          </div>
        </div>
      </section>
      <section className="section section-dark">
        <div className="wrap">
          <div className="section-intro"><div className="eyebrow">A lively evening, your way</div><h2 className="display">Made for the<br /><em>whole family.</em></h2><p>Whether it is the match, the music, or keeping little hands busy, there is more than one way to enjoy the night.</p></div>
          <div className="detail-grid">
            <article className="detail-card"><Music2 /><h3>Live music</h3><p>Live music four nights a week.</p></article>
            <article className="detail-card"><Baby /><h3>Kids area</h3><p>A dedicated kids area for family visits.</p></article>
            <article className="detail-card"><MonitorPlay /><h3>Multiple screens</h3><p>Stay close to the action over dinner.</p></article>
            <article className="detail-card"><Utensils /><h3>Open kitchen</h3><p>A view into the kitchen at work.</p></article>
          </div>
        </div>
      </section>
    </>
  );
}