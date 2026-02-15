"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  useAvailability,
  useCreateEvent,
  type TimeSlot,
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
    <div className="flex items-center gap-3 rounded-lg border p-3 bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800">
      <Clock className="size-4 text-green-600 dark:text-green-400 shrink-0" />
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

  // Create event form
  const [eventTitle, setEventTitle] = useState("");
  const [eventStart, setEventStart] = useState("");
  const [eventEnd, setEventEnd] = useState("");
  const [eventAttendees, setEventAttendees] = useState("");
  const [eventDescription, setEventDescription] = useState("");

  const startISO = dateStart ? `${dateStart}T00:00:00` : undefined;
  const endISO = dateEnd ? `${dateEnd}T23:59:59` : undefined;

  const { data: availability, isLoading, error } = useAvailability(startISO, endISO);
  const createEvent = useCreateEvent();

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
          toast.error(
            err.response?.data?.detail ||
              "Failed to create event. Make sure Gmail is connected."
          );
        },
      }
    );
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Calendar</h1>
          <p className="text-muted-foreground mt-1">
            Check availability and create calendar events
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Availability Check */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CalendarIcon className="size-5" />
                Check Availability
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="avail-start">From</Label>
                  <Input
                    id="avail-start"
                    type="date"
                    value={dateStart}
                    onChange={(e) => setDateStart(e.target.value)}
                    className="mt-1.5"
                  />
                </div>
                <div>
                  <Label htmlFor="avail-end">To</Label>
                  <Input
                    id="avail-end"
                    type="date"
                    value={dateEnd}
                    onChange={(e) => setDateEnd(e.target.value)}
                    className="mt-1.5"
                  />
                </div>
              </div>

              {isLoading && (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="size-6 animate-spin text-muted-foreground" />
                </div>
              )}

              {error && (
                <div className="flex items-center gap-2 rounded-md bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
                  <AlertCircle className="size-4 shrink-0" />
                  {error instanceof Error
                    ? error.message
                    : "Failed to check availability. Make sure Gmail is connected."}
                </div>
              )}

              {availability && !isLoading && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">
                    Free slots on {formatDate(availability.checked_range_start)}
                    {availability.checked_range_start !==
                      availability.checked_range_end &&
                      ` – ${formatDate(availability.checked_range_end)}`}
                  </p>
                  {availability.free_slots.length === 0 ? (
                    <p className="text-sm text-muted-foreground py-4 text-center">
                      No free slots found in this range.
                    </p>
                  ) : (
                    <div className="space-y-2 max-h-[400px] overflow-y-auto">
                      {availability.free_slots.map((slot, i) => (
                        <SlotCard key={i} slot={slot} />
                      ))}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Create Event */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Plus className="size-5" />
                Create Event
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateEvent} className="space-y-4">
                <div>
                  <Label htmlFor="event-title">Title</Label>
                  <Input
                    id="event-title"
                    placeholder="Meeting title"
                    value={eventTitle}
                    onChange={(e) => setEventTitle(e.target.value)}
                    className="mt-1.5"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="event-start">Start</Label>
                    <Input
                      id="event-start"
                      type="datetime-local"
                      value={eventStart}
                      onChange={(e) => setEventStart(e.target.value)}
                      className="mt-1.5"
                    />
                  </div>
                  <div>
                    <Label htmlFor="event-end">End</Label>
                    <Input
                      id="event-end"
                      type="datetime-local"
                      value={eventEnd}
                      onChange={(e) => setEventEnd(e.target.value)}
                      className="mt-1.5"
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="event-attendees">
                    Attendees{" "}
                    <span className="text-muted-foreground font-normal">
                      (comma-separated)
                    </span>
                  </Label>
                  <Input
                    id="event-attendees"
                    placeholder="alice@example.com, bob@example.com"
                    value={eventAttendees}
                    onChange={(e) => setEventAttendees(e.target.value)}
                    className="mt-1.5"
                  />
                </div>

                <div>
                  <Label htmlFor="event-desc">Description</Label>
                  <Input
                    id="event-desc"
                    placeholder="Optional description"
                    value={eventDescription}
                    onChange={(e) => setEventDescription(e.target.value)}
                    className="mt-1.5"
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full"
                  disabled={createEvent.isPending}
                >
                  {createEvent.isPending ? (
                    <>
                      <Loader2 className="animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="size-4" />
                      Create Event
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
