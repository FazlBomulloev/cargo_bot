import { useEffect, useState } from "react";
import { Table, Button, Modal, Form, Input, Select, message, Typography, Card, Space } from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
import { getWarehouses, createWarehouse, updateWarehouse, deleteWarehouse } from "../api/warehouses";

export default function Warehouses() {
  const [items, setItems] = useState<any[]>([]);
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [form] = Form.useForm();

  const load = () => getWarehouses().then((r) => setItems(r.data));
  useEffect(() => { load(); }, []);

  const openNew = () => { setEditing(null); form.resetFields(); setModal(true); };
  const openEdit = (r: any) => { setEditing(r); form.setFieldsValue(r); setModal(true); };

  const handleSave = async () => {
    const values = await form.validateFields();
    try {
      if (editing) { await updateWarehouse(editing.id, values); }
      else { await createWarehouse(values); }
      message.success("Сохранено");
      setModal(false); load();
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка");
    }
  };

  const handleDelete = async (id: number) => {
    await deleteWarehouse(id);
    message.success("Склад деактивирован");
    load();
  };

  return (
    <>
      <div className="page-header">
        <Typography.Title className="page-title" level={3}>
          Склады
        </Typography.Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={openNew}
          style={{ borderRadius: 10, height: 44 }}
        >
          Добавить склад
        </Button>
      </div>

      <div className="animate-fade-in-up">
        <Card bodyStyle={{ padding: 0 }} className="hover-card">
          <Table
            dataSource={items}
            rowKey="id"
            columns={[
              { title: "Название", dataIndex: "name", render: (v: string) => <span style={{ fontWeight: 600 }}>{v}</span> },
              { title: "Тип", dataIndex: "type" },
              { title: "Город", dataIndex: "city" },
              { title: "Телефон", dataIndex: "phone" },
              {
                title: "Действия",
                width: 160,
                render: (_: any, r: any) => (
                  <Space>
                    <Button
                      size="small"
                      icon={<EditOutlined />}
                      onClick={() => openEdit(r)}
                      style={{ borderRadius: 8 }}
                    />
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
        title={editing ? "Редактировать склад" : "Новый склад"}
        open={modal}
        onOk={handleSave}
        onCancel={() => setModal(false)}
        okText="Сохранить"
        cancelText="Отмена"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="name" label="Название" rules={[{ required: true }]}>
            <Input style={{ borderRadius: 10 }} />
          </Form.Item>
          <Form.Item name="type" label="Тип" rules={[{ required: true }]}>
            <Select options={[
              { value: "china", label: "Китай" },
              { value: "dushanbe", label: "Душанбе" },
              { value: "pvz", label: "ПВЗ" },
            ]} />
          </Form.Item>
          <Form.Item name="country" label="Страна"><Input style={{ borderRadius: 10 }} /></Form.Item>
          <Form.Item name="city" label="Город"><Input style={{ borderRadius: 10 }} /></Form.Item>
          <Form.Item name="phone" label="Телефон" rules={[{ required: true }]}><Input style={{ borderRadius: 10 }} /></Form.Item>
          <Form.Item name="region" label="Регион" rules={[{ required: true }]}><Input style={{ borderRadius: 10 }} /></Form.Item>
          <Form.Item name="address" label="Адрес" rules={[{ required: true }]}>
            <Input.TextArea rows={2} style={{ borderRadius: 10 }} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
