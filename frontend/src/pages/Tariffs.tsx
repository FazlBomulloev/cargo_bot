import { useEffect, useState } from "react";
import { Table, Button, Modal, Form, InputNumber, Select, Tag, message, Typography, Card } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { getActiveTariffs, createTariff } from "../api/tariffs";

export default function Tariffs() {
  const [items, setItems] = useState<any[]>([]);
  const [modal, setModal] = useState(false);
  const [form] = Form.useForm();

  const load = () => getActiveTariffs().then((r) => setItems(r.data));
  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    const values = await form.validateFields();
    try {
      await createTariff(values);
      message.success("Тариф создан (старый деактивирован)");
      setModal(false); form.resetFields(); load();
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка");
    }
  };

  return (
    <>
      <div className="page-header">
        <Typography.Title className="page-title" level={3}>
          Тарифы
        </Typography.Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => { form.resetFields(); setModal(true); }}
          style={{ borderRadius: 10, height: 44 }}
        >
          Новый тариф
        </Button>
      </div>

      <div className="animate-fade-in-up">
        <Card bodyStyle={{ padding: 0 }} className="hover-card">
          <Table
            dataSource={items}
            rowKey="id"
            columns={[
              {
                title: "Метод",
                dataIndex: "method",
                render: (v: string) => (
                  <Tag color={v === "avia" ? "blue" : "orange"} style={{ borderRadius: 20, padding: "2px 12px" }}>
                    {v === "avia" ? "Авиа" : "Фура"}
                  </Tag>
                ),
              },
              {
                title: "$/кг",
                dataIndex: "price_per_kg",
                render: (v: number) => <span style={{ fontWeight: 600 }}>${v}</span>,
              },
              {
                title: "$/м³",
                dataIndex: "price_per_m3",
                render: (v: number) => v ? <span style={{ fontWeight: 600 }}>${v}</span> : "—",
              },
              { title: "Валюта", dataIndex: "currency" },
              {
                title: "Дата",
                dataIndex: "created_at",
                render: (v: string) => v ? new Date(v).toLocaleDateString("ru-RU") : "—",
              },
            ]}
          />
        </Card>
      </div>

      <Modal
        title="Новый тариф"
        open={modal}
        onOk={handleCreate}
        onCancel={() => setModal(false)}
        okText="Создать"
        cancelText="Отмена"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="method" label="Метод" rules={[{ required: true }]}>
            <Select options={[
              { value: "avia", label: "Авиа" },
              { value: "truck", label: "Фура" },
            ]} />
          </Form.Item>
          <Form.Item name="price_per_kg" label="Цена за кг ($)" rules={[{ required: true }]}>
            <InputNumber min={0} step={0.5} style={{ width: "100%", borderRadius: 10 }} />
          </Form.Item>
          <Form.Item name="price_per_m3" label="Цена за м³ ($)">
            <InputNumber min={0} step={10} style={{ width: "100%", borderRadius: 10 }} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
