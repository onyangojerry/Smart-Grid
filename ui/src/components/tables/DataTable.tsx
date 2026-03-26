import React from "react";

export type Column<T> = {
  key: string;
  header: string;
  render: (row: T) => React.ReactNode;
};

type DataTableProps<T> = {
  rows: T[];
  columns: Column<T>[];
  getRowKey: (row: T) => string;
};

export function DataTable<T>({ rows, columns, getRowKey }: DataTableProps<T>) {
  return (
    <table style={{ width: "100%", borderCollapse: "collapse", background: "var(--card-bg)", color: "var(--text)" }}>
      <thead>
        <tr>
          {columns.map((col) => (
            <th key={col.key} style={{ textAlign: "left", padding: 10, borderBottom: "1px solid var(--border)", fontSize: 13, color: "var(--text-muted)" }}>
              {col.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={getRowKey(row)}>
            {columns.map((col) => (
              <td key={col.key} style={{ padding: 10, borderBottom: "1px solid var(--border)", fontSize: 14 }}>
                {col.render(row)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
