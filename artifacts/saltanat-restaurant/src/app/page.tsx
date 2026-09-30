import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Music2, Sparkles, UsersRound } from "lucide-react";

export const metadata: Metadata = {
  title: "Saltanat Restaurant Karachi | Pakistani BBQ, Karahi & Family Dining",
  description: "Discover Saltanat Restaurant on Stadium Road, Karachi: Pakistani BBQ, karahi and family dining under the stars. Browse the menu or request a table.",
};

const dishes = [
  { name: "Tawa Chicken", note: "From the tawa, made for sharing", image: "/brand/tawa-chicken.jpg", kind: "A Karachi favourite" },
  { name: "Honey Wings", note: "A little sweet, a little fire", image: "/brand/honey-wings.jpg", kind: "From the grill" },
  { name: "Saltanat Burger", note: "A hearty bite for the table", image: "/brand/burger.jpg", kind: "Something different" },
];

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div className="wrap">
          <div className="hero-content">
            <p className="hero-kicker">Saltanat ki shahi kahani</p>
            <h1 className="display">A night out<br /><em>fit for a feast.</em></h1>
            <p className="hero-copy">Karachi evenings, a table set generously, and the lights of the open sky overhead. Come as a family; leave with a story.</p>
            <div className="hero-buttons">
              <Link className="button" href="/book">Request a table <ArrowRight size={15} /></Link>
              <Link className="button button-outline" href="/menu">Explore the menu</Link>
            </div>
          </div>
        </div>
        <span className="hero-note">Stadium Road · Karachi</span>
      </section>

      <div className="ticker" aria-label="Dine-in under the stars">
        <div className="ticker-track"><span>Dine-in under the stars</span><span>Saltanat ki shahi kahani</span><span>Come together, stay awhile</span><span>Dine-in under the stars</span></div>
      </div>

      <section className="section">
        <div className="wrap feature-grid">
          <div className="feature-photo">
            <img src="/brand/banner-03.jpg" alt="A sizzling platter served for the table at Saltanat" />
            <img src="/brand/banner-01.jpg" alt="Open-air dining beneath the evening lights" />
          </div>
          <div className="feature-copy">
            <div className="eyebrow">A table for every story</div>
            <h2 className="display">Come for dinner.<br /><em>Stay for the evening.</em></h2>
            <p>At Saltanat, a meal is bigger than what is on the plate. It is the whole family catching up, a familiar favourite landing hot, and one more reason to linger.</p>
            <p>Settle in beneath the lights on Stadium Road, with Pakistani BBQ and karahi alongside dishes from across the menu.</p>
            <Link className="text-link" href="/about">The Saltanat feeling <ArrowRight size={16} /></Link>
          </div>
        </div>
      </section>

      <section className="section section-dark">
        <div className="wrap">
          <div className="food-heading">
            <div><div className="eyebrow">A few reasons to gather</div><h2 className="display">From the fire,<br /><em>for the table.</em></h2></div>
            <Link className="text-link" href="/menu">See the full menu <ArrowRight size={16} /></Link>
          </div>
          <div className="food-grid">
            {dishes.map((dish) => (
              <article className="food-card" key={dish.name}>
                <img src={dish.image} alt={dish.name} />
                <div className="food-card-copy"><span>{dish.kind}</span><h3>{dish.name}</h3></div>
              </article>
            ))}
          </div>
          <p className="notice" style={{ marginTop: 18 }}>Menu and availability may change. See the current menu for details.</p>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="section-intro">
            <div className="eyebrow">An evening made easy</div>
            <h2 className="display">Room for all<br /><em>your people.</em></h2>
            <p>Bring the little ones, catch a match, enjoy live music or watch the kitchen at work. It is all part of the evening here.</p>
          </div>
          <div className="detail-grid">
            <article className="detail-card"><Music2 /><h3>Live music</h3><p>Live music four nights a week.</p></article>
            <article className="detail-card"><UsersRound /><h3>For families</h3><p>A kids area makes room for the whole family.</p></article>
            <article className="detail-card"><Sparkles /><h3>Open kitchen</h3><p>Watch the action unfold in the open kitchen.</p></article>
            <article className="detail-card"><Sparkles /><h3>Game nights</h3><p>Multiple screens keep you close to the match.</p></article>
          </div>
          <Link className="text-link" href="/about">More about dining at Saltanat <ArrowRight size={16} /></Link>
        </div>
      </section>

      <section className="visit-band">
        <div className="wrap visit-band-inner">
          <div><h2>Your evening is waiting.</h2><p>Plot 118, near Old Drive Inn Cinema, Stadium Road, Karachi</p></div>
          <Link className="button" href="/book">Send a table request <ArrowRight size={15} /></Link>
        </div>
      </section>
    </>
  );
}