import { useEffect, useState } from "react";
import { Table, Select, Typography, Space, Card, Tag } from "antd";
import { getAuditLogs } from "../api/audit";

const entityLabels: Record<string, { label: string; color: string }> = {
  parcel: { label: "Посылка", color: "blue" },
  client: { label: "Клиент", color: "green" },
  staff: { label: "Сотрудник", color: "purple" },
  tariff: { label: "Тариф", color: "orange" },
  warehouse: { label: "Склад", color: "cyan" },
  setting: { label: "Настройка", color: "gold" },
  issuance: { label: "Выдача", color: "lime" },
  unresolved: { label: "Проблемная", color: "red" },
};

export default function AuditLog() {
  const [data, setData] = useState<any>({ items: [], total: 0 });
  const [page, setPage] = useState(1);
  const [entityType, setEntityType] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    getAuditLogs({ page, per_page: 50, entity_type: entityType }).then((r) => { setData(r.data); setLoading(false); });
  }, [page, entityType]);

  return (
    <>
      <div className="page-header">
        <Typography.Title className="page-title" level={3}>
          Журнал действий
        </Typography.Title>
        <Select
          allowClear
          placeholder="Тип объекта"
          style={{ width: 180 }}
          value={entityType}
          onChange={(v) => { setEntityType(v); setPage(1); }}
          options={Object.entries(entityLabels).map(([k, v]) => ({ value: k, label: v.label }))}
        />
      </div>

      <div className="animate-fade-in-up">
        <Card bodyStyle={{ padding: 0 }} className="hover-card">
          <Table
            loading={loading}
            dataSource={data.items}
            rowKey="id"
            size="small"
            pagination={{
              current: page,
              total: data.total,
              pageSize: 50,
              onChange: setPage,
              showTotal: (total) => `Всего: ${total}`,
            }}
            columns={[
              { title: "ID", dataIndex: "id", width: 60 },
              { title: "Сотрудник", dataIndex: "staff_id", width: 100 },
              {
                title: "Действие",
                dataIndex: "action",
                render: (v: string) => <span style={{ fontWeight: 500 }}>{v}</span>,
              },
              {
                title: "Тип",
                dataIndex: "entity_type",
                width: 120,
                render: (v: string) => {
                  const e = entityLabels[v];
                  return e ? (
                    <Tag color={e.color} style={{ borderRadius: 20, padding: "2px 12px" }}>
                      {e.label}
                    </Tag>
                  ) : v;
                },
              },
              { title: "Объект", dataIndex: "entity_id", width: 80 },
              {
                title: "IP",
                dataIndex: "ip_address",
                width: 130,
                render: (v: string) => (
                  <span style={{ fontFamily: "monospace", fontSize: 13, color: "#637381" }}>{v}</span>
                ),
              },
              { title: "Дата", dataIndex: "created_at", width: 170 },
            ]}
          />
        </Card>
      </div>
    </>
  );
}
