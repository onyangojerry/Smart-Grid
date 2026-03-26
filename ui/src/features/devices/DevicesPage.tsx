import React from "react";
import { useParams } from "react-router-dom";
import { PageHeader } from "../../components/layout/PageHeader";
import { Card } from "../../components/ui/Card";
import "../../styles/features.css";

export function DevicesPage() {
  const { siteId } = useParams();
  return (
    <div className="page-content">
      <PageHeader title="Devices" subtitle={siteId} />
      <Card title="Status">
        <div className="deferred-box">
          <div style={{ fontWeight: 600, marginBottom: 8 }}>The following Device Management endpoints are currently DEFERRED:</div>
          <ul style={{ margin: 0, paddingLeft: 20, display: "grid", gap: 4 }}>
            <li>`POST /api/v1/sites/{site_id}/assets`</li>
            <li>`POST /api/v1/assets/{'{asset_id}'}/devices`</li>
            <li>`GET /api/v1/sites/{site_id}/devices`</li>
            <li>`POST /api/v1/devices/{'{device_id}'}/mappings`</li>
          </ul>
        </div>
      </Card>
    </div>
  );
}
