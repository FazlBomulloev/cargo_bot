import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Form, Input, Button, Typography, message } from "antd";
import { UserOutlined, LockOutlined } from "@ant-design/icons";
import { login, getMe } from "../api/auth";
import { useAuth } from "../hooks/useAuth";

export default function Login() {
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAuth();
  const navigate = useNavigate();

  const onFinish = async (values: { login: string; password: string }) => {
    setLoading(true);
    try {
      const { data } = await login(values.login, values.password);
      const token = data.access_token;
      setAuth(token, null as any);
      const { data: user } = await getMe();
      setAuth(token, user);
      message.success(`Добро пожаловать, ${user.full_name}!`);
      navigate("/");
    } catch (err: any) {
      console.error("Login error detail:", err.response?.data || err.message);
      message.error("Неверный логин или пароль");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-bg">
      <div className="login-card">
        <div
          style={{
            background: "#fff",
            borderRadius: 24,
            padding: "48px 40px 40px",
            boxShadow: "0 24px 48px rgba(0, 0, 0, 0.2)",
          }}
        >
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              marginBottom: 40,
            }}
          >
            <div
              style={{
                width: 64,
                height: 64,
                borderRadius: 16,
                background: "linear-gradient(135deg, #00A76F 0%, #5BE49B 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#fff",
                fontSize: 28,
                fontWeight: 700,
                marginBottom: 20,
                boxShadow: "0 12px 24px rgba(0, 167, 111, 0.3)",
              }}
            >
              C
            </div>
            <Typography.Title
              level={3}
              style={{
                margin: 0,
                fontWeight: 700,
                color: "#1C252E",
                letterSpacing: -0.5,
              }}
            >
              Cargo TPS
            </Typography.Title>
            <Typography.Text
              style={{
                color: "#919EAB",
                marginTop: 8,
                fontSize: 15,
              }}
            >
              Войдите в панель управления
            </Typography.Text>
          </div>

          <Form onFinish={onFinish} size="large" layout="vertical">
            <Form.Item
              name="login"
              rules={[{ required: true, message: "Введите логин" }]}
            >
              <Input
                prefix={
                  <UserOutlined style={{ color: "#919EAB", fontSize: 18 }} />
                }
                placeholder="Логин"
                style={{
                  height: 48,
                  borderRadius: 12,
                  fontSize: 15,
                }}
              />
            </Form.Item>
            <Form.Item
              name="password"
              rules={[{ required: true, message: "Введите пароль" }]}
            >
              <Input.Password
                prefix={
                  <LockOutlined style={{ color: "#919EAB", fontSize: 18 }} />
                }
                placeholder="Пароль"
                style={{
                  height: 48,
                  borderRadius: 12,
                  fontSize: 15,
                }}
              />
            </Form.Item>
            <Form.Item style={{ marginBottom: 0, marginTop: 8 }}>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                style={{
                  height: 48,
                  borderRadius: 12,
                  fontSize: 16,
                  fontWeight: 600,
                }}
              >
                Войти
              </Button>
            </Form.Item>
          </Form>
        </div>
      </div>
    </div>
  );
}
