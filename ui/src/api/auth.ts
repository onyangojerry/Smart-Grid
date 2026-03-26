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
