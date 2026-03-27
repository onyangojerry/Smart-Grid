import React, { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getSiteDevices, createSiteDevice, getSiteAssets, createAsset, deleteAsset } from "../../api/devices";
import { queryKeys } from "../../api/queryKeys";
import { PageHeader } from "../../components/layout/PageHeader";
import { Card } from "../../components/ui/Card";
import { DataTable } from "../../components/tables/DataTable";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { EmptyState } from "../../components/ui/EmptyState";
import { DeviceForm } from "../../components/forms/DeviceForm";
import { AssetForm } from "../../components/forms/AssetForm";
import { formatTimestamp } from "../../utils/time";
import "../../styles/features.css";

export function DevicesPage() {
  const { siteId } = useParams();
  const qc = useQueryClient();
  const [openCreateDevice, setOpenCreateDevice] = useState(false);
  const [openCreateAsset, setOpenCreateAsset] = useState(false);

  if (!siteId) return <ErrorBanner error={new Error("Missing siteId")} />;

  const devicesQuery = useQuery({
    queryKey: queryKeys.devices(siteId),
    queryFn: () => getSiteDevices(siteId)
  });

  const assetsQuery = useQuery({
    queryKey: queryKeys.assets(siteId),
    queryFn: () => getSiteAssets(siteId)
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
                    <button 
                      onClick={() => deleteAssetMutation.mutate(a.id)} 
                      style={{ color: "var(--error)", border: "none", background: "none", cursor: "pointer" }}
                    >
                      Delete
                    </button>
                  ) 
                }
              ]}
            />
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
                { key: "id", header: "Device ID", render: (d) => d.id },
                { key: "type", header: "Type", render: (d) => d.device_type },
                { key: "protocol", header: "Protocol", render: (d) => d.protocol },
                { key: "created", header: "Added", render: (d) => formatTimestamp(d.created_at) }
              ]}
            />
          )}
        </Card>
      </div>

      <Card title="Advanced Configuration">
        <div className="deferred-box">
          <div style={{ fontWeight: 600, marginBottom: 8 }}>Available Advanced Features:</div>
          <ul style={{ margin: 0, paddingLeft: 20, display: "grid", gap: 4 }}>
            <li>Direct Asset-Device assignment (Implemented)</li>
            <li>Custom Canonical Key Mappings (Implemented)</li>
          </ul>
          <div style={{ marginTop: 12, fontSize: 13, color: "var(--text-muted)" }}>
            UI for granular device-to-asset binding and field mapping is under development. Use the API directly for advanced scenarios.
          </div>
        </div>
      </Card>
    </div>
  );
}
