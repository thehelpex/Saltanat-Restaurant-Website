import { createInsertSchema } from "drizzle-zod";
import { date, integer, pgTable, text, timestamp, uuid } from "drizzle-orm/pg-core";
import { z } from "zod/v4";

export const reservationRequestsTable = pgTable("restaurant_reservation_requests", {
  id: uuid("id").defaultRandom().primaryKey(),
  name: text("name").notNull(),
  phone: text("phone").notNull(),
  preferredDate: date("preferred_date", { mode: "string" }).notNull(),
  preferredTime: text("preferred_time").notNull(),
  guestCount: integer("guest_count").notNull(),
  notes: text("notes"),
  status: text("status").notNull().default("awaiting_confirmation"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

export const eventInquiriesTable = pgTable("restaurant_event_inquiries", {
  id: uuid("id").defaultRandom().primaryKey(),
  name: text("name").notNull(),
  phone: text("phone").notNull(),
  email: text("email"),
  eventType: text("event_type").notNull(),
  preferredDate: date("preferred_date", { mode: "string" }),
  guestCount: integer("guest_count").notNull(),
  notes: text("notes"),
  status: text("status").notNull().default("received"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

export const insertReservationRequestSchema = createInsertSchema(reservationRequestsTable).omit({
  id: true,
  createdAt: true,
});

export const insertEventInquirySchema = createInsertSchema(eventInquiriesTable).omit({
  id: true,
  createdAt: true,
});

export type InsertReservationRequest = z.infer<typeof insertReservationRequestSchema>;
export type ReservationRequest = typeof reservationRequestsTable.$inferSelect;
export type InsertEventInquiry = z.infer<typeof insertEventInquirySchema>;
export type EventInquiry = typeof eventInquiriesTable.$inferSelect;