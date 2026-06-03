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
  unresolved: { label: "Неопознанная", color: "red" },
};

const actionLabels: Record<string, string> = {
  create_parcel_china: "Добавление посылки (Китай)",
  bulk_create_parcel_china: "Массовое добавление (Китай)",
  create_parcel_dushanbe: "Добавление посылки (Душанбе)",
  update_status: "Изменение статуса",
  update_parcel: "Редактирование посылки",
  create_staff: "Создание сотрудника",
  update_staff: "Редактирование сотрудника",
  deactivate_staff: "Деактивация сотрудника",
  reset_password: "Сброс пароля",
  update_permissions: "Изменение прав доступа",
  create_tariff: "Создание тарифа",
  update_tariff: "Редактирование тарифа",
  update_client: "Редактирование клиента",
  block_client: "Блокировка клиента",
  unblock_client: "Разблокировка клиента",
  create_issuance: "Оформление выдачи",
  issue_parcels: "Оформление выдачи",
  resolve_parcel: "Привязка неопознанной посылки",
  resolve_unresolved: "Привязка неопознанной посылки",
  delete_unresolved: "Удаление неопознанной посылки",
  create_warehouse: "Создание склада",
  update_warehouse: "Редактирование склада",
  delete_warehouse: "Удаление склада",
  update_setting: "Изменение настройки",
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
          placeholder="Раздел"
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
              {
                title: "Сотрудник",
                dataIndex: "staff_name",
                width: 160,
                render: (v: string) => <span style={{ fontWeight: 500 }}>{v}</span>,
              },
              {
                title: "Действие",
                dataIndex: "action",
                render: (v: string) => (
                  <span style={{ fontWeight: 500 }}>
                    {actionLabels[v] || v}
                  </span>
                ),
              },
              {
                title: "Раздел",
                dataIndex: "entity_type",
                width: 130,
                render: (v: string) => {
                  const e = entityLabels[v];
                  return e ? (
                    <Tag color={e.color} style={{ borderRadius: 20, padding: "2px 12px" }}>
                      {e.label}
                    </Tag>
                  ) : v;
                },
              },
              {
                title: "Дата",
                dataIndex: "created_at",
                width: 170,
                render: (v: string) =>
                  v ? new Date(v).toLocaleString("ru-RU", {
                    day: "2-digit", month: "2-digit", year: "numeric",
                    hour: "2-digit", minute: "2-digit",
                  }) : "—",
              },
            ]}
          />
        </Card>
      </div>
    </>
  );
}
