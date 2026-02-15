"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useContact, useUpdateContact } from "@/hooks/use-crm";
import {
  Search,
  Loader2,
  User,
  Building2,
  Briefcase,
  Phone,
  Mail,
  Tag,
  StickyNote,
  Save,
  AlertCircle,
} from "lucide-react";
import { toast } from "sonner";

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

  // Edit form state
  const [editName, setEditName] = useState("");
  const [editCompany, setEditCompany] = useState("");
  const [editTitle, setEditTitle] = useState("");
  const [editPhone, setEditPhone] = useState("");
  const [editNotes, setEditNotes] = useState("");
  const [editTags, setEditTags] = useState("");
  const [isEditing, setIsEditing] = useState(false);

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
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">CRM Contacts</h1>
          <p className="text-muted-foreground mt-1">
            Look up and manage contact information
          </p>
        </div>

        {/* Search */}
        <Card>
          <CardContent className="pt-6">
            <form onSubmit={handleSearch} className="flex gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                <Input
                  placeholder="Search by email address..."
                  value={searchEmail}
                  onChange={(e) => setSearchEmail(e.target.value)}
                  className="pl-9"
                  type="email"
                />
              </div>
              <Button type="submit" disabled={!searchEmail.trim()}>
                <Search className="size-4" />
                Look Up
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Loading */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        )}

        {/* Not Found */}
        {error && isFetched && !isLoading && (
          <Card>
            <CardContent className="flex flex-col items-center gap-3 py-12">
              <AlertCircle className="size-12 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                No contact found for{" "}
                <span className="font-medium text-foreground">
                  {activeEmail}
                </span>
              </p>
              <Button variant="outline" onClick={handleStartEdit}>
                Create Contact
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Contact Details */}
        {contact && !isLoading && !isEditing && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <User className="size-5" />
                Contact Details
              </CardTitle>
              <Button variant="outline" size="sm" onClick={handleStartEdit}>
                Edit
              </Button>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <Mail className="size-4 mt-0.5 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Email</p>
                      <p className="text-sm font-medium">{contact.email}</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <User className="size-4 mt-0.5 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Name</p>
                      <p className="text-sm font-medium">
                        {contact.name || "—"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <Building2 className="size-4 mt-0.5 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Company</p>
                      <p className="text-sm font-medium">
                        {contact.company || "—"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <Briefcase className="size-4 mt-0.5 text-muted-foreground" />
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
                    <Phone className="size-4 mt-0.5 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Phone</p>
                      <p className="text-sm font-medium">
                        {contact.phone || "—"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <Tag className="size-4 mt-0.5 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Tags</p>
                      <div className="flex flex-wrap gap-1 mt-0.5">
                        {contact.tags && contact.tags.length > 0 ? (
                          contact.tags.map((tag) => (
                            <span
                              key={tag}
                              className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary"
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
                    <StickyNote className="size-4 mt-0.5 text-muted-foreground" />
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
            </CardContent>
          </Card>
        )}

        {/* Edit Form */}
        {isEditing && !isLoading && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="size-5" />
                {contact ? "Edit Contact" : "Create Contact"}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="edit-name">Name</Label>
                  <Input
                    id="edit-name"
                    placeholder="Full name"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    className="mt-1.5"
                  />
                </div>
                <div>
                  <Label htmlFor="edit-company">Company</Label>
                  <Input
                    id="edit-company"
                    placeholder="Company name"
                    value={editCompany}
                    onChange={(e) => setEditCompany(e.target.value)}
                    className="mt-1.5"
                  />
                </div>
                <div>
                  <Label htmlFor="edit-title">Title</Label>
                  <Input
                    id="edit-title"
                    placeholder="Job title"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    className="mt-1.5"
                  />
                </div>
                <div>
                  <Label htmlFor="edit-phone">Phone</Label>
                  <Input
                    id="edit-phone"
                    placeholder="Phone number"
                    value={editPhone}
                    onChange={(e) => setEditPhone(e.target.value)}
                    className="mt-1.5"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="edit-tags">
                  Tags{" "}
                  <span className="text-muted-foreground font-normal">
                    (comma-separated)
                  </span>
                </Label>
                <Input
                  id="edit-tags"
                  placeholder="vip, partner, lead"
                  value={editTags}
                  onChange={(e) => setEditTags(e.target.value)}
                  className="mt-1.5"
                />
              </div>
              <div>
                <Label htmlFor="edit-notes">Notes</Label>
                <Input
                  id="edit-notes"
                  placeholder="Notes about this contact"
                  value={editNotes}
                  onChange={(e) => setEditNotes(e.target.value)}
                  className="mt-1.5"
                />
              </div>
              <div className="flex gap-2 pt-2">
                <Button
                  onClick={handleSave}
                  disabled={updateContact.isPending}
                >
                  {updateContact.isPending ? (
                    <>
                      <Loader2 className="animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="size-4" />
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
            </CardContent>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
