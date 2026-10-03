import type { Metadata } from "next";
import { StaffOrders } from "@/components/staff-orders";

export const metadata: Metadata = {
  title: "Staff Orders | Saltanat Restaurant",
  robots: { index: false, follow: false },
};

export default function StaffOrdersPage() {
  return <StaffOrders />;
}
