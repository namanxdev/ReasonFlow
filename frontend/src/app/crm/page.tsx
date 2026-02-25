"use client";

import { useState, memo } from "react";
import { cn } from "@/lib/utils";
import type { Contact } from "@/types";
import { AppShellTopNav } from "@/components/layout/app-shell-top-nav";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Pagination } from "@/components/ui/pagination";
import { useContact, useContacts, useUpdateContact, useDeleteContact, useContactEmails } from "@/hooks/use-crm";
import {
  Search,
  Loader2,
  User,
  Users,
  Building2,
  Briefcase,
  Phone,
  Mail,
  Tag,
  StickyNote,
  Save,
  AlertCircle,
  Contact as ContactIcon,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";
import { PageHeader, SectionCard, StaggerContainer, StaggerItem } from "@/components/layout/dashboard-shell";
import { formatDateTime } from "@/lib/date-utils";
import { useDebounce } from "@/hooks/use-debounce";

// Memoized Contact Card Component
interface ContactCardProps {
  contact: Contact;
  onSelect: (email: string) => void;
  isActive: boolean;
}

const ContactCard = memo(function ContactCard({
  contact,
  onSelect,
  isActive,
}: ContactCardProps) {
  return (
    <div
      role="button"
      tabIndex={0}
      className={cn(
        "border rounded-xl p-4 cursor-pointer hover:shadow-lg transition-all",
        isActive
          ? "border-indigo-500 bg-indigo-50"
          : "hover:border-indigo-200 bg-white/50"
      )}
      onClick={() => onSelect(contact.email)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect(contact.email);
        }
      }}
    >
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-xl bg-indigo-100 flex items-center justify-center flex-shrink-0">
          <ContactIcon className="w-5 h-5 text-indigo-600" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm truncate">
            {contact.name || contact.email}
          </p>
          <p className="text-xs text-muted-foreground truncate">
            {contact.email}
          </p>
          {contact.company && (
            <p className="text-xs text-muted-foreground mt-1">
              {contact.company}
            </p>
          )}
        </div>
      </div>
      {contact.tags && contact.tags.length > 0 && (
        <div className="flex gap-1 mt-3 ml-[52px]">
          {contact.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="text-xs bg-indigo-100 text-indigo-600 rounded-full px-2 py-0.5 font-medium"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
});

export default function CrmPage() {
  const [searchEmail, setSearchEmail] = useState("");
  const [activeEmail, setActiveEmail] = useState("");
  const [contactPage, setContactPage] = useState(1);
  const [contactPageSize, setContactPageSize] = useState(25);

  // Debounce the search input for API filtering
  const debouncedSearchEmail = useDebounce(searchEmail, 300);

  const [editName, setEditName] = useState("");
  const [editCompany, setEditCompany] = useState("");
  const [editTitle, setEditTitle] = useState("");
  const [editPhone, setEditPhone] = useState("");
  const [editNotes, setEditNotes] = useState("");
  const [editTags, setEditTags] = useState("");
  const [isEditing, setIsEditing] = useState(false);

  // Use debounced search for filtering contacts with pagination
  const { data: contactsData, isLoading: contactsLoading, isFetching: contactsFetching } = useContacts({
    q: debouncedSearchEmail || undefined,
    page: contactPage,
    per_page: contactPageSize,
  });
  const {
    data: contact,
    isLoading,
    error,
    isFetched,
  } = useContact(activeEmail);
  const { data: contactEmailHistory } = useContactEmails(activeEmail);
  const updateContact = useUpdateContact();
  const deleteContact = useDeleteContact();

  const contacts = contactsData?.items || [];
  const contactsTotal = contactsData?.total || 0;
  const contactsTotalPages = contactsData ? Math.ceil(contactsData.total / contactsData.per_page) || 1 : 1;

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchEmail.trim()) {
      setActiveEmail(searchEmail.trim());
      setIsEditing(false);
    }
  };

  const handleStartEdit = () => {
    if (contact) {
      setEditName(contact.name || "");
      setEditCompany(contact.company || "");
      setEditTitle(contact.title || "");
      setEditPhone(contact.phone || "");
      setEditNotes(contact.notes || "");
      setEditTags(contact.tags?.join(", ") || "");
    }
    setIsEditing(true);
  };

  const handleSave = () => {
    if (!activeEmail) return;

    updateContact.mutate(
      {
        email: activeEmail,
        data: {
          name: editName || undefined,
          company: editCompany || undefined,
          title: editTitle || undefined,
          phone: editPhone || undefined,
          notes: editNotes || undefined,
          tags: editTags ? editTags.split(",").map((t) => t.trim()) : undefined,
        },
      },
      {
        onSuccess: () => {
          toast.success("Contact updated successfully");
          setIsEditing(false);
        },
        onError: (err: any) => {
          toast.error(
            err.response?.data?.detail || "Failed to update contact"
          );
        },
      }
    );
  };

  const handleDelete = () => {
    if (!activeEmail) return;
    deleteContact.mutate(activeEmail, {
      onSuccess: () => {
        toast.success("Contact deleted");
        setActiveEmail("");
        setIsEditing(false);
      },
      onError: (err: any) => {
        toast.error(err.response?.data?.detail || "Failed to delete contact");
      },
    });
  };

  return (
    <AppShellTopNav>
      <StaggerContainer className="space-y-6">
          {/* Header */}
          <StaggerItem>
            <PageHeader
              icon={<Users className="w-6 h-6 text-indigo-600" />}
              iconColor="bg-indigo-500/10"
              title="CRM Contacts"
              subtitle="Look up and manage contact information"
            />
          </StaggerItem>

          {/* Search */}
          <StaggerItem>
            <SectionCard className="p-5">
              <form onSubmit={handleSearch} className="flex gap-3">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                  <Input
                    placeholder="Search by email address..."
                    value={searchEmail}
                    onChange={(e) => {
                      setSearchEmail(e.target.value);
                      setContactPage(1);
                    }}
                    className="pl-9 h-12 bg-white/70 border-white/50 text-base"
                    type="text"
                  />
                </div>
                <Button type="submit" disabled={!searchEmail.trim()} className="h-12 px-6 gap-2">
                  <Search className="size-4" />
                  Look Up
                </Button>
              </form>
            </SectionCard>
          </StaggerItem>

          {/* All Contacts */}
          <StaggerItem>
            <SectionCard>
              <div className="p-5 border-b bg-gradient-to-r from-indigo-50/50 to-violet-50/50">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-indigo-500" />
                  <span className="text-sm font-medium">All Contacts</span>
                  {contactsData && (
                    <span className="px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-600 text-xs font-medium">
                      {contactsData.total}
                    </span>
                  )}
                </div>
              </div>
              <div className="p-5">
                {contactsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="size-6 animate-spin text-muted-foreground" />
                  </div>
                ) : contacts.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {contacts.map((c) => (
                      <ContactCard
                        key={c.email}
                        contact={c}
                        onSelect={(email) => {
                          setSearchEmail(email);
                          setActiveEmail(email);
                          setIsEditing(false);
                        }}
                        isActive={c.email === activeEmail}
                      />
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    No contacts yet. Sync your emails to auto-populate contacts.
                  </p>
                )}
              </div>
            </SectionCard>
          </StaggerItem>

          {/* Contacts Pagination */}
          {contactsTotal > 0 && (
            <StaggerItem>
              <Pagination
                currentPage={contactPage}
                totalPages={contactsTotalPages}
                totalItems={contactsTotal}
                pageSize={contactPageSize}
                isFetching={contactsFetching}
                itemLabel="contacts"
                onPageChange={setContactPage}
                onPageSizeChange={(size) => {
                  setContactPageSize(size);
                  setContactPage(1);
                }}
              />
            </StaggerItem>
          )}

          {/* Select a contact prompt */}
          {!activeEmail && !isEditing && (
            <StaggerItem>
              <SectionCard>
                <div className="flex flex-col items-center gap-3 py-16">
                  <div className="w-16 h-16 rounded-2xl bg-indigo-50 flex items-center justify-center">
                    <ContactIcon className="size-8 text-indigo-400" />
                  </div>
                  <p className="text-sm text-muted-foreground">Select a contact to view details</p>
                </div>
              </SectionCard>
            </StaggerItem>
          )}

          {/* Loading */}
          {activeEmail && (isLoading || (!contact && !error && !isFetched)) && (
            <StaggerItem>
              <div className="flex items-center justify-center py-12">
                <div className="relative">
                  <div className="absolute inset-0 bg-indigo-500/20 blur-xl rounded-full" />
                  <Loader2 className="relative size-8 animate-spin text-indigo-500" />
                </div>
              </div>
            </StaggerItem>
          )}

          {/* Not Found */}
          {error && isFetched && !isLoading && (
            <StaggerItem>
              <SectionCard>
                <div className="flex flex-col items-center gap-3 py-12">
                  <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center">
                    <AlertCircle className="size-8 text-slate-500" />
                  </div>
                  <p className="text-sm text-muted-foreground">
                    No contact found for{" "}
                    <span className="font-medium text-foreground">
                      {activeEmail}
                    </span>
                  </p>
                  <Button variant="outline" onClick={handleStartEdit}>
                    Create Contact
                  </Button>
                </div>
              </SectionCard>
            </StaggerItem>
          )}

          {/* Contact Details */}
          {contact && !isLoading && !isEditing && (
            <StaggerItem>
              <SectionCard>
                <div className="p-5 border-b bg-gradient-to-r from-indigo-50/50 to-violet-50/50 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-indigo-500" />
                    <span className="text-sm font-medium">Contact Details</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={handleStartEdit}>
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleDelete}
                      disabled={deleteContact.isPending}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      {deleteContact.isPending ? (
                        <Loader2 className="size-4 animate-spin" />
                      ) : (
                        <Trash2 className="size-4" />
                      )}
                    </Button>
                  </div>
                </div>
                <div className="p-5">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
                          <Mail className="size-4 text-slate-600" />
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Email</p>
                          <p className="text-sm font-medium">{contact.email}</p>
                        </div>
                      </div>
                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
                          <User className="size-4 text-slate-600" />
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Name</p>
                          <p className="text-sm font-medium">
                            {contact.name || "\u2014"}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
                          <Building2 className="size-4 text-slate-600" />
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Company</p>
                          <p className="text-sm font-medium">
                            {contact.company || "\u2014"}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
                          <Briefcase className="size-4 text-slate-600" />
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Title</p>
                          <p className="text-sm font-medium">
                            {contact.title || "\u2014"}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
                          <Phone className="size-4 text-slate-600" />
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Phone</p>
                          <p className="text-sm font-medium">
                            {contact.phone || "\u2014"}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
                          <Tag className="size-4 text-slate-600" />
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Tags</p>
                          <div className="flex flex-wrap gap-1 mt-0.5">
                            {contact.tags && contact.tags.length > 0 ? (
                              contact.tags.map((tag) => (
                                <span
                                  key={tag}
                                  className="inline-flex items-center rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-600"
                                >
                                  {tag}
                                </span>
                              ))
                            ) : (
                              <span className="text-sm">{"\u2014"}</span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
                          <StickyNote className="size-4 text-slate-600" />
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Notes</p>
                          <p className="text-sm">{contact.notes || "\u2014"}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="mt-6 pt-4 border-t text-xs text-muted-foreground">
                    Last interaction: {contact.last_interaction ? formatDateTime(contact.last_interaction) : "N/A"}
                  </div>
                </div>
              </SectionCard>
            </StaggerItem>
          )}

          {/* Email History */}
          {contact && !isLoading && !isEditing && contactEmailHistory && contactEmailHistory.length > 0 && (
            <StaggerItem>
              <SectionCard>
                <div className="p-5 border-b bg-gradient-to-r from-indigo-50/50 to-violet-50/50">
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-indigo-500" />
                    <span className="text-sm font-medium">Email History</span>
                    <span className="px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-600 text-xs font-medium">
                      {contactEmailHistory.length}
                    </span>
                  </div>
                </div>
                <div className="divide-y">
                  {contactEmailHistory.map((email) => (
                    <div key={email.id} className="p-4 hover:bg-slate-50/50">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium truncate flex-1">
                          {email.subject || "(No subject)"}
                        </p>
                        <div className="flex items-center gap-2 ml-4">
                          {email.classification && (
                            <span className="text-xs bg-blue-100 text-blue-600 rounded-full px-2 py-0.5">
                              {email.classification}
                            </span>
                          )}
                          {email.status && (
                            <span className="text-xs bg-slate-100 text-slate-600 rounded-full px-2 py-0.5">
                              {email.status}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                        <span>{email.sender}</span>
                        {email.received_at && (
                          <span>{formatDateTime(email.received_at)}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </SectionCard>
            </StaggerItem>
          )}

          {/* Edit Form */}
          {isEditing && !isLoading && (
            <StaggerItem>
              <SectionCard>
                <div className="p-5 border-b bg-gradient-to-r from-indigo-50/50 to-violet-50/50">
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-indigo-500" />
                    <span className="text-sm font-medium">
                      {contact ? "Edit Contact" : "Create Contact"}
                    </span>
                  </div>
                </div>
                <div className="p-5">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="edit-name" className="text-xs text-muted-foreground">Name</Label>
                      <Input
                        id="edit-name"
                        placeholder="Full name"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        className="mt-1.5 h-11 bg-white/70 border-white/50"
                      />
                    </div>
                    <div>
                      <Label htmlFor="edit-company" className="text-xs text-muted-foreground">Company</Label>
                      <Input
                        id="edit-company"
                        placeholder="Company name"
                        value={editCompany}
                        onChange={(e) => setEditCompany(e.target.value)}
                        className="mt-1.5 h-11 bg-white/70 border-white/50"
                      />
                    </div>
                    <div>
                      <Label htmlFor="edit-title" className="text-xs text-muted-foreground">Title</Label>
                      <Input
                        id="edit-title"
                        placeholder="Job title"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        className="mt-1.5 h-11 bg-white/70 border-white/50"
                      />
                    </div>
                    <div>
                      <Label htmlFor="edit-phone" className="text-xs text-muted-foreground">Phone</Label>
                      <Input
                        id="edit-phone"
                        placeholder="Phone number"
                        value={editPhone}
                        onChange={(e) => setEditPhone(e.target.value)}
                        className="mt-1.5 h-11 bg-white/70 border-white/50"
                      />
                    </div>
                  </div>
                  <div className="mt-4">
                    <Label htmlFor="edit-tags" className="text-xs text-muted-foreground">
                      Tags <span className="text-muted-foreground font-normal">(comma-separated)</span>
                    </Label>
                    <Input
                      id="edit-tags"
                      placeholder="vip, partner, lead"
                      value={editTags}
                      onChange={(e) => setEditTags(e.target.value)}
                      className="mt-1.5 h-11 bg-white/70 border-white/50"
                    />
                  </div>
                  <div className="mt-4">
                    <Label htmlFor="edit-notes" className="text-xs text-muted-foreground">Notes</Label>
                    <Input
                      id="edit-notes"
                      placeholder="Notes about this contact"
                      value={editNotes}
                      onChange={(e) => setEditNotes(e.target.value)}
                      className="mt-1.5 h-11 bg-white/70 border-white/50"
                    />
                  </div>
                  <div className="flex gap-2 pt-5">
                    <Button
                      onClick={handleSave}
                      disabled={updateContact.isPending}
                    >
                      {updateContact.isPending ? (
                        <>
                          <Loader2 className="animate-spin mr-2" />
                          Saving...
                        </>
                      ) : (
                        <>
                          <Save className="size-4 mr-2" />
                          Save
                        </>
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => setIsEditing(false)}
                      disabled={updateContact.isPending}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              </SectionCard>
            </StaggerItem>
          )}
      </StaggerContainer>
    </AppShellTopNav>
  );
}
