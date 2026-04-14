import React, { useState } from "react";

type MappingIn = {
  source_key: string;
  canonical_key: string;
  value_type: "uint16" | "int16" | "uint32" | "int32" | "float32";
  register_address: number;
  register_count: number;
  scale_factor: number;
  signed: boolean;
  byte_order: "big" | "little";
  word_order: "big" | "little";
  unit?: string;
};

type Props = {
  onSubmit: (body: MappingIn) => void;
  loading?: boolean;
};

export function DeviceMappingForm({ onSubmit, loading }: Props) {
  const [sourceKey, setSourceKey] = useState("");
  const [canonicalKey, setCanonicalKey] = useState("");
  const [valueType, setValueType] = useState<MappingIn["value_type"]>("float32");
  const [address, setAddress] = useState(0);
  const [count, setCount] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [signed, setSigned] = useState(false);
  const [unit, setUnit] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      source_key: sourceKey,
      canonical_key: canonicalKey,
      value_type: valueType,
      register_address: address,
      register_count: count,
      scale_factor: scale,
      signed,
      byte_order: "big",
      word_order: "big",
      unit: unit || undefined
    });
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
      <div style={{ display: "grid", gap: 4 }}>
        <label>Source Key</label>
        <input value={sourceKey} onChange={(e) => setSourceKey(e.target.value)} placeholder="e.g. Inv_P_Total" required className="form-input" />
      </div>
      <div style={{ display: "grid", gap: 4 }}>
        <label>Canonical Key</label>
        <input value={canonicalKey} onChange={(e) => setCanonicalKey(e.target.value)} placeholder="e.g. inverter_power_kw" required className="form-input" />
      </div>
      <div style={{ display: "grid", gap: 4 }}>
        <label>Register Address</label>
        <input type="number" value={address} onChange={(e) => setAddress(parseInt(e.target.value))} required className="form-input" />
      </div>
      <div style={{ display: "grid", gap: 4 }}>
        <label>Register Count</label>
        <input type="number" value={count} onChange={(e) => setCount(parseInt(e.target.value))} required className="form-input" />
      </div>
      <div style={{ display: "grid", gap: 4 }}>
        <label>Value Type</label>
        <select value={valueType} onChange={(e) => setValueType(e.target.value as any)} className="form-input">
          <option value="uint16">uint16</option>
          <option value="int16">int16</option>
          <option value="uint32">uint32</option>
          <option value="int32">int32</option>
          <option value="float32">float32</option>
        </select>
      </div>
      <div style={{ display: "grid", gap: 4 }}>
        <label>Scale Factor</label>
        <input type="number" step="0.001" value={scale} onChange={(e) => setScale(parseFloat(e.target.value))} required className="form-input" />
      </div>
      <div style={{ display: "grid", gap: 4 }}>
        <label>Unit</label>
        <input value={unit} onChange={(e) => setUnit(e.target.value)} placeholder="e.g. kW" className="form-input" />
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 24 }}>
        <input type="checkbox" checked={signed} onChange={(e) => setSigned(e.target.checked)} id="signed-chk" />
        <label htmlFor="signed-chk">Signed</label>
      </div>
      <div style={{ gridColumn: "span 2" }}>
        <button disabled={loading} type="submit" className="btn-icon" style={{ width: "100%" }}>
          {loading ? "Adding Mapping..." : "Add Field Mapping"}
        </button>
      </div>
    </form>
  );
}
