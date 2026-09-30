"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import { useState } from "react";

const navItems = [
  { href: "/", label: "Discover" },
  { href: "/menu", label: "Menu" },
  { href: "/about", label: "Our story" },
  { href: "/events", label: "Gatherings" },
  { href: "/contact", label: "Find us" },
];

export function SiteHeader() {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  return (
    <>
      <div className="topline">Stadium Road · Karachi &nbsp; | &nbsp; Dine-in under the stars</div>
      <header className="header">
        <div className="wrap nav-inner">
          <Link className="brand" href="/" aria-label="Saltanat Restaurant home" onClick={() => setOpen(false)}>
            <img src="/brand/logo.png" alt="Saltanat Restaurant" />
          </Link>
          <nav className={`nav-links${open ? " open" : ""}`} aria-label="Main navigation">
            {navItems.map((item) => (
              <Link key={item.href} href={item.href} aria-current={path === item.href ? "page" : undefined} onClick={() => setOpen(false)}>
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="nav-actions">
            <a className="phone-link" href="tel:021111111771">021 111-111-771</a>
            <Link className="button" href="/book">Request a table</Link>
            <button className="menu-toggle" type="button" aria-label={open ? "Close navigation" : "Open navigation"} aria-expanded={open} onClick={() => setOpen(!open)}>
              {open ? <X size={19} /> : <Menu size={19} />}
            </button>
          </div>
        </div>
      </header>
    </>
  );
}