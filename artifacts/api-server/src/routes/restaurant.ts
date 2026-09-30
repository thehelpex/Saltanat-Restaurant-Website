import { Router, type IRouter } from "express";
import { db, eventInquiriesTable, reservationRequestsTable } from "@workspace/db";
import {
  CreateEventInquiryBody,
  CreateEventInquiryResponse,
  CreateReservationRequestBody,
  CreateReservationRequestResponse,
  ListRestaurantMenuQueryParams,
  ListRestaurantMenuResponse,
} from "@workspace/api-zod";
import { restaurantMenu } from "../lib/menu-data";

const router: IRouter = Router();

router.get("/restaurant/menu", (req, res): void => {
  const parsed = ListRestaurantMenuQueryParams.safeParse(req.query);
  if (!parsed.success) {
    res.status(400).json({ error: "Invalid menu filters." });
    return;
  }

  const category = parsed.data.category?.trim().toLocaleLowerCase();
  const search = parsed.data.search?.trim().toLocaleLowerCase();
  const filtered = restaurantMenu.filter((item) => {
    const matchesCategory =
      !category || category === "all" || item.category.toLocaleLowerCase() === category;
    const matchesSearch =
      !search ||
      `${item.name} ${item.category} ${item.description ?? ""}`
        .toLocaleLowerCase()
        .includes(search);
    return matchesCategory && matchesSearch;
  });

  res.json(ListRestaurantMenuResponse.parse(filtered));
});

router.post("/restaurant/reservations", async (req, res): Promise<void> => {
  const parsed = CreateReservationRequestBody.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: "Please check the reservation details and try again." });
    return;
  }

  const name = parsed.data.name.trim();
  const phone = parsed.data.phone.trim();
  if (name.length < 2 || phone.replace(/\D/g, "").length < 7) {
    res.status(400).json({ error: "Please enter a valid name and phone number." });
    return;
  }

  const [reservation] = await db
    .insert(reservationRequestsTable)
    .values({
      ...parsed.data,
      name,
      phone,
      notes: parsed.data.notes?.trim() || null,
      status: "awaiting_confirmation",
    })
    .returning({ id: reservationRequestsTable.id });

  res.status(201).json(
    CreateReservationRequestResponse.parse({
      id: reservation.id,
      status: "awaiting_confirmation",
      message: "Your request has been received. Saltanat will contact you to confirm availability.",
    }),
  );
});

router.post("/restaurant/event-inquiries", async (req, res): Promise<void> => {
  const parsed = CreateEventInquiryBody.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: "Please check the event details and try again." });
    return;
  }

  const name = parsed.data.name.trim();
  const phone = parsed.data.phone.trim();
  const email = parsed.data.email?.trim() || null;
  if (name.length < 2 || phone.replace(/\D/g, "").length < 7) {
    res.status(400).json({ error: "Please enter a valid name and phone number." });
    return;
  }
  if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    res.status(400).json({ error: "Please enter a valid email address." });
    return;
  }

  const [inquiry] = await db
    .insert(eventInquiriesTable)
    .values({
      ...parsed.data,
      name,
      phone,
      email,
      notes: parsed.data.notes?.trim() || null,
      status: "received",
    })
    .returning({ id: eventInquiriesTable.id });

  res.status(201).json(
    CreateEventInquiryResponse.parse({
      id: inquiry.id,
      status: "received",
      message: "Your event inquiry has been received. Saltanat will contact you to discuss the details.",
    }),
  );
});

export default router;