import React, { useState } from "react";

type Props = {
  onSubmit: (body: { name: string; asset_type: string }) => void;
  loading?: boolean;
};

export function AssetForm({ onSubmit, loading }: Props) {
  const [name, setName] = useState("");
  const [assetType, setAssetType] = useState("battery_system");

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({ name, asset_type: assetType });
      }}
      style={{ display: "grid", gap: 8 }}
    >
      <input 
        value={name} 
        onChange={(e) => setName(e.target.value)} 
        placeholder="Asset Name (e.g. West Battery Bank)" 
        required
        className="form-input"
      />
      <select 
        value={assetType} 
        onChange={(e) => setAssetType(e.target.value)}
        className="form-input"
      >
        <option value="battery_system">Battery System</option>
        <option value="pv_system">PV System</option>
        <option value="load_center">Load Center</option>
        <option value="ev_charger">EV Charger</option>
        <option value="other">Other</option>
      </select>
      <button disabled={loading} type="submit" className="btn-icon">
        {loading ? "Creating..." : "Create Asset"}
      </button>
    </form>
  );
}
