import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, Link } from "react-router-dom";
import { createSite, getSites } from "../../api/sites";
import { queryKeys } from "../../api/queryKeys";
import { PageHeader } from "../../components/layout/PageHeader";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { SiteForm } from "../../components/forms/SiteForm";
import { DataTable } from "../../components/tables/DataTable";
import { formatTimestamp } from "../../utils/time";
import "../../styles/features.css";

export function SitesPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [openCreate, setOpenCreate] = useState(false);

  const sitesQuery = useQuery({ queryKey: queryKeys.sites(), queryFn: getSites });
  const createMutation = useMutation({
    mutationFn: createSite,
    onSuccess: (created) => {
      qc.invalidateQueries({ queryKey: queryKeys.sites() });
      setOpenCreate(false);
      navigate(`/sites/${created.id}`);
    }
  });

  if (sitesQuery.isLoading) return <LoadingSpinner />;
  if (sitesQuery.isError) return <ErrorBanner error={sitesQuery.error} onRetry={() => sitesQuery.refetch()} />;

  const rows = sitesQuery.data || [];
  return (
    <div className="page-content">
      <PageHeader title="Sites" right={<button onClick={() => setOpenCreate((v) => !v)} className="btn-icon">{openCreate ? "Close" : "New site"}</button>} />
      {openCreate ? (
        <Card title="Create site">
          <SiteForm onSubmit={(body) => createMutation.mutate(body)} loading={createMutation.isPending} />
        </Card>
      ) : null}
      {!rows.length ? (
        <EmptyState title="No sites found" description="Create your first site to start operations." />
      ) : (
        <Card>
          <DataTable
            rows={rows}
            getRowKey={(r) => r.id}
            columns={[
              { key: "name", header: "Name", render: (r) => <Link to={`/sites/${r.id}`}>{r.name}</Link> },
              { key: "timezone", header: "Timezone", render: (r) => r.timezone },
              { key: "reserve", header: "Reserve SOC min", render: (r) => `${r.reserve_soc_min}%` },
              { key: "created", header: "Created", render: (r) => formatTimestamp(r.created_at) }
            ]}
          />
        </Card>
      )}
    </div>
  );
}
