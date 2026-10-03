import type { Metadata } from "next";
import { OrderCheckout } from "@/components/order-checkout";

export const metadata: Metadata = {
  title: "Order Online | Saltanat Restaurant Karachi",
  description: "Request pickup or delivery from Saltanat Restaurant in Karachi. Staff confirm order availability and delivery details.",
};

export default function OrderPage() {
  return <OrderCheckout />;
}
