import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Table, Select, Typography, Tag, Space, Card } from "antd";
import { getAllParcels } from "../api/parcels";

const statusColors: Record<string, string> = {
  in_china: "cyan",
  received_dushanbe: "processing",
  issued: "success",
  problem: "error",
  unresolved: "warning",
};
const statusLabels: Record<string, string> = {
  in_china: "В Китае",
  received_dushanbe: "В Душанбе",
  issued: "Получена",
  problem: "Проблема",
  unresolved: "Неопознанные",
};

export default function ParcelsList() {
  const [data, setData] = useState<any>({ items: [], total: 0 });
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const { data: d } = await getAllParcels({ page, per_page: 20, status });
      setData(d);
    } catch {
      setData({ items: [], total: 0 });
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, [page, status]);

  return (
    <>
      <div className="page-header">
        <Typography.Title className="page-title" level={3}>
          Все посылки
        </Typography.Title>
        <Space>
          <Select
            allowClear
            placeholder="Статус"
            style={{ width: 180 }}
            value={status}
            onChange={(v) => { setStatus(v); setPage(1); }}
            options={Object.entries(statusLabels).map(([k, v]) => ({ value: k, label: v }))}
          />
        </Space>
      </div>

      <div className="animate-fade-in-up">
        <Card bodyStyle={{ padding: 0 }} className="hover-card">
          <Table
            loading={loading}
            dataSource={data.items}
            rowKey={(r) => `${r.status === "in_china" ? "c" : "d"}_${r.id}`}
            pagination={{
              current: page,
              total: data.total,
              pageSize: 20,
              onChange: setPage,
              showTotal: (total) => `Всего: ${total}`,
            }}
            columns={[
              {
                title: "Трек",
                dataIndex: "track_id",
                render: (v: string, r: any) =>
                  r.status !== "in_china" ? (
                    <Link to={`/parcels/${r.id}`} style={{ fontFamily: "monospace", fontWeight: 600, color: "#00A76F" }}>
                      {v}
                    </Link>
                  ) : (
                    <span style={{ fontFamily: "monospace", fontWeight: 600 }}>{v}</span>
                  ),
              },
              {
                title: "Клиент",
                dataIndex: "client_name",
                render: (v: string, r: any) =>
                  v ? (
                    <span>
                      <span style={{ fontWeight: 500 }}>{v}</span>
                      <span style={{ color: "#919EAB", marginLeft: 8, fontSize: 12 }}>{r.tps_code}</span>
                    </span>
                  ) : (
                    <span style={{ color: "#919EAB" }}>—</span>
                  ),
              },
              {
                title: "Статус",
                dataIndex: "status",
                width: 140,
                render: (v: string) => (
                  <Tag color={statusColors[v] || "default"} style={{ borderRadius: 20, padding: "2px 12px" }}>
                    {statusLabels[v] || v}
                  </Tag>
                ),
              },
              {
                title: "Вес",
                dataIndex: "weight_kg",
                width: 90,
                render: (v: number | null) =>
                  v != null ? <span style={{ fontWeight: 500 }}>{v} кг</span> : <span style={{ color: "#919EAB" }}>—</span>,
              },
              {
                title: "Метод",
                dataIndex: "delivery_method",
                width: 90,
                render: (v: string | null) =>
                  v ? (
                    <Tag color={v === "avia" ? "blue" : "orange"} style={{ borderRadius: 20 }}>
                      {v === "avia" ? "Авиа" : "Фура"}
                    </Tag>
                  ) : (
                    <span style={{ color: "#919EAB" }}>—</span>
                  ),
              },
              {
                title: "Дата",
                dataIndex: "created_at",
                width: 160,
                render: (v: string) =>
                  v
                    ? new Date(v).toLocaleString("ru-RU", {
                        day: "2-digit", month: "2-digit", year: "numeric",
                        hour: "2-digit", minute: "2-digit",
                      })
                    : "—",
              },
            ]}
          />
        </Card>
      </div>
    </>
  );
}
