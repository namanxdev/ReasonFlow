import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { Contact } from "@/types";

export interface ContactUpdatePayload {
  name?: string;
  company?: string;
  title?: string;
  phone?: string;
  notes?: string;
  tags?: string[];
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
    },
  });
}
