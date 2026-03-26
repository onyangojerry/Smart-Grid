import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { Navigate } from "react-router-dom";
import { TOKEN_KEY } from "../../api/client";
import { getMe, login, signup } from "../../api/auth";
import type { User } from "../../types";

type AuthContextValue = {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isBootstrapping: boolean;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState<boolean>(Boolean(localStorage.getItem(TOKEN_KEY)));

  useEffect(() => {
    let mounted = true;
    async function validate() {
      if (!token) {
        if (mounted) setIsBootstrapping(false);
        return;
      }
      try {
        const me = await getMe();
        if (mounted) {
          setUser(me);
        }
      } catch (error) {
        localStorage.removeItem(TOKEN_KEY);
        if (mounted) {
          setToken(null);
          setUser(null);
        }
      } finally {
        if (mounted) {
          setIsBootstrapping(false);
        }
      }
    }
    void validate();
    return () => {
      mounted = false;
    };
  }, [token]);

  const ctx = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      login: async (email: string, password: string) => {
        const result = await login({ email, password });
        localStorage.setItem(TOKEN_KEY, result.access_token);
        setToken(result.access_token);
        const me = await getMe();
        setUser(me);
      },
      signup: async (email: string, password: string, name?: string) => {
        const result = await signup({ email, password, name });
        localStorage.setItem(TOKEN_KEY, result.access_token);
        setToken(result.access_token);
        const me = await getMe();
        setUser(me);
      },
      logout: () => {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
        setIsBootstrapping(false);
      },
      isAuthenticated: Boolean(token && user),
      isBootstrapping
    }),
    [user, token, isBootstrapping]
  );

  return <AuthContext.Provider value={ctx}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isBootstrapping } = useAuth();
  if (isBootstrapping) {
    return <div style={{ padding: 24 }}>Loading session...</div>;
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}
