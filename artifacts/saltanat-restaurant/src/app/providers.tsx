"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { setBaseUrl } from "@workspace/api-client-react";
import { CartProvider } from "@/components/cart";

if (process.env.NEXT_PUBLIC_API_BASE_URL) {
  setBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL);
}

export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(() => new QueryClient({
    defaultOptions: { queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: false } },
  }));
  return <QueryClientProvider client={client}><CartProvider>{children}</CartProvider></QueryClientProvider>;
}