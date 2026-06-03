import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Descriptions, Tag, Select, Button, message, Typography, Space } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import { getParcel, updateParcelStatus } from "../api/parcels";

const statusLabels: Record<string, string> = {
  received_dushanbe: "В Душанбе",
  issued: "Получена",
};
const statusColors: Record<string, string> = {
  received_dushanbe: "processing",
  issued: "success",
};

export default function ParcelDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [parcel, setParcel] = useState<any>(null);
  const [newStatus, setNewStatus] = useState<string>("");

  useEffect(() => {
    if (id) getParcel(+id).then((r) => { setParcel(r.data); setNewStatus(r.data.status); });
  }, [id]);

  const handleStatusChange = async () => {
    try {
      await updateParcelStatus(+id!, newStatus);
      const { data } = await getParcel(+id!);
      setParcel(data);
      message.success("Статус обновлён");
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка");
    }
  };

  if (!parcel) return null;

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
            Посылка #{parcel.id}
          </Typography.Title>
        </Space>
      </div>

      <div className="animate-fade-in-up">
        <Card className="hover-card">
          <Descriptions
            bordered
            column={{ xs: 1, sm: 2 }}
            labelStyle={{ fontWeight: 600, color: "#637381", background: "#F9FAFB" }}
            contentStyle={{ background: "#fff" }}
          >
            <Descriptions.Item label="Трек-код">
              <span style={{ fontFamily: "monospace", fontWeight: 600 }}>{parcel.track_id}</span>
            </Descriptions.Item>
            <Descriptions.Item label="Статус">
              <Tag color={statusColors[parcel.status]} style={{ borderRadius: 20, padding: "2px 12px" }}>
                {statusLabels[parcel.status]}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Client ID">{parcel.client_id}</Descriptions.Item>
            <Descriptions.Item label="Метод">
              <Tag color={parcel.delivery_method === "avia" ? "blue" : "orange"} style={{ borderRadius: 20 }}>
                {parcel.delivery_method === "avia" ? "Авиа" : "Фура"}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Вес">
              <span style={{ fontWeight: 600 }}>{parcel.weight_kg} кг</span>
            </Descriptions.Item>
            <Descriptions.Item label="Объём">{parcel.volume_m3 ? `${parcel.volume_m3} м³` : "—"}</Descriptions.Item>
            <Descriptions.Item label="Сумма">
              <span style={{ fontWeight: 600, color: "#00A76F" }}>
                {parcel.amount_due ? `$${parcel.amount_due}` : "—"}
              </span>
            </Descriptions.Item>
            <Descriptions.Item label="Тариф">{parcel.tariff_snapshot ? `$${parcel.tariff_snapshot}` : "—"}</Descriptions.Item>
            <Descriptions.Item label="Регистрация Китай">
              <Tag color={parcel.has_china_registration ? "success" : "default"}>
                {parcel.has_china_registration ? "Да" : "Нет"}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Комментарий">{parcel.comment || "—"}</Descriptions.Item>
            <Descriptions.Item label="Дата создания">{parcel.created_at?.slice(0, 10)}</Descriptions.Item>
            <Descriptions.Item label="Уведомлён">{parcel.notified_at?.slice(0, 10) || "—"}</Descriptions.Item>
          </Descriptions>
          <div style={{ marginTop: 20, display: "flex", gap: 12, alignItems: "center" }}>
            <Select
              value={newStatus}
              onChange={setNewStatus}
              style={{ width: 220 }}
              options={Object.entries(statusLabels).map(([k, v]) => ({ value: k, label: v }))}
            />
            <Button
              type="primary"
              onClick={handleStatusChange}
              disabled={newStatus === parcel.status}
              style={{ borderRadius: 10 }}
            >
              Обновить статус
            </Button>
          </div>
        </Card>
      </div>
    </>
  );
}
