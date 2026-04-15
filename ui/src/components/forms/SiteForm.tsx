import React, { useState } from "react";
import type { SiteCreateBody } from "../../types";

type Props = {
  onSubmit: (body: SiteCreateBody) => void;
  loading?: boolean;
};

export function SiteForm({ onSubmit, loading }: Props) {
  const [name, setName] = useState("");
  const [timezone, setTimezone] = useState("UTC");

  return (
    <form
      className="auth-form"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({
          site_id: `site_${Date.now()}`,
          name,
          timezone,
          reserve_soc_min: 20,
          polling_interval_seconds: 300
        });
      }}
      style={{ maxWidth: 400 }}
    >
      <div className="form-group">
        <label className="form-label">Site Name</label>
        <input 
          className="form-input"
          required 
          placeholder="e.g. West Facility or Main Residence" 
          value={name} 
          onChange={(e) => setName(e.target.value)} 
        />
      </div>
      <div className="form-group">
        <label className="form-label">Timezone</label>
        <input 
          className="form-input"
          required 
          placeholder="e.g. Australia/Sydney" 
          value={timezone} 
          onChange={(e) => setTimezone(e.target.value)} 
        />
      </div>
      <button className="btn btn-primary" disabled={loading} type="submit" style={{ marginTop: 8 }}>
        {loading ? "Creating..." : "Add New Site"}
      </button>
    </form>
  );
}
