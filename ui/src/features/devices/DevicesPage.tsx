import React, { useState, useMemo } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, useScroll, useTransform } from "framer-motion";
import { 
  getSiteDevices, createSiteDevice, getSiteAssets, createAsset, deleteAsset,
  getDeviceMappings, createDeviceMapping, deleteDeviceMapping, createAssetDevice
} from "../../api/devices";
import { queryKeys } from "../../api/queryKeys";
import { DataTable } from "../../components/tables/DataTable";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { DeviceForm } from "../../components/forms/DeviceForm";
import { AssetForm } from "../../components/forms/AssetForm";
import { DeviceMappingForm } from "../../components/forms/DeviceMappingForm";
import { AssetDeviceBindingForm } from "../../components/forms/AssetDeviceBindingForm";
import { formatTimestamp } from "../../utils/time";
import "../../styles/features.css";

export function DevicesPage() {
  const { siteId } = useParams();
  const qc = useQueryClient();
  const [openCreateDevice, setOpenCreateDevice] = useState(false);
  const [openCreateAsset, setOpenCreateAsset] = useState(false);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
  const [bindingAssetId, setBindingAssetId] = useState<string | null>(null);

  const { scrollYProgress } = useScroll();
  const opacities = [
    useTransform(scrollYProgress, [0, 0.25], [1, 0]),
    useTransform(scrollYProgress, [0.25, 0.5, 0.75], [0, 1, 0]),
    useTransform(scrollYProgress, [0.75, 1], [0, 1]),
  ];

  if (!siteId) return <ErrorBanner error={new Error("Missing siteId")} />;

  const devicesQuery = useQuery({
    queryKey: queryKeys.devices(siteId),
    queryFn: () => getSiteDevices(siteId)
  });

  const assetsQuery = useQuery({
    queryKey: queryKeys.assets(siteId),
    queryFn: () => getSiteAssets(siteId)
  });

  const mappingsQuery = useQuery({
    queryKey: ["device-mappings", selectedDeviceId],
    queryFn: () => getDeviceMappings(selectedDeviceId!),
    enabled: !!selectedDeviceId
  });

  const createDeviceMutation = useMutation({
    mutationFn: (body: any) => createSiteDevice(siteId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.devices(siteId) });
      setOpenCreateDevice(false);
    }
  });

  const createAssetMutation = useMutation({
    mutationFn: (body: { name: string; asset_type: string }) => createAsset(siteId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.assets(siteId) });
      setOpenCreateAsset(false);
    }
  });

  const deleteAssetMutation = useMutation({
    mutationFn: deleteAsset,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.assets(siteId) });
    }
  });

  const createMappingMutation = useMutation({
    mutationFn: (body: any) => createDeviceMapping(selectedDeviceId!, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["device-mappings", selectedDeviceId] });
    }
  });

  const deleteMappingMutation = useMutation({
    mutationFn: deleteDeviceMapping,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["device-mappings", selectedDeviceId] });
    }
  });

  const bindDeviceMutation = useMutation({
    mutationFn: (deviceId: string) => createAssetDevice(bindingAssetId!, { device_id: deviceId }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.assets(siteId) });
      setBindingAssetId(null);
    }
  });

  const images = [
    "https://images.unsplash.com/photo-1558449028-b53a39d100fc?auto=format&fit=crop&q=80&w=2000", // Hardware/Devices
    "https://images.unsplash.com/photo-1581092160562-40aa08e78837?auto=format&fit=crop&q=80&w=2000", // Industrial Tech
    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&q=80&w=2000", // Microchip/Logic
  ];

  if (devicesQuery.isLoading || assetsQuery.isLoading) return <LoadingSpinner />;

  return (
    <div className="scrolly-container">
      <div className="scrolly-stage">
        {images.map((src, i) => (
          <motion.img key={src} src={src} className="stage-image" style={{ opacity: opacities[i] }} />
        ))}
        <div className="stage-overlay" />
        <div className="scroll-hint">Asset Management Discovery</div>
      </div>

      <div className="scrolly-story">
        <section className="story-section center">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1 }}
            className="story-content-narrative"
          >
            <h1 className="story-title">Devices & Assets</h1>
            <p className="story-subtitle">The physical foundation for {siteId}</p>
            <p className="story-body">
              Behind every intelligent decision is a physical asset. From high-capacity batteries to precision meters, your hardware is the bridge between digital logic and physical power.
            </p>
            <div style={{ display: "flex", gap: "1rem", justifyContent: "center", marginTop: "2rem" }}>
              <button onClick={() => setOpenCreateAsset((v) => !v)} className="btn btn-primary">{openCreateAsset ? "Cancel Asset" : "Add Asset"}</button>
              <button onClick={() => setOpenCreateDevice((v) => !v)} className="btn btn-secondary">{openCreateDevice ? "Cancel Device" : "Add Device"}</button>
            </div>
          </motion.div>
        </section>

        {(openCreateAsset || openCreateDevice) && (
          <section className="story-section">
            <div className="story-content-narrative" style={{ maxWidth: "800px", margin: "0 auto" }}>
              {openCreateAsset && (
                <div style={{ background: "rgba(255,255,255,0.1)", padding: "2rem", borderRadius: "1rem", backdropFilter: "blur(10px)", marginBottom: "2rem" }}>
                  <h3 style={{ marginBottom: "1.5rem" }}>Create New Asset</h3>
                  <AssetForm onSubmit={(body) => createAssetMutation.mutate(body)} loading={createAssetMutation.isPending} />
                </div>
              )}
              {openCreateDevice && (
                <div style={{ background: "rgba(255,255,255,0.1)", padding: "2rem", borderRadius: "1rem", backdropFilter: "blur(10px)" }}>
                  <h3 style={{ marginBottom: "1.5rem" }}>Register New Device</h3>
                  <DeviceForm onSubmit={(body) => createDeviceMutation.mutate(body)} loading={createDeviceMutation.isPending} />
                </div>
              )}
            </div>
          </section>
        )}

        <section className="story-section">
          <div className="story-content-narrative" style={{ maxWidth: "100%", width: "100%" }}>
            <h2 className="story-title" style={{ fontSize: "2.5rem" }}>Site Assets</h2>
            <div style={{ background: "rgba(0,0,0,0.4)", padding: "2rem", borderRadius: "1rem", backdropFilter: "blur(10px)", marginTop: "2rem" }}>
              {assetsQuery.isError ? (
                <ErrorBanner error={assetsQuery.error as Error} />
              ) : (
                <DataTable
                  rows={assetsQuery.data || []}
                  getRowKey={(a) => a.id}
                  columns={[
                    { key: "name", header: "Name", render: (a) => <span style={{ color: "white", fontWeight: 700 }}>{a.name}</span> },
                    { key: "type", header: "Type", render: (a) => a.asset_type },
                    { key: "created", header: "Added", render: (a) => formatTimestamp(a.created_at) },
                    { 
                      key: "actions", 
                      header: "", 
                      render: (a) => (
                        <div style={{ display: "flex", gap: 12 }}>
                          <button onClick={() => setBindingAssetId(a.id)} className="btn btn-sm btn-secondary">Bind Device</button>
                          <button onClick={() => deleteAssetMutation.mutate(a.id)} className="btn btn-sm btn-danger">Delete</button>
                        </div>
                      ) 
                    }
                  ]}
                />
              )}
              {bindingAssetId && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} style={{ marginTop: "2rem", padding: "1.5rem", border: "1px solid rgba(255,255,255,0.2)", borderRadius: "1rem" }}>
                  <div style={{ marginBottom: "1rem", fontWeight: 700 }}>Bind Device to {assetsQuery.data?.find(a => a.id === bindingAssetId)?.name}</div>
                  <AssetDeviceBindingForm 
                    devices={devicesQuery.data || []} 
                    onSubmit={(deviceId) => bindDeviceMutation.mutate(deviceId)}
                    loading={bindDeviceMutation.isPending}
                  />
                  <button onClick={() => setBindingAssetId(null)} className="btn btn-sm btn-secondary" style={{ marginTop: "1rem" }}>Cancel</button>
                </motion.div>
              )}
            </div>
          </div>
        </section>

        <section className="story-section" style={{ minHeight: "150vh" }}>
          <div className="story-content-narrative" style={{ maxWidth: "100%", width: "100%" }}>
            <h2 className="story-title" style={{ fontSize: "2.5rem" }}>Connected Devices</h2>
            <div style={{ background: "rgba(0,0,0,0.4)", padding: "2rem", borderRadius: "1rem", backdropFilter: "blur(10px)", marginTop: "2rem" }}>
              <DataTable
                rows={devicesQuery.data || []}
                getRowKey={(d) => d.id}
                columns={[
                  { key: "id", header: "Device ID", render: (d) => <code style={{ color: "var(--primary)" }}>{d.id.slice(0, 8)}</code> },
                  { key: "type", header: "Type", render: (d) => d.device_type },
                  { key: "protocol", header: "Protocol", render: (d) => d.protocol },
                  { key: "created", header: "Added", render: (d) => formatTimestamp(d.created_at) },
                  {
                    key: "mappings",
                    header: "",
                    render: (d) => (
                      <button onClick={() => setSelectedDeviceId(d.id)} className="btn btn-sm btn-primary">
                        Mappings
                      </button>
                    )
                  }
                ]}
              />
            </div>

            {selectedDeviceId && (
              <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} style={{ marginTop: "3rem", background: "rgba(0,0,0,0.5)", padding: "2rem", borderRadius: "1rem", backdropFilter: "blur(20px)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
                  <h3 className="story-title" style={{ fontSize: "2rem", margin: 0 }}>Field Mappings: {selectedDeviceId.slice(0, 8)}</h3>
                  <button onClick={() => setSelectedDeviceId(null)} className="btn btn-secondary">Close Mappings</button>
                </div>
                
                <div style={{ background: "rgba(255,255,255,0.05)", padding: "1.5rem", borderRadius: "1rem", marginBottom: "2rem" }}>
                  <div style={{ marginBottom: "1rem", fontWeight: 700 }}>Add New Mapping</div>
                  <DeviceMappingForm onSubmit={(body) => createMappingMutation.mutate(body)} loading={createMappingMutation.isPending} />
                </div>

                {mappingsQuery.isLoading ? <LoadingSpinner /> : (
                  <DataTable
                    rows={mappingsQuery.data?.items || []}
                    getRowKey={(m) => m.id}
                    columns={[
                      { key: "canonical", header: "Canonical Key", render: (m) => <code>{m.canonical_key}</code> },
                      { key: "source", header: "Source Key", render: (m) => m.source_key },
                      { key: "addr", header: "Address", render: (m) => m.register_address },
                      { key: "type", header: "Type", render: (m) => m.value_type },
                      { key: "unit", header: "Unit", render: (m) => m.unit || "-" },
                      {
                        key: "actions",
                        header: "",
                        render: (m) => (
                          <button onClick={() => deleteMappingMutation.mutate(m.id)} className="btn btn-sm btn-danger">Remove</button>
                        )
                      }
                    ]}
                  />
                )}
              </motion.div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
