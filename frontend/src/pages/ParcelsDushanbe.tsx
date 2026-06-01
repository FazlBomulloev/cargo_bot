import { useState } from "react";
import { Card, Form, Input, InputNumber, Select, Button, message, Typography, Alert } from "antd";
import { InboxOutlined } from "@ant-design/icons";
import { addDushanbeParcel } from "../api/parcels";

export default function ParcelsDushanbe() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const onFinish = async (values: any) => {
    setLoading(true);
    setResult(null);
    try {
      const { data } = await addDushanbeParcel(values);
      if (data.status === "unresolved") {
        setResult({ type: "warning", message: "TPS-код не найден, посылка сохранена как проблемная" });
      } else {
        setResult({ type: "success", message: `Посылка добавлена. Клиент: ${data.client_name}` });
      }
      form.resetFields();
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="page-header">
        <Typography.Title className="page-title" level={3}>
          Склад Душанбе
        </Typography.Title>
      </div>

      <div className="animate-fade-in-up">
        <Card
          style={{ maxWidth: 600 }}
          className="hover-card"
          title={
            <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <InboxOutlined style={{ color: "#00A76F" }} />
              <span style={{ fontWeight: 600 }}>Приёмка посылки</span>
            </span>
          }
        >
          {result && (
            <div className="animate-scale-in">
              <Alert
                type={result.type}
                message={result.message}
                showIcon
                style={{ marginBottom: 20, borderRadius: 12 }}
                closable
                onClose={() => setResult(null)}
              />
            </div>
          )}
          <Form form={form} layout="vertical" onFinish={onFinish} size="large">
            <Form.Item name="track_id" label="Трек-код" rules={[{ required: true }]}>
              <Input placeholder="Скан или ручной ввод" autoFocus style={{ borderRadius: 12 }} />
            </Form.Item>
            <Form.Item name="tps_code" label="TPS-код клиента" rules={[{ required: true }]}>
              <Input placeholder="TPS001" style={{ borderRadius: 12 }} />
            </Form.Item>
            <Form.Item name="weight_kg" label="Вес (кг)" rules={[{ required: true }]}>
              <InputNumber min={0.001} step={0.1} style={{ width: "100%", borderRadius: 12 }} />
            </Form.Item>
            <Form.Item name="volume_m3" label="Объём м³ (для фуры)">
              <InputNumber min={0} step={0.01} style={{ width: "100%", borderRadius: 12 }} />
            </Form.Item>
            <Form.Item name="delivery_method" label="Способ доставки" rules={[{ required: true }]}>
              <Select
                options={[
                  { value: "avia", label: "Авиа" },
                  { value: "truck", label: "Фура" },
                ]}
              />
            </Form.Item>
            <Form.Item name="comment" label="Комментарий">
              <Input.TextArea rows={2} style={{ borderRadius: 12 }} />
            </Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{ height: 48, borderRadius: 12, fontSize: 15, fontWeight: 600 }}
            >
              Добавить
            </Button>
          </Form>
        </Card>
      </div>
    </>
  );
}
