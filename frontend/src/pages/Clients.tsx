import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Table, Input, Typography, Tag, Card } from "antd";
import { getClients } from "../api/clients";

export default function Clients() {
  const [data, setData] = useState<any>({ items: [], total: 0 });
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    getClients({ page, per_page: 20, q: search || undefined }).then((r) => { setData(r.data); setLoading(false); });
  }, [page, search]);

  return (
    <>
      <div className="page-header">
        <Typography.Title className="page-title" level={3}>
          Клиенты
        </Typography.Title>
        <Input.Search
          placeholder="Поиск по TPS / телефону / ФИО"
          style={{ maxWidth: 360 }}
          onSearch={(v) => { setSearch(v); setPage(1); }}
          allowClear
          size="large"
        />
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
              {
                title: "TPS",
                dataIndex: "tps_code",
                width: 100,
                render: (v: string, r: any) => (
                  <Link to={`/clients/${r.id}`} style={{ fontWeight: 600, color: "#00A76F" }}>
                    {v}
                  </Link>
                ),
              },
              { title: "ФИО", dataIndex: "full_name" },
              { title: "Телефон", dataIndex: "phone", width: 160 },
              {
                title: "Регистрация",
                dataIndex: "created_at",
                width: 120,
                render: (v: string) => v?.slice(0, 10),
              },
            ]}
          />
        </Card>
      </div>
    </>
  );
}
