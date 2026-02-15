import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";

export interface TimeSlot {
  start: string;
  end: string;
  duration_minutes: number;
}

export interface AvailabilityResponse {
  free_slots: TimeSlot[];
  checked_range_start: string;
  checked_range_end: string;
}

export interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  attendees: string[];
  html_link: string;
}

export interface CreateEventPayload {
  title: string;
  start: string;
  end: string;
  attendees?: string[];
  description?: string;
  location?: string;
}

export function useAvailability(start?: string, end?: string) {
  return useQuery({
    queryKey: ["calendar", "availability", start, end],
    queryFn: () =>
      api
        .get<AvailabilityResponse>("/calendar/availability", {
          params: { start, end },
        })
        .then((r) => r.data),
    enabled: !!start && !!end,
  });
}

export function useCreateEvent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateEventPayload) =>
      api.post<CalendarEvent>("/calendar/events", payload).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["calendar"] });
    },
  });
}
