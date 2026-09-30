import Link from "next/link";

export default function NotFound() {
  return <section className="page-hero"><div className="wrap"><div className="eyebrow">A wrong turn</div><h1 className="display">This page<br /><em>isn't on the menu.</em></h1><p>Head back to the table and find your way around Saltanat.</p><Link className="button" href="/">Back to Saltanat</Link></div></section>;
}