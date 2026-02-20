"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { AppShellTopNav } from "@/components/layout/app-shell-top-nav";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useContact, useContacts, useUpdateContact } from "@/hooks/use-crm";
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
  Contact,
} from "lucide-react";
import { toast } from "sonner";
import { PageHeader, SectionCard, StaggerContainer, StaggerItem } from "@/components/layout/dashboard-shell";

function formatDate(iso: string | null) {
  if (!iso) return "N/A";
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function CrmPage() {
  const [searchEmail, setSearchEmail] = useState("");
  const [activeEmail, setActiveEmail] = useState("");

  const [editName, setEditName] = useState("");
  const [editCompany, setEditCompany] = useState("");
  const [editTitle, setEditTitle] = useState("");
  const [editPhone, setEditPhone] = useState("");
  const [editNotes, setEditNotes] = useState("");
  const [editTags, setEditTags] = useState("");
  const [isEditing, setIsEditing] = useState(false);

  const { data: contacts, isLoading: contactsLoading } = useContacts();
  const {
    data: contact,
    isLoading,
    error,
    isFetched,
  } = useContact(activeEmail);
  const updateContact = useUpdateContact();

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
                    onChange={(e) => setSearchEmail(e.target.value)}
                    className="pl-9 h-12 bg-white/70 border-white/50 text-base"
                    type="email"
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
                  {contacts && (
                    <span className="px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-600 text-xs font-medium">
                      {contacts.length}
                    </span>
                  )}
                </div>
              </div>
              <div className="p-5">
                {contactsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="size-6 animate-spin text-muted-foreground" />
                  </div>
                ) : contacts && contacts.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {contacts.map((c) => (
                      <div
                        key={c.email}
                        className="border rounded-xl p-4 cursor-pointer hover:shadow-lg hover:border-indigo-200 transition-all bg-white/50"
                        onClick={() => {
                          setSearchEmail(c.email);
                          setActiveEmail(c.email);
                          setIsEditing(false);
                        }}
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-xl bg-indigo-100 flex items-center justify-center flex-shrink-0">
                            <Contact className="w-5 h-5 text-indigo-600" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm truncate">
                              {c.name || c.email}
                            </p>
                            <p className="text-xs text-muted-foreground truncate">
                              {c.email}
                            </p>
                            {c.company && (
                              <p className="text-xs text-muted-foreground mt-1">
                                {c.company}
                              </p>
                            )}
                          </div>
                        </div>
                        {c.tags && c.tags.length > 0 && (
                          <div className="flex gap-1 mt-3 ml-[52px]">
                            {c.tags.slice(0, 3).map((tag) => (
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

          {/* Loading */}
          {isLoading && (
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
                  <Button variant="outline" size="sm" onClick={handleStartEdit}>
                    Edit
                  </Button>
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
                            {contact.name || "—"}
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
                            {contact.company || "—"}
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
                            {contact.title || "—"}
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
                            {contact.phone || "—"}
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
                              <span className="text-sm">—</span>
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
                          <p className="text-sm">{contact.notes || "—"}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="mt-6 pt-4 border-t text-xs text-muted-foreground">
                    Last interaction: {formatDate(contact.last_interaction)}
                  </div>
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
