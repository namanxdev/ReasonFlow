import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Contact, PaginatedResponse } from "@/types";

export interface ContactUpdatePayload {
  name?: string;
  company?: string;
  title?: string;
  phone?: string;
  notes?: string;
  tags?: string[];
}

export interface ContactFilters {
  q?: string;
  page?: number;
  per_page?: number;
}

export interface ContactEmail {
  id: string;
  subject: string | null;
  sender: string | null;
  recipient: string | null;
  received_at: string | null;
  classification: string | null;
  status: string | null;
}

export function useContacts(filters: ContactFilters = {}) {
  return useQuery({
    queryKey: ["crm", "contacts", filters],
    queryFn: () =>
      api
        .get<PaginatedResponse<Contact>>(`/crm/contacts`, {
          params: {
            q: filters.q || undefined,
            page: filters.page || 1,
            per_page: filters.per_page || 25,
          },
        })
        .then((r) => r.data),
    placeholderData: (previousData) => previousData,
  });
}

export function useContact(email: string) {
  return useQuery({
    queryKey: ["crm", "contact", email],
    queryFn: () =>
      api.get<Contact>(`/crm/contacts/${encodeURIComponent(email)}`).then((r) => r.data),
    enabled: !!email,
    retry: false,
  });
}

export function useContactEmails(email: string) {
  return useQuery({
    queryKey: ["crm", "contact-emails", email],
    queryFn: () =>
      api
        .get<ContactEmail[]>(`/crm/contacts/${encodeURIComponent(email)}/emails`)
        .then((r) => r.data),
    enabled: !!email,
  });
}

export function useUpdateContact() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      email,
      data,
    }: {
      email: string;
      data: ContactUpdatePayload;
    }) =>
      api
        .put<Contact>(`/crm/contacts/${encodeURIComponent(email)}`, data)
        .then((r) => r.data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["crm", "contact", variables.email],
      });
      queryClient.invalidateQueries({
        queryKey: ["crm", "contacts"],
      });
    },
  });
}

export function useDeleteContact() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (email: string) =>
      api.delete(`/crm/contacts/${encodeURIComponent(email)}`),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["crm", "contacts"],
      });
    },
  });
}
