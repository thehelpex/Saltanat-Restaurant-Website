import type { ReactNode } from "react";

export function PageHero({ eyebrow, title, copy }: { eyebrow: string; title: ReactNode; copy: string }) {
  return (
    <section className="page-hero">
      <div className="wrap motion-in">
        <div className="eyebrow">{eyebrow}</div>
        <h1 className="display">{title}</h1>
        <p>{copy}</p>
      </div>
    </section>
  );
}