import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Descriptions, Tag, Table, Button, message, Typography, Space } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import { getClient, blockClient } from "../api/clients";
import { getParcels } from "../api/parcels";

export default function ClientDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [client, setClient] = useState<any>(null);
  const [parcels, setParcels] = useState<any[]>([]);

  const load = async () => {
    const { data: c } = await getClient(+id!);
    setClient(c);
    const { data: p } = await getParcels({ client_id: c.id, per_page: 100 });
    setParcels(p.items || []);
  };

  useEffect(() => { if (id) load(); }, [id]);

  const handleBlock = async () => {
    await blockClient(+id!);
    await load();
    message.success("Статус изменён");
  };

  if (!client) return null;

  return (
    <>
      <div className="page-header">
        <Space>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate(-1)}
            style={{ borderRadius: 10 }}
          />
          <Typography.Title className="page-title" level={3}>
            Клиент {client.tps_code}
          </Typography.Title>
        </Space>
        <Button
          danger={client.status === "active"}
          type={client.status === "active" ? "primary" : "default"}
          onClick={handleBlock}
          style={{ borderRadius: 10 }}
        >
          {client.status === "active" ? "Заблокировать" : "Разблокировать"}
        </Button>
      </div>

      <div className="stagger-children">
        <Card className="hover-card" style={{ marginBottom: 20 }}>
          <Descriptions
            bordered
            column={{ xs: 1, sm: 2 }}
            labelStyle={{ fontWeight: 600, color: "#637381", background: "#F9FAFB" }}
          >
            <Descriptions.Item label="TPS-код">
              <span style={{ fontWeight: 600, color: "#00A76F" }}>{client.tps_code}</span>
            </Descriptions.Item>
            <Descriptions.Item label="Статус">
              <Tag
                color={client.status === "active" ? "success" : "error"}
                style={{ borderRadius: 20, padding: "2px 12px" }}
              >
                {client.status === "active" ? "Активен" : "Заблокирован"}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="ФИО">{client.full_name}</Descriptions.Item>
            <Descriptions.Item label="Телефон">{client.phone}</Descriptions.Item>
            <Descriptions.Item label="Адрес">{client.address || "—"}</Descriptions.Item>
            <Descriptions.Item label="Telegram ID">{client.telegram_id}</Descriptions.Item>
            <Descriptions.Item label="Язык">{client.lang}</Descriptions.Item>
            <Descriptions.Item label="Регистрация">{client.created_at?.slice(0, 10)}</Descriptions.Item>
          </Descriptions>
        </Card>

        <Card
          title={<span style={{ fontWeight: 600 }}>Посылки</span>}
          className="hover-card"
        >
          <Table
            dataSource={parcels}
            rowKey="id"
            size="small"
            columns={[
              {
                title: "Трек",
                dataIndex: "track_id",
                render: (v: string) => (
                  <span style={{ fontFamily: "monospace", fontWeight: 500 }}>{v}</span>
                ),
              },
              {
                title: "Статус",
                dataIndex: "status",
                render: (v: string) => {
                  const colors: Record<string, string> = {
                    received_dushanbe: "processing",
                    issued: "success",
                  };
                  const labels: Record<string, string> = {
                    received_dushanbe: "В Душанбе",
                    issued: "Получена",
                  };
                  return <Tag color={colors[v] || "default"} style={{ borderRadius: 20 }}>{labels[v] || v}</Tag>;
                },
              },
              { title: "Вес", dataIndex: "weight_kg", render: (v: number) => `${v} кг` },
              {
                title: "Метод",
                dataIndex: "delivery_method",
                render: (v: string) => (
                  <Tag color={v === "avia" ? "blue" : "orange"} style={{ borderRadius: 20 }}>
                    {v === "avia" ? "Авиа" : "Фура"}
                  </Tag>
                ),
              },
              {
                title: "Сумма",
                dataIndex: "amount_due",
                render: (v: number) => v ? (
                  <span style={{ fontWeight: 600, color: "#00A76F" }}>${v}</span>
                ) : "—",
              },
              { title: "Дата", dataIndex: "created_at", render: (v: string) => v?.slice(0, 10) },
            ]}
          />
        </Card>
      </div>
    </>
  );
}
