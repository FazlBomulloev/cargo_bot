import { useEffect, useState } from "react";
import { Table, Typography, Tag, Card } from "antd";
import { getIssuances } from "../api/issuance";

export default function IssuanceHistory() {
  const [data, setData] = useState<any>({ items: [], total: 0 });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    getIssuances({ page, per_page: 20 }).then((r) => { setData(r.data); setLoading(false); });
  }, [page]);

  return (
    <>
      <div className="page-header">
        <Typography.Title className="page-title" level={3}>
          История выдач
        </Typography.Title>
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
            expandable={{
              expandedRowRender: (record: any) => (
                <Table
                  dataSource={record.items}
                  rowKey="id"
                  size="small"
                  pagination={false}
                  columns={[
                    { title: "Посылка", dataIndex: "parcel_id" },
                    { title: "Вес", dataIndex: "weight_kg", render: (v: number) => `${v} кг` },
                    { title: "Метод", dataIndex: "delivery_method" },
                    { title: "Тариф", dataIndex: "tariff_applied", render: (v: number) => `$${v}` },
                    {
                      title: "Сумма",
                      dataIndex: "amount",
                      render: (v: number) => (
                        <span style={{ fontWeight: 600, color: "#00A76F" }}>${v}</span>
                      ),
                    },
                  ]}
                />
              ),
            }}
            columns={[
              { title: "ID", dataIndex: "id", width: 60 },
              { title: "Клиент", dataIndex: "client_id", width: 100 },
              {
                title: "Вес",
                dataIndex: "total_weight",
                render: (v: number) => <span style={{ fontWeight: 500 }}>{v} кг</span>,
              },
              {
                title: "Сумма",
                dataIndex: "total_amount",
                render: (v: number) => (
                  <span style={{ fontWeight: 600, color: "#00A76F" }}>${v}</span>
                ),
              },
              {
                title: "Оплата",
                dataIndex: "payment_status",
                render: (v: string) => (
                  <Tag
                    color={v === "paid" ? "success" : "error"}
                    style={{ borderRadius: 20, padding: "2px 12px" }}
                  >
                    {v === "paid" ? "Оплачено" : "Долг"}
                  </Tag>
                ),
              },
              {
                title: "Способ",
                dataIndex: "payment_method",
                render: (v: string) => v === "cash" ? "Наличные" : v === "transfer" ? "Перевод" : "—",
              },
              {
                title: "Дата",
                dataIndex: "issued_at",
                render: (v: string) => v?.slice(0, 10),
              },
            ]}
          />
        </Card>
      </div>
    </>
  );
}
