"use client";

import type { MenuItem } from "@workspace/api-client-react";
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type CartItem = MenuItem & { quantity: number };

type CartValue = {
  items: CartItem[];
  itemCount: number;
  subtotalPkr: number;
  addItem: (item: MenuItem) => void;
  setQuantity: (id: number, quantity: number) => void;
  clear: () => void;
};

const STORAGE_KEY = "saltanat-order-cart";
const CartContext = createContext<CartValue | null>(null);

function isCartItem(value: unknown): value is CartItem {
  if (!value || typeof value !== "object") return false;
  const item = value as Record<string, unknown>;
  return (
    Number.isInteger(item.id) &&
    typeof item.name === "string" &&
    typeof item.category === "string" &&
    (typeof item.description === "string" || item.description === null) &&
    Number.isInteger(item.pricePkr) &&
    (typeof item.imageUrl === "string" || item.imageUrl === null) &&
    typeof item.isFeatured === "boolean" &&
    Number.isInteger(item.quantity) &&
    Number(item.quantity) > 0 &&
    Number(item.quantity) <= 20
  );
}

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItem[]>([]);
  const [restored, setRestored] = useState(false);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed: unknown = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.every(isCartItem)) {
          setItems(parsed);
        } else {
          console.error("The saved order cart has an invalid format and was ignored.");
        }
      }
    } catch (error) {
      console.error("Unable to restore the saved order cart.", error);
    } finally {
      setRestored(true);
    }
  }, []);

  useEffect(() => {
    if (!restored) return;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    } catch (error) {
      console.error("Unable to save the order cart.", error);
    }
  }, [items, restored]);

  const value = useMemo<CartValue>(() => ({
    items,
    itemCount: items.reduce((total, item) => total + item.quantity, 0),
    subtotalPkr: items.reduce((total, item) => total + item.pricePkr * item.quantity, 0),
    addItem(item) {
      setItems((current) => {
        const existing = current.find((entry) => entry.id === item.id);
        if (existing) {
          return current.map((entry) =>
            entry.id === item.id
              ? { ...entry, quantity: Math.min(20, entry.quantity + 1) }
              : entry,
          );
        }
        return [...current, { ...item, quantity: 1 }];
      });
    },
    setQuantity(id, quantity) {
      setItems((current) =>
        quantity <= 0
          ? current.filter((item) => item.id !== id)
          : current.map((item) =>
              item.id === id ? { ...item, quantity: Math.min(20, quantity) } : item,
            ),
      );
    },
    clear() {
      setItems([]);
    },
  }), [items]);

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const cart = useContext(CartContext);
  if (!cart) throw new Error("useCart must be used within CartProvider.");
  return cart;
}
