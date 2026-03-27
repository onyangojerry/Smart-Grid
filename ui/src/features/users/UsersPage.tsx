import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { 
  deactivateUser, getAuditLog, inviteUser, listInvitations, 
  listUsers, reactivateUser, revokeInvitation, updateUser 
} from "../../api/users";
import { useAuth } from "../auth/useAuth";
import { PageHeader } from "../../components/layout/PageHeader";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { Badge } from "../../components/ui/Badge";
import { UserPlus, Shield, Clock, X } from "lucide-react";
import "../../styles/features.css";

const ROLES = [
  "client_admin",
  "facility_manager", 
  "energy_analyst",
  "viewer",
  "ops_admin",
  "ml_engineer"
];

export function UsersPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const [activeTab, setActiveTab] = useState<"users" | "invitations" | "audit">("users");
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [editingUser, setEditingUser] = useState<string | null>(null);
  const [editRole, setEditRole] = useState("");

  const usersQuery = useQuery({
    queryKey: ["users", "list"],
    queryFn: listUsers,
  });

  const invitationsQuery = useQuery({
    queryKey: ["users", "invitations"],
    queryFn: listInvitations,
  });

  const auditQuery = useQuery({
    queryKey: ["users", "audit"],
    queryFn: () => getAuditLog(50),
  });

  const inviteMutation = useMutation({
    mutationFn: (data: { email: string; role: string }) => inviteUser(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      setShowInviteModal(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: { role: string } }) => 
      updateUser(userId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      setEditingUser(null);
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: deactivateUser,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });

  const reactivateMutation = useMutation({
    mutationFn: reactivateUser,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });

  const revokeMutation = useMutation({
    mutationFn: revokeInvitation,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });

  const isAdmin = user?.role === "client_admin" || user?.role === "admin" || user?.role === "owner";

  return (
    <div className="page-content">
      <PageHeader title="User Management" subtitle="Manage users and permissions" />

      <div className="tabs">
        <button
          onClick={() => setActiveTab("users")}
          className={`tab ${activeTab === "users" ? "active" : ""}`}
        >
          <Shield size={14} style={{ marginRight: 6 }} />
          Users ({usersQuery.data?.items?.length || 0})
        </button>
        {isAdmin && (
          <button
            onClick={() => setActiveTab("invitations")}
            className={`tab ${activeTab === "invitations" ? "active" : ""}`}
          >
            Invitations ({invitationsQuery.data?.items?.filter(i => !i.accepted_at).length || 0})
          </button>
        )}
        {isAdmin && (
          <button
            onClick={() => setActiveTab("audit")}
            className={`tab ${activeTab === "audit" ? "active" : ""}`}
          >
            <Clock size={14} style={{ marginRight: 6 }} />
            Audit Log
          </button>
        )}
      </div>

      {activeTab === "users" && (
        <Card 
          title="Team Members"
          actions={
            isAdmin && (
              <button
                onClick={() => setShowInviteModal(true)}
                className="btn btn-primary btn-sm"
              >
                <UserPlus size={14} /> Invite User
              </button>
            )
          }
        >
          {usersQuery.isLoading ? (
            <LoadingSpinner />
          ) : usersQuery.isError ? (
            <ErrorBanner error={usersQuery.error as Error} />
          ) : usersQuery.data?.items.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">👥</div>
              <div className="empty-state-title">No team members yet</div>
              <div className="empty-state-description">
                Invite team members to collaborate on this organization.
              </div>
            </div>
          ) : (
            <div className="data-table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Joined</th>
                    {isAdmin && <th style={{ textAlign: "right" }}>Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {usersQuery.data?.items.map((u) => (
                    <tr key={u.id}>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                          <img
                            src={`https://picsum.photos/seed/${u.id}/32/32`}
                            alt={u.full_name || "User"}
                            style={{ borderRadius: "50%", width: 32, height: 32 }}
                          />
                          <span style={{ fontWeight: 500 }}>{u.full_name || "—"}</span>
                        </div>
                      </td>
                      <td style={{ color: "var(--text-muted)" }}>{u.email}</td>
                      <td>
                        {editingUser === u.id ? (
                          <select
                            value={editRole}
                            onChange={(e) => setEditRole(e.target.value)}
                            className="form-input"
                            style={{ width: "auto", padding: "4px 8px" }}
                          >
                            {ROLES.map((r) => (
                              <option key={r} value={r}>{r}</option>
                            ))}
                          </select>
                        ) : (
                          <Badge kind="plain" value={u.role} />
                        )}
                      </td>
                      <td>
                        <span className={`badge ${u.status === "active" ? "badge-success" : "badge-neutral"}`}>
                          {u.status}
                        </span>
                      </td>
                      <td style={{ color: "var(--text-muted)" }}>
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                      {isAdmin && (
                        <td>
                          <div className="data-table-actions">
                            {editingUser === u.id ? (
                              <>
                                <button
                                  onClick={() => updateMutation.mutate({ userId: u.id, data: { role: editRole } })}
                                  className="btn btn-primary btn-sm"
                                  disabled={updateMutation.isPending}
                                >
                                  Save
                                </button>
                                <button
                                  onClick={() => setEditingUser(null)}
                                  className="btn btn-secondary btn-sm"
                                >
                                  Cancel
                                </button>
                              </>
                            ) : (
                              <>
                                <button
                                  onClick={() => {
                                    setEditingUser(u.id);
                                    setEditRole(u.role);
                                  }}
                                  className="btn btn-secondary btn-sm"
                                  disabled={u.id === user?.id}
                                >
                                  Edit
                                </button>
                                {u.status === "active" ? (
                                  <button
                                    onClick={() => {
                                      if (confirm(`Deactivate ${u.email}?`)) {
                                        deactivateMutation.mutate(u.id);
                                      }
                                    }}
                                    className="btn btn-danger btn-sm"
                                    disabled={u.id === user?.id}
                                  >
                                    Deactivate
                                  </button>
                                ) : (
                                  <button
                                    onClick={() => reactivateMutation.mutate(u.id)}
                                    className="btn btn-success btn-sm"
                                  >
                                    Reactivate
                                  </button>
                                )}
                              </>
                            )}
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {activeTab === "invitations" && isAdmin && (
        <Card title="Pending Invitations">
          {invitationsQuery.isLoading ? (
            <LoadingSpinner />
          ) : invitationsQuery.isError ? (
            <ErrorBanner error={invitationsQuery.error as Error} />
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {invitationsQuery.data?.items.filter(i => !i.accepted_at).length === 0 ? (
                <div className="empty-state">
                  <div className="empty-state-icon">✉️</div>
                  <div className="empty-state-title">No pending invitations</div>
                  <div className="empty-state-description">
                    All team members have accepted their invitations.
                  </div>
                </div>
              ) : (
                invitationsQuery.data?.items
                  .filter(i => !i.accepted_at)
                  .map((inv) => (
                    <div
                      key={inv.id}
                      className="card"
                      style={{ 
                        display: "flex", 
                        alignItems: "center", 
                        justifyContent: "space-between",
                        padding: 16
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 600 }}>{inv.email}</div>
                        <div style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 4 }}>
                          <span className="badge badge-info">{inv.role}</span>
                          <span style={{ marginLeft: 8 }}>Sent: {new Date(inv.created_at).toLocaleDateString()}</span>
                          {inv.is_expired && <span className="badge badge-danger" style={{ marginLeft: 8 }}>Expired</span>}
                        </div>
                      </div>
                      {!inv.is_expired && (
                        <button
                          onClick={() => {
                            if (confirm(`Revoke invitation for ${inv.email}?`)) {
                              revokeMutation.mutate(inv.id);
                            }
                          }}
                          className="btn btn-danger btn-sm"
                        >
                          Revoke
                        </button>
                      )}
                    </div>
                  ))
              )}
            </div>
          )}
        </Card>
      )}

      {activeTab === "audit" && isAdmin && (
        <Card title="Audit Log">
          {auditQuery.isLoading ? (
            <LoadingSpinner />
          ) : auditQuery.isError ? (
            <ErrorBanner error={auditQuery.error as Error} />
          ) : auditQuery.data?.items.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📋</div>
              <div className="empty-state-title">No audit entries</div>
              <div className="empty-state-description">
                User activity will appear here.
              </div>
            </div>
          ) : (
            <div className="data-table-container" style={{ maxHeight: 500, overflowY: "auto" }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Action</th>
                    <th>Actor</th>
                    <th>Target</th>
                  </tr>
                </thead>
                <tbody>
                  {auditQuery.data?.items.map((entry) => (
                    <tr key={entry.id}>
                      <td style={{ fontSize: 13, color: "var(--text-muted)" }}>
                        {new Date(entry.created_at).toLocaleString()}
                      </td>
                      <td>
                        <Badge kind="plain" value={entry.action.replace(/_/g, " ")} />
                      </td>
                      <td style={{ fontSize: 13 }}>
                        {entry.actor_name || <span style={{ color: "var(--text-muted)" }}>System</span>}
                      </td>
                      <td style={{ fontSize: 13, color: "var(--text-muted)" }}>
                        {entry.target_email || entry.target_user_id || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {showInviteModal && (
        <InviteModal
          onClose={() => setShowInviteModal(false)}
          onInvite={(email, role) => inviteMutation.mutate({ email, role })}
          isLoading={inviteMutation.isPending}
          error={inviteMutation.error as Error | null}
        />
      )}
    </div>
  );
}

function InviteModal({ 
  onClose, 
  onInvite, 
  isLoading,
  error 
}: { 
  onClose: () => void; 
  onInvite: (email: string, role: string) => void;
  isLoading: boolean;
  error: Error | null;
}) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("viewer");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onInvite(email, role);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">Invite User</h3>
          <button className="modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>
        
        {error && (
          <div className="form-error" style={{ marginBottom: 16, padding: 12, background: "#fef2f2", borderRadius: 8 }}>
            {error.message}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="form-input"
              required
              placeholder="user@example.com"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Role</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="form-input"
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
            <div className="form-hint">Choose the appropriate role for this user.</div>
          </div>

          <div className="modal-footer">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={isLoading}>
              {isLoading ? <LoadingSpinner /> : "Send Invitation"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
