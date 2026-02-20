"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { AppShellTopNav } from "@/components/layout/app-shell-top-nav";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  useAvailability,
  useCreateEvent,
  useEvents,
  type TimeSlot,
  type CalendarEventItem,
} from "@/hooks/use-calendar";
import {
  Calendar as CalendarIcon,
  Clock,
  Loader2,
  Plus,
  AlertCircle,
  CheckCircle,
} from "lucide-react";
import { toast } from "sonner";
import { PageHeader, SectionCard, StaggerContainer, StaggerItem } from "@/components/layout/dashboard-shell";

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

function SlotCard({ slot }: { slot: TimeSlot }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-green-200 bg-green-50/50 p-3">
      <div className="w-10 h-10 rounded-xl bg-green-500/20 flex items-center justify-center flex-shrink-0">
        <Clock className="size-4 text-green-600" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">
          {formatTime(slot.start)} – {formatTime(slot.end)}
        </p>
        <p className="text-xs text-muted-foreground">
          {slot.duration_minutes} min available
        </p>
      </div>
    </div>
  );
}

export default function CalendarPage() {
  const today = new Date().toISOString().split("T")[0];
  const [dateStart, setDateStart] = useState(today);
  const [dateEnd, setDateEnd] = useState(today);

  const [eventTitle, setEventTitle] = useState("");
  const [eventStart, setEventStart] = useState("");
  const [eventEnd, setEventEnd] = useState("");
  const [eventAttendees, setEventAttendees] = useState("");
  const [eventDescription, setEventDescription] = useState("");

  const startISO = dateStart ? `${dateStart}T00:00:00` : undefined;
  const endISO = dateEnd ? `${dateEnd}T23:59:59` : undefined;

  const { data: availability, isLoading, error } = useAvailability(startISO, endISO);
  const createEvent = useCreateEvent();

  const eventsStartISO = `${today}T00:00:00`;
  const eventsEndDate = new Date(today);
  eventsEndDate.setDate(eventsEndDate.getDate() + 7);
  const eventsEndISO = `${eventsEndDate.toISOString().split("T")[0]}T23:59:59`;

  const { data: events, isLoading: eventsLoading, error: eventsError } = useEvents(eventsStartISO, eventsEndISO);

  const handleCreateEvent = (e: React.FormEvent) => {
    e.preventDefault();

    if (!eventTitle || !eventStart || !eventEnd) {
      toast.error("Please fill in title, start, and end time");
      return;
    }

    createEvent.mutate(
      {
        title: eventTitle,
        start: eventStart,
        end: eventEnd,
        attendees: eventAttendees
          ? eventAttendees.split(",").map((a) => a.trim())
          : [],
        description: eventDescription || undefined,
      },
      {
        onSuccess: (data) => {
          toast.success(`Event "${data.title}" created successfully`);
          setEventTitle("");
          setEventStart("");
          setEventEnd("");
          setEventAttendees("");
          setEventDescription("");
        },
        onError: (err: any) => {
          const detail = err?.response?.data?.detail;
          toast.error(
            detail || "Failed to create event. Make sure Gmail is connected."
          );
        },
      }
    );
  };

  return (
    <AppShellTopNav>
      <StaggerContainer className="space-y-6">
          {/* Header */}
          <StaggerItem>
            <PageHeader
              icon={<CalendarIcon className="w-6 h-6 text-amber-600" />}
              iconColor="bg-amber-500/10"
              title="Calendar"
              subtitle="Check availability and create calendar events"
            />
          </StaggerItem>

          {/* Main Grid */}
          <StaggerItem>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Availability Check */}
              <SectionCard>
                <div className="p-5">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="w-10 h-10 rounded-xl bg-green-500/10 flex items-center justify-center">
                      <Clock className="w-5 h-5 text-green-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold">Check Availability</h3>
                      <p className="text-xs text-muted-foreground">Find free time slots</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <Label htmlFor="avail-start" className="text-xs text-muted-foreground">From</Label>
                      <Input
                        id="avail-start"
                        type="date"
                        value={dateStart}
                        onChange={(e) => setDateStart(e.target.value)}
                        className="mt-1.5 h-11 bg-white/70 border-white/50"
                      />
                    </div>
                    <div>
                      <Label htmlFor="avail-end" className="text-xs text-muted-foreground">To</Label>
                      <Input
                        id="avail-end"
                        type="date"
                        value={dateEnd}
                        onChange={(e) => setDateEnd(e.target.value)}
                        className="mt-1.5 h-11 bg-white/70 border-white/50"
                      />
                    </div>
                  </div>

                  {isLoading && (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="size-6 animate-spin text-muted-foreground" />
                    </div>
                  )}

                  {error && (
                    <div className="flex items-center gap-2 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-600">
                      <AlertCircle className="size-4 shrink-0" />
                      {(() => {
                        const axiosErr = error as any;
                        const detail = axiosErr?.response?.data?.detail;
                        if (detail) return detail;
                        if (error instanceof Error) return error.message;
                        return "Failed to check availability.";
                      })()}
                    </div>
                  )}

                  {availability && !isLoading && (
                    <div className="space-y-3">
                      <p className="text-sm font-medium">
                        Free slots on {formatDate(availability.checked_range_start)}
                        {availability.checked_range_start !== availability.checked_range_end &&
                          ` – ${formatDate(availability.checked_range_end)}`}
                      </p>
                      {availability.free_slots.length === 0 ? (
                        <p className="text-sm text-muted-foreground py-4 text-center bg-muted/30 rounded-lg">
                          No free slots found in this range.
                        </p>
                      ) : (
                        <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                          {availability.free_slots.map((slot, i) => (
                            <SlotCard key={i} slot={slot} />
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </SectionCard>

              {/* Create Event */}
              <SectionCard>
                <div className="p-5">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
                      <Plus className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold">Create Event</h3>
                      <p className="text-xs text-muted-foreground">Schedule a new meeting</p>
                    </div>
                  </div>

                  <form onSubmit={handleCreateEvent} className="space-y-4">
                    <div>
                      <Label htmlFor="event-title" className="text-xs text-muted-foreground">Title</Label>
                      <Input
                        id="event-title"
                        placeholder="Meeting title"
                        value={eventTitle}
                        onChange={(e) => setEventTitle(e.target.value)}
                        className="mt-1.5 h-11 bg-white/70 border-white/50"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="event-start" className="text-xs text-muted-foreground">Start</Label>
                        <Input
                          id="event-start"
                          type="datetime-local"
                          value={eventStart}
                          onChange={(e) => setEventStart(e.target.value)}
                          className="mt-1.5 h-11 bg-white/70 border-white/50"
                        />
                      </div>
                      <div>
                        <Label htmlFor="event-end" className="text-xs text-muted-foreground">End</Label>
                        <Input
                          id="event-end"
                          type="datetime-local"
                          value={eventEnd}
                          onChange={(e) => setEventEnd(e.target.value)}
                          className="mt-1.5 h-11 bg-white/70 border-white/50"
                        />
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="event-attendees" className="text-xs text-muted-foreground">
                        Attendees <span className="text-muted-foreground">(comma-separated)</span>
                      </Label>
                      <Input
                        id="event-attendees"
                        placeholder="alice@example.com, bob@example.com"
                        value={eventAttendees}
                        onChange={(e) => setEventAttendees(e.target.value)}
                        className="mt-1.5 h-11 bg-white/70 border-white/50"
                      />
                    </div>

                    <div>
                      <Label htmlFor="event-desc" className="text-xs text-muted-foreground">Description</Label>
                      <Input
                        id="event-desc"
                        placeholder="Optional description"
                        value={eventDescription}
                        onChange={(e) => setEventDescription(e.target.value)}
                        className="mt-1.5 h-11 bg-white/70 border-white/50"
                      />
                    </div>

                    <Button
                      type="submit"
                      className="w-full h-11 bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-700 hover:to-violet-700"
                      disabled={createEvent.isPending}
                    >
                      {createEvent.isPending ? (
                        <>
                          <Loader2 className="animate-spin mr-2" />
                          Creating...
                        </>
                      ) : (
                        <>
                          <CheckCircle className="size-4 mr-2" />
                          Create Event
                        </>
                      )}
                    </Button>
                  </form>
                </div>
              </SectionCard>
            </div>
          </StaggerItem>

          {/* Upcoming Events */}
          <StaggerItem>
            <SectionCard>
              <div className="p-5">
                <div className="flex items-center gap-3 mb-5">
                  <div className="w-10 h-10 rounded-xl bg-violet-500/10 flex items-center justify-center">
                    <CalendarIcon className="w-5 h-5 text-violet-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Upcoming Events</h3>
                    <p className="text-xs text-muted-foreground">Next 7 days</p>
                  </div>
                </div>

                {eventsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="size-6 animate-spin text-muted-foreground" />
                  </div>
                ) : eventsError ? (
                  <div className="flex items-center gap-2 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-600">
                    <AlertCircle className="size-4 shrink-0" />
                    Failed to load events.
                  </div>
                ) : events && events.length > 0 ? (
                  <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                    {events.map((event: CalendarEventItem) => (
                      <div
                        key={event.id}
                        className="flex items-center gap-3 rounded-xl border p-3 hover:bg-violet-50/50 transition-colors"
                      >
                        <div className="w-10 h-10 rounded-xl bg-violet-500/10 flex items-center justify-center flex-shrink-0">
                          <CalendarIcon className="size-4 text-violet-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium">{event.title}</p>
                          <p className="text-xs text-muted-foreground">
                            {formatTime(event.start)} – {formatTime(event.end)}
                            {" · "}
                            {formatDate(event.start)}
                          </p>
                          {event.attendees.length > 0 && (
                            <p className="text-xs text-muted-foreground truncate">
                              {event.attendees.join(", ")}
                            </p>
                          )}
                        </div>
                        {event.html_link && (
                          <a
                            href={event.html_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-violet-600 hover:underline shrink-0 font-medium"
                          >
                            Open
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground py-8 text-center bg-muted/20 rounded-xl">
                    No upcoming events found.
                  </p>
                )}
              </div>
            </SectionCard>
          </StaggerItem>
      </StaggerContainer>
    </AppShellTopNav>
  );
}
