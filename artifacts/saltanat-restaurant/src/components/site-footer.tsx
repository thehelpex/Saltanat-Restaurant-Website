"use client";

import Link from "next/link";
import { ArrowUpRight, MapPin } from "lucide-react";
import { getHealthCheckQueryKey, useHealthCheck } from "@workspace/api-client-react";

export function SiteFooter() {
  const health = useHealthCheck({ query: { queryKey: getHealthCheckQueryKey(), refetchInterval: 60_000, retry: 1 } });
  const online = health.data?.status?.toLowerCase() === "ok" || health.data?.status?.toLowerCase() === "healthy";
  return (
    <footer className="footer">
      <div className="wrap">
        <div className="footer-grid">
          <div>
            <img className="footer-logo" src="/brand/logo.png" alt="Saltanat Restaurant" />
            <p>A royal story told over a generous table. Find us on Stadium Road, Karachi.</p>
          </div>
          <div className="footer-col">
            <h3>Explore</h3>
            <Link href="/menu">The menu</Link><Link href="/about">Our story</Link><Link href="/events">Private gatherings</Link><Link href="/book">Request a table</Link>
          </div>
          <div className="footer-col">
            <h3>Visit</h3>
            <a href="https://maps.google.com/?q=Saltanat+Restaurant+Stadium+Road+Karachi" target="_blank" rel="noreferrer">Plot 118, near Old Drive Inn Cinema, Stadium Road</a>
            <a href="tel:021111111771">021 111-111-771</a><a href="mailto:order@saltanatrestaurant.com">order@saltanatrestaurant.com</a>
          </div>
          <div className="footer-col">
            <h3>Evenings</h3>
            <p>Mon–Fri · 6:30 PM–1:00 AM<br />Sat–Sun · 6:30 PM–1:30 AM</p>
            <Link href="/contact">Plan your visit <ArrowUpRight size={13} /></Link>
          </div>
        </div>
        <div className="footer-bottom">
          <span>© {new Date().getFullYear()} Saltanat Restaurant. Hours and availability can change.</span>
          <span className="health" aria-live="polite">
            <span className={`health-dot${health.isError ? " down" : ""}`} />
            {health.isLoading ? "Checking service" : health.isError ? "Service status unavailable" : online ? "Online enquiries available" : "Enquiry service ready"}
            <MapPin size={12} aria-hidden="true" />
          </span>
        </div>
      </div>
    </footer>
  );
}