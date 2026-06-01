import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Table, Select, Typography, Tag, Space, Card } from "antd";
import { UnorderedListOutlined } from "@ant-design/icons";
import { getParcels } from "../api/parcels";

const statusColors: Record<string, string> = {
  received_dushanbe: "processing",
  ready_to_issue: "warning",
  issued: "success",
  problem: "error",
};
const statusLabels: Record<string, string> = {
  received_dushanbe: "В Душанбе",
  ready_to_issue: "Готова",
  issued: "Выдана",
  problem: "Проблема",
};

export default function ParcelsList() {
  const [data, setData] = useState<any>({ items: [], total: 0 });
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<string | undefined>();
  const [method, setMethod] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    const { data: d } = await getParcels({ page, per_page: 20, status, delivery_method: method });
    setData(d);
    setLoading(false);
  };

  useEffect(() => { load(); }, [page, status, method]);

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
            style={{ width: 160 }}
            value={status}
            onChange={(v) => { setStatus(v); setPage(1); }}
            options={Object.entries(statusLabels).map(([k, v]) => ({ value: k, label: v }))}
          />
          <Select
            allowClear
            placeholder="Метод"
            style={{ width: 130 }}
            value={method}
            onChange={(v) => { setMethod(v); setPage(1); }}
            options={[
              { value: "avia", label: "Авиа" },
              { value: "truck", label: "Фура" },
            ]}
          />
        </Space>
      </div>

      <div className="animate-fade-in-up">
        <Card bodyStyle={{ padding: 0 }} className="hover-card">
          <Table
            loading={loading}
            dataSource={data.items}
            rowKey="id"
            pagination={{
              current: page,
              total: data.total,
              pageSize: 20,
              onChange: setPage,
              showTotal: (total) => `Всего: ${total}`,
            }}
            columns={[
              { title: "ID", dataIndex: "id", width: 60 },
              {
                title: "Трек",
                dataIndex: "track_id",
                render: (v: string, r: any) => (
                  <Link to={`/parcels/${r.id}`} style={{ fontWeight: 600, color: "#00A76F" }}>
                    {v}
                  </Link>
                ),
              },
              { title: "Клиент ID", dataIndex: "client_id", width: 100 },
              {
                title: "Статус",
                dataIndex: "status",
                width: 130,
                render: (v: string) => (
                  <Tag color={statusColors[v]} style={{ borderRadius: 20, padding: "2px 12px" }}>
                    {statusLabels[v] || v}
                  </Tag>
                ),
              },
              {
                title: "Вес",
                dataIndex: "weight_kg",
                width: 90,
                render: (v: number) => <span style={{ fontWeight: 500 }}>{v} кг</span>,
              },
              {
                title: "Метод",
                dataIndex: "delivery_method",
                width: 90,
                render: (v: string) => (
                  <Tag color={v === "avia" ? "blue" : "orange"} style={{ borderRadius: 20 }}>
                    {v === "avia" ? "Авиа" : "Фура"}
                  </Tag>
                ),
              },
              {
                title: "Дата",
                dataIndex: "created_at",
                width: 110,
                render: (v: string) => v?.slice(0, 10),
              },
            ]}
          />
        </Card>
      </div>
    </>
  );
}
