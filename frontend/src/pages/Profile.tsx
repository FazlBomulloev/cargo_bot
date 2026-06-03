import { useState, useRef } from "react";
import { Card, Form, Input, Button, message, Typography, Avatar, Upload, Divider } from "antd";
import { UserOutlined, CameraOutlined, SaveOutlined } from "@ant-design/icons";
import { updateProfile, uploadAvatar, getMe } from "../api/auth";
import { useAuth } from "../hooks/useAuth";

export default function Profile() {
  const { user, setAuth } = useAuth();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [avatarLoading, setAvatarLoading] = useState(false);
  const token = localStorage.getItem("token") || "";

  const refreshUser = async () => {
    const { data } = await getMe();
    setAuth(token, data);
  };

  const onSave = async () => {
    const values = await form.validateFields();
    const payload: Record<string, unknown> = {};
    if (values.full_name && values.full_name !== user?.full_name) payload.full_name = values.full_name;
    if (values.login && values.login !== user?.login) payload.login = values.login;
    if (values.new_password) {
      payload.current_password = values.current_password;
      payload.new_password = values.new_password;
    }
    if (Object.keys(payload).length === 0) {
      message.info("Нет изменений");
      return;
    }
    setLoading(true);
    try {
      await updateProfile(payload);
      await refreshUser();
      message.success("Профиль обновлён");
      form.setFieldsValue({ current_password: "", new_password: "", confirm_password: "" });
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarUpload = async (file: File) => {
    setAvatarLoading(true);
    try {
      await uploadAvatar(file);
      await refreshUser();
      message.success("Фото обновлено");
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка загрузки");
    } finally {
      setAvatarLoading(false);
    }
    return false;
  };

  const roleLabels: Record<string, string> = {
    owner: "Владелец",
    admin_china: "Админ Китай",
    admin_dushanbe: "Админ Душанбе",
  };

  return (
    <>
      <div className="page-header">
        <Typography.Title className="page-title" level={3}>
          Профиль
        </Typography.Title>
      </div>

      <div className="animate-fade-in-up" style={{ maxWidth: 560 }}>
        <Card className="hover-card">
          <div style={{ display: "flex", alignItems: "center", gap: 24, marginBottom: 32 }}>
            <Upload
              showUploadList={false}
              accept="image/jpeg,image/png,image/webp"
              beforeUpload={handleAvatarUpload}
            >
              <div style={{ position: "relative", cursor: "pointer" }}>
                <Avatar
                  size={80}
                  src={user?.avatar_url || undefined}
                  icon={!user?.avatar_url && <UserOutlined />}
                  style={{
                    background: "#00A76F",
                    fontSize: 32,
                    fontWeight: 700,
                  }}
                >
                  {!user?.avatar_url && user?.full_name?.charAt(0)?.toUpperCase()}
                </Avatar>
                <div
                  style={{
                    position: "absolute",
                    bottom: 0,
                    right: 0,
                    width: 28,
                    height: 28,
                    borderRadius: "50%",
                    background: "#1C252E",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    border: "2px solid #fff",
                  }}
                >
                  <CameraOutlined style={{ color: "#fff", fontSize: 12 }} />
                </div>
              </div>
            </Upload>
            <div>
              <div style={{ fontSize: 20, fontWeight: 700 }}>{user?.full_name}</div>
              <div style={{ color: "#919EAB", fontSize: 14 }}>{roleLabels[user?.role || ""] || user?.role}</div>
            </div>
          </div>

          <Form
            form={form}
            layout="vertical"
            initialValues={{
              full_name: user?.full_name,
              login: user?.login,
            }}
            size="large"
          >
            <Form.Item name="full_name" label="Имя">
              <Input style={{ borderRadius: 12 }} />
            </Form.Item>
            <Form.Item name="login" label="Логин">
              <Input style={{ borderRadius: 12 }} />
            </Form.Item>

            <Divider style={{ margin: "16px 0" }}>Смена пароля</Divider>

            <Form.Item name="current_password" label="Текущий пароль">
              <Input.Password style={{ borderRadius: 12 }} />
            </Form.Item>
            <Form.Item name="new_password" label="Новый пароль">
              <Input.Password style={{ borderRadius: 12 }} />
            </Form.Item>
            <Form.Item
              name="confirm_password"
              label="Подтверждение"
              dependencies={["new_password"]}
              rules={[
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue("new_password") === value) return Promise.resolve();
                    return Promise.reject(new Error("Пароли не совпадают"));
                  },
                }),
              ]}
            >
              <Input.Password style={{ borderRadius: 12 }} />
            </Form.Item>

            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={onSave}
              loading={loading}
              block
              style={{ height: 48, borderRadius: 12, fontSize: 15, fontWeight: 600, marginTop: 8 }}
            >
              Сохранить
            </Button>
          </Form>
        </Card>
      </div>
    </>
  );
}
