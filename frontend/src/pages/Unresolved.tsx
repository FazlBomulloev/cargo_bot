import { useEffect, useState } from "react";
import { Table, Button, Input, Modal, message, Typography, Tag, Card, Space } from "antd";
import { WarningOutlined, LinkOutlined, DeleteOutlined } from "@ant-design/icons";
import { getUnresolved, resolveParcel, deleteUnresolved } from "../api/unresolved";

export default function Unresolved() {
  const [items, setItems] = useState<any[]>([]);
  const [resolveId, setResolveId] = useState<number | null>(null);
  const [tpsCode, setTpsCode] = useState("");

  const load = () => getUnresolved().then((r) => setItems(r.data));
  useEffect(() => { load(); }, []);

  const handleResolve = async () => {
    if (!tpsCode.trim()) return;
    try {
      await resolveParcel(resolveId!, tpsCode.trim());
      message.success("Посылка привязана к клиенту");
      setResolveId(null); setTpsCode(""); load();
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка");
    }
  };

  const handleDelete = async (id: number) => {
    await deleteUnresolved(id);
    message.success("Удалено");
    load();
  };

  return (
    <>
      <div className="page-header">
        <Typography.Title className="page-title" level={3}>
          Проблемные посылки
        </Typography.Title>
        {items.length > 0 && (
          <Tag
            color="error"
            style={{
              borderRadius: 20,
              padding: "4px 16px",
              fontSize: 14,
              fontWeight: 600,
            }}
          >
            <WarningOutlined /> {items.length} шт.
          </Tag>
        )}
      </div>

      <div className="animate-fade-in-up">
        <Card bodyStyle={{ padding: 0 }} className="hover-card">
          <Table
            dataSource={items}
            rowKey="id"
            columns={[
              {
                title: "Трек",
                dataIndex: "track_id",
                render: (v: string) => (
                  <span style={{ fontFamily: "monospace", fontWeight: 600 }}>{v}</span>
                ),
              },
              {
                title: "TPS (введённый)",
                dataIndex: "raw_tps_code",
                render: (v: string) => (
                  <Tag color="error" style={{ borderRadius: 20, padding: "2px 12px" }}>{v}</Tag>
                ),
              },
              {
                title: "Вес",
                dataIndex: "weight_kg",
                render: (v: number) => v ? `${v} кг` : "—",
              },
              {
                title: "Метод",
                dataIndex: "delivery_method",
                render: (v: string) => v ? (
                  <Tag color={v === "avia" ? "blue" : "orange"} style={{ borderRadius: 20 }}>
                    {v === "avia" ? "Авиа" : "Фура"}
                  </Tag>
                ) : "—",
              },
              { title: "Дата", dataIndex: "created_at", render: (v: string) => v?.slice(0, 10) },
              {
                title: "Действия",
                width: 200,
                render: (_: any, r: any) => (
                  <Space>
                    <Button
                      size="small"
                      type="primary"
                      icon={<LinkOutlined />}
                      onClick={() => setResolveId(r.id)}
                      style={{ borderRadius: 8 }}
                    >
                      Привязать
                    </Button>
                    <Button
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => handleDelete(r.id)}
                      style={{ borderRadius: 8 }}
                    />
                  </Space>
                ),
              },
            ]}
          />
        </Card>
      </div>

      <Modal
        title="Привязать к клиенту"
        open={resolveId !== null}
        onOk={handleResolve}
        onCancel={() => setResolveId(null)}
        okText="Привязать"
        cancelText="Отмена"
      >
        <Input
          placeholder="Правильный TPS-код"
          value={tpsCode}
          onChange={(e) => setTpsCode(e.target.value)}
          style={{ borderRadius: 12, height: 44 }}
          size="large"
        />
      </Modal>
    </>
  );
}
