import { useEffect, useState } from "react";
import { Card, Input, Button, message, Typography, Space } from "antd";
import { SaveOutlined, SettingOutlined } from "@ant-design/icons";
import { getSettings, updateSetting } from "../api/settings";

const keys = [
  { key: "tariffs", label: "Тарифы (текст для бота)", icon: "💰" },
  { key: "support", label: "Поддержка (текст для бота)", icon: "🎧" },
];

export default function Settings() {
  const [values, setValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState<string | null>(null);

  useEffect(() => {
    getSettings().then((r) => setValues(r.data));
  }, []);

  const handleSave = async (key: string) => {
    setLoading(key);
    try {
      await updateSetting(key, values[key] || "");
      message.success("Сохранено");
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка");
    } finally {
      setLoading(null);
    }
  };

  return (
    <>
      <div className="page-header">
        <Typography.Title className="page-title" level={3}>
          Настройки контента бота
        </Typography.Title>
      </div>

      <div className="stagger-children">
        {keys.map((k) => (
          <Card
            key={k.key}
            className="hover-card"
            style={{ marginBottom: 20 }}
            title={
              <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 20 }}>{k.icon}</span>
                <span style={{ fontWeight: 600 }}>{k.label}</span>
              </span>
            }
          >
            <Input.TextArea
              rows={6}
              value={values[k.key] || ""}
              onChange={(e) => setValues({ ...values, [k.key]: e.target.value })}
              style={{ borderRadius: 12, fontSize: 14 }}
            />
            <Button
              type="primary"
              style={{ marginTop: 12, borderRadius: 10 }}
              loading={loading === k.key}
              onClick={() => handleSave(k.key)}
              icon={<SaveOutlined />}
            >
              Сохранить
            </Button>
          </Card>
        ))}
      </div>
    </>
  );
}
