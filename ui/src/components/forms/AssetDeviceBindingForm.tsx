import React, { useState } from "react";
import type { Device } from "../../types";

type Props = {
  devices: Device[];
  onSubmit: (deviceId: string) => void;
  loading?: boolean;
};

export function AssetDeviceBindingForm({ devices, onSubmit, loading }: Props) {
  const [selectedDevice, setSelectedDevice] = useState(devices[0]?.id || "");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedDevice) {
      onSubmit(selectedDevice);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
      <div style={{ display: "grid", gap: 4, flex: 1 }}>
        <label>Select Device to Bind</label>
        <select 
          value={selectedDevice} 
          onChange={(e) => setSelectedDevice(e.target.value)}
          className="form-input"
          required
        >
          <option value="" disabled>-- Select Device --</option>
          {devices.map((d) => (
            <option key={d.id} value={d.id}>
              {d.device_type} ({d.id.slice(0, 8)})
            </option>
          ))}
        </select>
      </div>
      <button disabled={loading || !selectedDevice} type="submit" className="btn-icon">
        {loading ? "Binding..." : "Bind Device"}
      </button>
    </form>
  );
}
