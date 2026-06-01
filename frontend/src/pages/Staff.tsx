import { useEffect, useState } from "react";
import { Table, Button, Modal, Form, Input, Select, Tag, message, Typography, Card, Space, Avatar } from "antd";
import { PlusOutlined, KeyOutlined, StopOutlined } from "@ant-design/icons";
import { getStaff, createStaff, updateStaff, deleteStaff, resetPassword } from "../api/staff";

const roleLabels: Record<string, string> = { owner: "Владелец", admin_china: "Админ Китай", admin_dushanbe: "Админ Душанбе" };
const roleColors: Record<string, string> = { owner: "#00A76F", admin_china: "#00B8D9", admin_dushanbe: "#FFAB00" };

export default function Staff() {
  const [items, setItems] = useState<any[]>([]);
  const [modal, setModal] = useState(false);
  const [pwModal, setPwModal] = useState<number | null>(null);
  const [newPw, setNewPw] = useState("");
  const [form] = Form.useForm();

  const load = () => getStaff().then((r) => setItems(r.data));
  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    const values = await form.validateFields();
    try {
      await createStaff(values);
      message.success("Сотрудник создан");
      setModal(false); form.resetFields(); load();
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка");
    }
  };

  const handleDeactivate = async (id: number) => {
    await deleteStaff(id);
    message.success("Деактивирован");
    load();
  };

  const handleResetPw = async () => {
    if (!newPw) return;
    await resetPassword(pwModal!, newPw);
    message.success("Пароль сброшен");
    setPwModal(null); setNewPw("");
  };

  return (
    <>
      <div className="page-header">
        <Typography.Title className="page-title" level={3}>
          Сотрудники
        </Typography.Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => { form.resetFields(); setModal(true); }}
          style={{ borderRadius: 10, height: 44 }}
        >
          Добавить
        </Button>
      </div>

      <div className="animate-fade-in-up">
        <Card bodyStyle={{ padding: 0 }} className="hover-card">
          <Table
            dataSource={items}
            rowKey="id"
            columns={[
              {
                title: "Сотрудник",
                render: (_: any, r: any) => (
                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <Avatar
                      size={36}
                      style={{
                        background: roleColors[r.role] || "#919EAB",
                        fontWeight: 600,
                        fontSize: 14,
                      }}
                    >
                      {r.full_name?.charAt(0)?.toUpperCase()}
                    </Avatar>
                    <div>
                      <div style={{ fontWeight: 600 }}>{r.full_name}</div>
                      <div style={{ fontSize: 12, color: "#919EAB" }}>{r.login}</div>
                    </div>
                  </div>
                ),
              },
              {
                title: "Роль",
                dataIndex: "role",
                render: (v: string) => (
                  <Tag
                    style={{
                      borderRadius: 20,
                      padding: "2px 12px",
                      background: `${roleColors[v]}16`,
                      color: roleColors[v],
                      fontWeight: 600,
                    }}
                  >
                    {roleLabels[v] || v}
                  </Tag>
                ),
              },
              {
                title: "Статус",
                dataIndex: "is_active",
                render: (v: boolean) => (
                  <Tag
                    color={v ? "success" : "error"}
                    style={{ borderRadius: 20, padding: "2px 12px" }}
                  >
                    {v ? "Активен" : "Неактивен"}
                  </Tag>
                ),
              },
              {
                title: "Действия",
                width: 240,
                render: (_: any, r: any) => (
                  <Space>
                    <Button
                      size="small"
                      icon={<KeyOutlined />}
                      onClick={() => setPwModal(r.id)}
                      style={{ borderRadius: 8 }}
                    >
                      Пароль
                    </Button>
                    {r.is_active && (
                      <Button
                        size="small"
                        danger
                        icon={<StopOutlined />}
                        onClick={() => handleDeactivate(r.id)}
                        style={{ borderRadius: 8 }}
                      >
                        Деактивировать
                      </Button>
                    )}
                  </Space>
                ),
              },
            ]}
          />
        </Card>
      </div>

      <Modal
        title="Новый сотрудник"
        open={modal}
        onOk={handleCreate}
        onCancel={() => setModal(false)}
        okText="Создать"
        cancelText="Отмена"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="full_name" label="ФИО" rules={[{ required: true }]}>
            <Input style={{ borderRadius: 10 }} />
          </Form.Item>
          <Form.Item name="login" label="Логин" rules={[{ required: true }]}>
            <Input style={{ borderRadius: 10 }} />
          </Form.Item>
          <Form.Item name="password" label="Пароль" rules={[{ required: true }]}>
            <Input.Password style={{ borderRadius: 10 }} />
          </Form.Item>
          <Form.Item name="role" label="Роль" rules={[{ required: true }]}>
            <Select options={[
              { value: "admin_china", label: "Админ Китай" },
              { value: "admin_dushanbe", label: "Админ Душанбе" },
              { value: "owner", label: "Владелец" },
            ]} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="Сброс пароля"
        open={pwModal !== null}
        onOk={handleResetPw}
        onCancel={() => setPwModal(null)}
        okText="Сбросить"
        cancelText="Отмена"
      >
        <Input.Password
          placeholder="Новый пароль"
          value={newPw}
          onChange={(e) => setNewPw(e.target.value)}
          style={{ borderRadius: 10, height: 44 }}
          size="large"
        />
      </Modal>
    </>
  );
}
