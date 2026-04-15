import React, { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { 
  getSiteDevices, createSiteDevice, getSiteAssets, createAsset, deleteAsset,
  getDeviceMappings, createDeviceMapping, deleteDeviceMapping, createAssetDevice
} from "../../api/devices";
import { queryKeys } from "../../api/queryKeys";
import { PageHeader } from "../../components/layout/PageHeader";
import { Card } from "../../components/ui/Card";
import { DataTable } from "../../components/tables/DataTable";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { EmptyState } from "../../components/ui/EmptyState";
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
    mutationFn: (body: import("../../types").DeviceCreateBody) => createSiteDevice(siteId, body),
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

  if (devicesQuery.isLoading || assetsQuery.isLoading) return <LoadingSpinner />;
  
  return (
    <div className="page-content">
      <PageHeader 
        title="Devices & Assets" 
        subtitle={siteId} 
        right={
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={() => setOpenCreateAsset((v) => !v)} className="btn-icon">
              {openCreateAsset ? "Cancel Asset" : "Add Asset"}
            </button>
            <button onClick={() => setOpenCreateDevice((v) => !v)} className="btn-icon">
              {openCreateDevice ? "Cancel Device" : "Add Device"}
            </button>
          </div>
        }
      />

      {openCreateAsset && (
        <Card title="Add new asset">
          <AssetForm onSubmit={(body) => createAssetMutation.mutate(body)} loading={createAssetMutation.isPending} />
        </Card>
      )}

      {openCreateDevice && (
        <Card title="Add new device">
          <DeviceForm onSubmit={(body) => createDeviceMutation.mutate(body)} loading={createDeviceMutation.isPending} />
        </Card>
      )}

      <div style={{ display: "grid", gap: 20 }}>
        <Card title="Site Assets">
          {assetsQuery.isError ? (
            <ErrorBanner error={assetsQuery.error as Error} message="Failed to load site assets. Please try again later." />
          ) : !assetsQuery.data?.length ? (
            <EmptyState title="No assets found" description="Create your first asset to organize devices." />
          ) : (
            <>
              <DataTable
                rows={assetsQuery.data}
                getRowKey={(a) => a.id}
                columns={[
                  { key: "name", header: "Name", render: (a) => a.name },
                  { key: "type", header: "Type", render: (a) => a.asset_type },
                  { key: "created", header: "Added", render: (a) => formatTimestamp(a.created_at) },
                  { 
                    key: "actions", 
                    header: "", 
                    render: (a) => (
                      <div style={{ display: "flex", gap: 8 }}>
                        <button 
                          onClick={() => setBindingAssetId(a.id)}
                          style={{ color: "var(--primary)", border: "none", background: "none", cursor: "pointer" }}
                        >
                          Bind Device
                        </button>
                        <button 
                          onClick={() => deleteAssetMutation.mutate(a.id)} 
                          style={{ color: "var(--error)", border: "none", background: "none", cursor: "pointer" }}
                        >
                          Delete
                        </button>
                      </div>
                    ) 
                  }
                ]}
              />
              {bindingAssetId && (
                <div style={{ marginTop: 16, padding: 16, border: "1px solid var(--border)", borderRadius: 8 }}>
                  <div style={{ marginBottom: 12, fontWeight: 600 }}>Bind Device to {assetsQuery.data.find(a => a.id === bindingAssetId)?.name}</div>
                  <AssetDeviceBindingForm 
                    devices={devicesQuery.data || []} 
                    onSubmit={(deviceId) => bindDeviceMutation.mutate(deviceId)}
                    loading={bindDeviceMutation.isPending}
                  />
                  <button onClick={() => setBindingAssetId(null)} className="btn-icon" style={{ marginTop: 8, background: "none", color: "var(--text-muted)" }}>
                    Cancel
                  </button>
                </div>
              )}
            </>
          )}
        </Card>

        <Card title="Connected Devices">
          {devicesQuery.isError ? (
            <ErrorBanner error={devicesQuery.error as Error} />
          ) : !devicesQuery.data?.length ? (
            <EmptyState title="No devices found" description="Add your first device to this site." />
          ) : (
            <DataTable
              rows={devicesQuery.data}
              getRowKey={(d) => d.id}
              columns={[
                { key: "id", header: "Device ID", render: (d) => <code style={{ cursor: "pointer", color: "var(--primary)" }} onClick={() => setSelectedDeviceId(d.id)}>{d.id.slice(0, 8)}</code> },
                { key: "type", header: "Type", render: (d) => d.device_type },
                { key: "protocol", header: "Protocol", render: (d) => d.protocol },
                { key: "created", header: "Added", render: (d) => formatTimestamp(d.created_at) },
                {
                  key: "mappings",
                  header: "",
                  render: (d) => (
                    <button onClick={() => setSelectedDeviceId(d.id)} className="btn-icon">
                      Mappings
                    </button>
                  )
                }
              ]}
            />
          )}
        </Card>

        {selectedDeviceId && (
          <Card title={`Field Mappings: ${selectedDeviceId.slice(0, 8)}`}>
            <div style={{ display: "grid", gap: 20 }}>
              <div style={{ background: "var(--bg-muted)", padding: 16, borderRadius: 8 }}>
                <div style={{ marginBottom: 12, fontWeight: 600 }}>Add New Mapping</div>
                <DeviceMappingForm 
                  onSubmit={(body) => createMappingMutation.mutate(body)} 
                  loading={createMappingMutation.isPending} 
                />
              </div>

              {mappingsQuery.isLoading ? (
                <LoadingSpinner />
              ) : mappingsQuery.data?.items?.length ? (
                <DataTable
                  rows={mappingsQuery.data.items}
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
                        <button 
                          onClick={() => deleteMappingMutation.mutate(m.id)} 
                          style={{ color: "var(--error)", border: "none", background: "none", cursor: "pointer" }}
                        >
                          Remove
                        </button>
                      )
                    }
                  ]}
                />
              ) : (
                <EmptyState title="No mappings defined" description="Add field mappings to decode Modbus data." />
              )}
              
              <button onClick={() => setSelectedDeviceId(null)} className="btn-icon" style={{ justifySelf: "start" }}>
                Close Mappings
              </button>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
