import { apiFetch } from "./client";

export type User = {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  status: string;
  created_at: string;
};

export type UserCreate = {
  email: string;
  full_name?: string;
  role: string;
};

export type UserUpdate = {
  full_name?: string;
  role?: string;
  status?: string;
};

export type Invitation = {
  id: string;
  email: string;
  role: string;
  expires_at: string;
  accepted_at: string | null;
  created_at: string;
  is_expired?: boolean;
};

export type AuditLogEntry = {
  id: string;
  action: string;
  target_user_id: string | null;
  target_email: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
  actor_name: string | null;
};

export const listUsers = () =>
  apiFetch<{ items: User[] }>("/api/v1/users");

export const getUser = (userId: string) =>
  apiFetch<User>(`/api/v1/users/${userId}`);

export const updateUser = (userId: string, data: UserUpdate) =>
  apiFetch<User>(`/api/v1/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(data)
  });

export const inviteUser = (data: { email: string; role: string }) =>
  apiFetch<{ id: string; email: string; role: string; expires_at: string; invitation_link: string; token: string }>(
    "/api/v1/users/invite",
    {
      method: "POST",
      body: JSON.stringify(data)
    }
  );

export const listInvitations = () =>
  apiFetch<{ items: Invitation[] }>("/api/v1/users/invitations");

export const revokeInvitation = (invitationId: string) =>
  apiFetch<{ status: string }>(`/api/v1/users/invitations/${invitationId}`, {
    method: "DELETE"
  });

export const deactivateUser = (userId: string) =>
  apiFetch<{ status: string; message: string }>(`/api/v1/users/${userId}/deactivate`, {
    method: "POST"
  });

export const reactivateUser = (userId: string) =>
  apiFetch<{ status: string; message: string }>(`/api/v1/users/${userId}/reactivate`, {
    method: "POST"
  });

export const getAuditLog = (limit = 100) =>
  apiFetch<{ items: AuditLogEntry[] }>(`/api/v1/users/audit-log`, {
    params: { limit: String(limit) }
  });
