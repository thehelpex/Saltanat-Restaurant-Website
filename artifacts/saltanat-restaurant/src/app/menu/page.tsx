import type { Metadata } from "next";
import { MenuBrowser } from "@/components/menu-browser";
import { PageHero } from "@/components/page-hero";

export const metadata: Metadata = {
  title: "Menu | BBQ, Karahi & More on Stadium Road",
  description: "Browse Saltanat Restaurant's current menu in Karachi, from BBQ, karahi and handi to seafood, Chinese, steaks, burgers, drinks and family platters.",
};

export default function MenuPage() {
  return <><PageHero eyebrow="Something for every appetite" title={<>The menu<br /><em>at Saltanat.</em></>} copy="Gather around Pakistani BBQ and karahi, or find a familiar favourite from across our wide-ranging menu." /><MenuBrowser /></>;
}