import type { Metadata } from "next";
import { ManagerConsole } from "@/components/manager-console";

export const metadata: Metadata = {
  title: "Manager | Saltanat Restaurant",
  robots: { index: false, follow: false },
};

export default function ManagerPage() {
  return <ManagerConsole />;
}
