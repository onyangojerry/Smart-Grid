import { apiFetch } from "./client";
import type { User } from "../types";

export type LoginBody = { email: string; password: string };
export type LoginResponse = { access_token: string; token_type: "bearer" };

export const login = (body: LoginBody) =>
  apiFetch<LoginResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(body)
  });

export const signup = (body: LoginBody & { name?: string }) =>
  apiFetch<LoginResponse>("/api/v1/auth/signup", {
    method: "POST",
    body: JSON.stringify(body)
  });

export const getMe = () => apiFetch<User>("/api/v1/auth/me");

export const updateProfile = (data: { full_name?: string; timezone?: string }) =>
  apiFetch<User>("/api/v1/auth/me", {
    method: "PATCH",
    body: JSON.stringify(data)
  });

export const changePassword = (data: { current_password: string; new_password: string }) =>
  apiFetch<{ status: string; message: string }>("/api/v1/auth/me/password", {
    method: "POST",
    body: JSON.stringify(data)
  });

export const getPreferences = () =>
  apiFetch<Record<string, unknown>>("/api/v1/auth/me/preferences");

export const updatePreferences = (preferences: Record<string, unknown>) =>
  apiFetch<Record<string, unknown>>("/api/v1/auth/me/preferences", {
    method: "PUT",
    body: JSON.stringify(preferences)
  });

export type Organization = {
  id: string;
  name: string;
  legal_name: string | null;
  industry: string | null;
  timezone: string;
  role: string;
  created_at: string;
};

export const getOrganization = () =>
  apiFetch<Organization>("/api/v1/auth/me/organization");

export const listRoles = () =>
  apiFetch<{ roles: string[] }>("/api/v1/auth/roles");
