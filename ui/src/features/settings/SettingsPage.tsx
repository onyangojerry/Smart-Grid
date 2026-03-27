import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { changePassword, getMe, getOrganization, getPreferences, listRoles, updatePreferences, updateProfile } from "../../api/auth";
import { PageHeader } from "../../components/layout/PageHeader";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { User, Shield, Sliders, Check } from "lucide-react";
import "../../styles/features.css";

const TIMEZONES = [
  "UTC", "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
  "Europe/London", "Europe/Paris", "Europe/Berlin", "Asia/Tokyo", "Asia/Shanghai",
  "Asia/Singapore", "Australia/Sydney", "Africa/Johannesburg"
];

export function SettingsPage() {
  const qc = useQueryClient();
  const [activeTab, setActiveTab] = useState<"profile" | "password" | "preferences">("profile");
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const { data: user, isLoading: userLoading, error: userError } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: getMe,
  });

  const { data: org } = useQuery({
    queryKey: ["auth", "org"],
    queryFn: getOrganization,
  });

  const { data: rolesData } = useQuery({
    queryKey: ["auth", "roles"],
    queryFn: listRoles,
  });

  const { data: preferences } = useQuery({
    queryKey: ["auth", "preferences"],
    queryFn: getPreferences,
  });

  const profileMutation = useMutation({
    mutationFn: (data: { full_name?: string; timezone?: string }) => updateProfile(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["auth", "me"] });
      showSuccess("Profile updated successfully");
    },
  });

  const passwordMutation = useMutation({
    mutationFn: changePassword,
    onSuccess: () => {
      showSuccess("Password changed successfully");
      setPasswordForm({ current: "", new: "", confirm: "" });
    },
  });

  const preferencesMutation = useMutation({
    mutationFn: updatePreferences,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["auth", "preferences"] });
      showSuccess("Preferences saved");
    },
  });

  const [profileForm, setProfileForm] = useState({ full_name: user?.full_name || "", timezone: "" });
  const [passwordForm, setPasswordForm] = useState({ current: "", new: "", confirm: "" });
  const [prefForm, setPrefForm] = useState<Record<string, boolean>>({
    emailNotifications: (preferences as Record<string, boolean>)?.emailNotifications ?? true,
    alertNotifications: (preferences as Record<string, boolean>)?.alertNotifications ?? true,
    weeklyReport: (preferences as Record<string, boolean>)?.weeklyReport ?? false,
    darkMode: (preferences as Record<string, boolean>)?.darkMode ?? false,
    compactView: (preferences as Record<string, boolean>)?.compactView ?? false,
  });

  const showSuccess = (msg: string) => {
    setSuccessMessage(msg);
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    profileMutation.mutate({
      full_name: profileForm.full_name || undefined,
      timezone: profileForm.timezone || undefined,
    });
  };

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (passwordForm.new !== passwordForm.confirm) {
      alert("New passwords do not match");
      return;
    }
    if (passwordForm.new.length < 8) {
      alert("New password must be at least 8 characters");
      return;
    }
    passwordMutation.mutate({
      current_password: passwordForm.current,
      new_password: passwordForm.new,
    });
  };

  const handlePreferencesSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    preferencesMutation.mutate(prefForm);
  };

  if (userLoading) return <LoadingSpinner />;
  if (userError) return <ErrorBanner error={userError as Error} />;

  return (
    <div className="page-content">
      <PageHeader title="Settings" subtitle="Manage your account" />

      {successMessage && (
        <div style={{
          padding: "12px 16px",
          background: "#f0fdf4",
          border: "1px solid #16a34a",
          borderRadius: 10,
          marginBottom: 16,
          color: "#16a34a",
          display: "flex",
          alignItems: "center",
          gap: 8
        }}>
          <Check size={18} /> {successMessage}
        </div>
      )}

      <div className="tabs">
        <button
          onClick={() => setActiveTab("profile")}
          className={`tab ${activeTab === "profile" ? "active" : ""}`}
        >
          <User size={14} style={{ marginRight: 6 }} /> Profile
        </button>
        <button
          onClick={() => setActiveTab("password")}
          className={`tab ${activeTab === "password" ? "active" : ""}`}
        >
          <Shield size={14} style={{ marginRight: 6 }} /> Security
        </button>
        <button
          onClick={() => setActiveTab("preferences")}
          className={`tab ${activeTab === "preferences" ? "active" : ""}`}
        >
          <Sliders size={14} style={{ marginRight: 6 }} /> Preferences
        </button>
      </div>

      {activeTab === "profile" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <Card title="Personal Information">
            <form onSubmit={handleProfileSubmit}>
              <div className="form-group">
                <label className="form-label">Email Address</label>
                <input
                  type="email"
                  value={user?.email || ""}
                  disabled
                  className="form-input"
                  style={{ background: "var(--bg)" }}
                />
                <div className="form-hint">Email cannot be changed</div>
              </div>

              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input
                  type="text"
                  value={profileForm.full_name}
                  onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                  className="form-input"
                  placeholder="Enter your name"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Timezone</label>
                <select
                  value={profileForm.timezone}
                  onChange={(e) => setProfileForm({ ...profileForm, timezone: e.target.value })}
                  className="form-input"
                >
                  <option value="">Select timezone</option>
                  {TIMEZONES.map((tz) => (
                    <option key={tz} value={tz}>{tz}</option>
                  ))}
                </select>
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                disabled={profileMutation.isPending}
              >
                {profileMutation.isPending ? <LoadingSpinner /> : "Save Changes"}
              </button>
            </form>
          </Card>

          <Card title="Account Information">
            <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              <div>
                <label className="form-label">Role</label>
                <span className="badge badge-info">
                  {user?.role || "viewer"}
                </span>
              </div>

              {org && (
                <>
                  <div>
                    <label className="form-label">Organization</label>
                    <div style={{ fontWeight: 600, fontSize: 15 }}>{org.name}</div>
                    {org.industry && <div className="form-hint">{org.industry}</div>}
                  </div>

                  <div>
                    <label className="form-label">Organization Timezone</label>
                    <div>{org.timezone}</div>
                  </div>

                  <div>
                    <label className="form-label">Member Since</label>
                    <div>{new Date(org.created_at).toLocaleDateString()}</div>
                  </div>
                </>
              )}
            </div>
          </Card>
        </div>
      )}

      {activeTab === "password" && (
        <Card title="Change Password">
          <form onSubmit={handlePasswordSubmit} style={{ maxWidth: 400 }}>
            <div className="form-group">
              <label className="form-label">Current Password</label>
              <input
                type="password"
                value={passwordForm.current}
                onChange={(e) => setPasswordForm({ ...passwordForm, current: e.target.value })}
                className="form-input"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">New Password</label>
              <input
                type="password"
                value={passwordForm.new}
                onChange={(e) => setPasswordForm({ ...passwordForm, new: e.target.value })}
                className="form-input"
                required
                minLength={8}
              />
              <div className="form-hint">Minimum 8 characters</div>
            </div>

            <div className="form-group">
              <label className="form-label">Confirm New Password</label>
              <input
                type="password"
                value={passwordForm.confirm}
                onChange={(e) => setPasswordForm({ ...passwordForm, confirm: e.target.value })}
                className="form-input"
                required
              />
            </div>

            {passwordMutation.isError && (
              <div style={{
                padding: 12,
                background: "#fef2f2",
                border: "1px solid #fecaca",
                borderRadius: 8,
                marginBottom: 16,
                color: "#dc2626",
                fontSize: 14
              }}>
                {String((passwordMutation.error as Error)?.message || "Failed to change password")}
              </div>
            )}

            <button
              type="submit"
              className="btn btn-primary"
              disabled={passwordMutation.isPending}
            >
              {passwordMutation.isPending ? <LoadingSpinner /> : "Change Password"}
            </button>
          </form>
        </Card>
      )}

      {activeTab === "preferences" && (
        <Card title="Application Preferences">
          <form onSubmit={handlePreferencesSubmit} style={{ maxWidth: 500 }}>
            <div style={{ marginBottom: 24 }}>
              <h4 style={{ marginBottom: 16, color: "var(--text)", fontSize: 15, fontWeight: 600 }}>
                Notifications
              </h4>
              
              <label style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12, cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={prefForm.emailNotifications}
                  onChange={(e) => setPrefForm({ ...prefForm, emailNotifications: e.target.checked })}
                  style={{ width: 20, height: 20, accentColor: "var(--primary)" }}
                />
                <div>
                  <div style={{ fontWeight: 500 }}>Email notifications</div>
                  <div className="form-hint">Receive important updates via email</div>
                </div>
              </label>

              <label style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12, cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={prefForm.alertNotifications}
                  onChange={(e) => setPrefForm({ ...prefForm, alertNotifications: e.target.checked })}
                  style={{ width: 20, height: 20, accentColor: "var(--primary)" }}
                />
                <div>
                  <div style={{ fontWeight: 500 }}>Alert notifications</div>
                  <div className="form-hint">Get notified about system alerts</div>
                </div>
              </label>

              <label style={{ display: "flex", alignItems: "center", gap: 12, cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={prefForm.weeklyReport}
                  onChange={(e) => setPrefForm({ ...prefForm, weeklyReport: e.target.checked })}
                  style={{ width: 20, height: 20, accentColor: "var(--primary)" }}
                />
                <div>
                  <div style={{ fontWeight: 500 }}>Weekly summary report</div>
                  <div className="form-hint">Receive weekly performance summaries</div>
                </div>
              </label>
            </div>

            <div style={{ marginBottom: 24 }}>
              <h4 style={{ marginBottom: 16, color: "var(--text)", fontSize: 15, fontWeight: 600 }}>
                Display
              </h4>
              
              <label style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12, cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={prefForm.darkMode}
                  onChange={(e) => setPrefForm({ ...prefForm, darkMode: e.target.checked })}
                  style={{ width: 20, height: 20, accentColor: "var(--primary)" }}
                />
                <div>
                  <div style={{ fontWeight: 500 }}>Dark mode</div>
                  <div className="form-hint">Use dark theme for the interface</div>
                </div>
              </label>

              <label style={{ display: "flex", alignItems: "center", gap: 12, cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={prefForm.compactView}
                  onChange={(e) => setPrefForm({ ...prefForm, compactView: e.target.checked })}
                  style={{ width: 20, height: 20, accentColor: "var(--primary)" }}
                />
                <div>
                  <div style={{ fontWeight: 500 }}>Compact view</div>
                  <div className="form-hint">Show more content with less spacing</div>
                </div>
              </label>
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={preferencesMutation.isPending}
            >
              {preferencesMutation.isPending ? <LoadingSpinner /> : "Save Preferences"}
            </button>
          </form>
        </Card>
      )}
    </div>
  );
}
