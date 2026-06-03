import { useEffect, useState } from "react";
import { Table, Button, Modal, Form, Input, Select, Tag, message, Typography, Card, Space, Avatar, Checkbox } from "antd";
import { PlusOutlined, KeyOutlined, StopOutlined, SafetyOutlined } from "@ant-design/icons";
import { getStaff, createStaff, deleteStaff, resetPassword, updatePermissions } from "../api/staff";

const roleLabels: Record<string, string> = { owner: "Владелец", admin_china: "Админ Китай", admin_dushanbe: "Админ Душанбе" };
const roleColors: Record<string, string> = { owner: "#00A76F", admin_china: "#00B8D9", admin_dushanbe: "#FFAB00" };

const ALL_PERMISSIONS = [
  { key: "dashboard", label: "Дашборд" },
  { key: "parcels_china", label: "Склад Китай" },
  { key: "parcels_dushanbe", label: "Склад Душанбе" },
  { key: "parcels_list", label: "Все посылки" },
  { key: "issuance", label: "Выдача" },
  { key: "issuance_history", label: "История выдач" },
  { key: "clients", label: "Клиенты" },
  { key: "unresolved", label: "Проблемные" },
  { key: "warehouses", label: "Склады" },
  { key: "tariffs", label: "Тарифы" },
  { key: "settings", label: "Настройки" },
  { key: "audit", label: "Журнал" },
];

export default function Staff() {
  const [items, setItems] = useState<any[]>([]);
  const [modal, setModal] = useState(false);
  const [pwModal, setPwModal] = useState<number | null>(null);
  const [newPw, setNewPw] = useState("");
  const [permModal, setPermModal] = useState<any>(null);
  const [permValues, setPermValues] = useState<string[]>([]);
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

  const openPermissions = (staff: any) => {
    setPermModal(staff);
    setPermValues(staff.permissions || []);
  };

  const handleSavePermissions = async () => {
    try {
      await updatePermissions(permModal.id, permValues);
      message.success("Права обновлены");
      setPermModal(null);
      load();
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка");
    }
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
                      src={r.avatar_url || undefined}
                      style={{
                        background: roleColors[r.role] || "#919EAB",
                        fontWeight: 600,
                        fontSize: 14,
                      }}
                    >
                      {!r.avatar_url && r.full_name?.charAt(0)?.toUpperCase()}
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
                title: "Доступ",
                dataIndex: "permissions",
                render: (perms: string[], r: any) =>
                  r.role === "owner" ? (
                    <span style={{ color: "#919EAB", fontSize: 13 }}>Полный доступ</span>
                  ) : (
                    <span style={{ fontSize: 13, color: "#637381" }}>
                      {(perms || []).length} из {ALL_PERMISSIONS.length} разделов
                    </span>
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
                width: 320,
                render: (_: any, r: any) => (
                  <Space>
                    {r.role !== "owner" && (
                      <Button
                        size="small"
                        icon={<SafetyOutlined />}
                        onClick={() => openPermissions(r)}
                        style={{ borderRadius: 8 }}
                      >
                        Права
                      </Button>
                    )}
                    <Button
                      size="small"
                      icon={<KeyOutlined />}
                      onClick={() => setPwModal(r.id)}
                      style={{ borderRadius: 8 }}
                    >
                      Пароль
                    </Button>
                    {r.is_active && r.role !== "owner" && (
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

      <Modal
        title={
          <span>
            Доступ: <span style={{ color: "#00A76F" }}>{permModal?.full_name}</span>
          </span>
        }
        open={permModal !== null}
        onOk={handleSavePermissions}
        onCancel={() => setPermModal(null)}
        okText="Сохранить"
        cancelText="Отмена"
      >
        <div style={{ marginTop: 16 }}>
          <Checkbox.Group
            value={permValues}
            onChange={(vals) => setPermValues(vals as string[])}
            style={{ display: "flex", flexDirection: "column", gap: 12 }}
          >
            {ALL_PERMISSIONS.map((p) => (
              <Checkbox key={p.key} value={p.key} style={{ fontSize: 14 }}>
                {p.label}
              </Checkbox>
            ))}
          </Checkbox.Group>
          <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
            <Button
              size="small"
              onClick={() => setPermValues(ALL_PERMISSIONS.map((p) => p.key))}
              style={{ borderRadius: 8 }}
            >
              Выбрать все
            </Button>
            <Button
              size="small"
              onClick={() => setPermValues([])}
              style={{ borderRadius: 8 }}
            >
              Убрать все
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
