import { useEffect, useRef, useState } from "react";
import { Card, Input, Button, message, Typography, Divider, Space, Tag, Table } from "antd";
import { ScanOutlined, CloudUploadOutlined, CheckCircleOutlined } from "@ant-design/icons";
import { addChinaParcel, addChinaBulk, getChinaParcels } from "../api/parcels";

const { TextArea } = Input;

export default function ParcelsChina() {
  const [singleTrack, setSingleTrack] = useState("");
  const [bulkText, setBulkText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [parcels, setParcels] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [tableLoading, setTableLoading] = useState(false);
  const inputRef = useRef<any>(null);

  const loadParcels = async (p = page) => {
    setTableLoading(true);
    try {
      const { data } = await getChinaParcels({ page: p, per_page: 20 });
      setParcels(data.items || []);
      setTotal(data.total || 0);
    } catch {
      // ignore
    } finally {
      setTableLoading(false);
    }
  };

  useEffect(() => { loadParcels(); }, [page]);

  const handleSingle = async () => {
    if (!singleTrack.trim()) return;
    setLoading(true);
    try {
      await addChinaParcel(singleTrack.trim());
      message.success(`Трек ${singleTrack.trim().toUpperCase()} добавлен`);
      setSingleTrack("");
      inputRef.current?.focus();
      loadParcels(1);
      setPage(1);
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  const handleBulk = async () => {
    const tracks = bulkText.split("\n").map((t) => t.trim()).filter(Boolean);
    if (!tracks.length) return;
    setLoading(true);
    try {
      const { data } = await addChinaBulk(tracks);
      setResult(data);
      message.success(`Добавлено: ${data.added} из ${data.total}`);
      setBulkText("");
      loadParcels(1);
      setPage(1);
    } catch (e: any) {
      message.error(e.response?.data?.detail || "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") { e.preventDefault(); handleSingle(); }
  };

  return (
    <>
      <div className="page-header">
        <Typography.Title className="page-title" level={3}>
          Склад Китай
        </Typography.Title>
      </div>

      <div className="stagger-children">
        <Card
          title={
            <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <ScanOutlined style={{ color: "#00A76F" }} />
              <span style={{ fontWeight: 600 }}>Одиночный скан</span>
            </span>
          }
          className="hover-card"
          style={{ marginBottom: 20 }}
        >
          <Space.Compact style={{ width: "100%" }}>
            <Input
              ref={inputRef}
              placeholder="Трек-код (скан или ввод)"
              value={singleTrack}
              onChange={(e) => setSingleTrack(e.target.value)}
              onKeyDown={handleKeyDown}
              autoFocus
              style={{ height: 48, fontSize: 15, borderRadius: "12px 0 0 12px" }}
            />
            <Button
              type="primary"
              loading={loading}
              onClick={handleSingle}
              icon={<CheckCircleOutlined />}
              style={{ height: 48, borderRadius: "0 12px 12px 0", paddingInline: 24 }}
            >
              Добавить
            </Button>
          </Space.Compact>
        </Card>

        <Card
          title={
            <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <CloudUploadOutlined style={{ color: "#00A76F" }} />
              <span style={{ fontWeight: 600 }}>Массовый ввод</span>
            </span>
          }
          className="hover-card"
        >
          <TextArea
            rows={8}
            placeholder="Каждая строка — отдельный трек-код"
            value={bulkText}
            onChange={(e) => setBulkText(e.target.value)}
            style={{ borderRadius: 12, fontSize: 14, fontFamily: "monospace" }}
          />
          <Button
            type="primary"
            style={{ marginTop: 16, height: 44, borderRadius: 12 }}
            loading={loading}
            onClick={handleBulk}
            icon={<CloudUploadOutlined />}
          >
            Добавить все
          </Button>

          {result && (
            <div className="animate-fade-in-up" style={{ marginTop: 20 }}>
              <Divider style={{ margin: "16px 0" }} />
              <Space size={8}>
                <Tag
                  color="processing"
                  style={{ fontSize: 13, padding: "4px 14px", borderRadius: 20 }}
                >
                  Всего: {result.total}
                </Tag>
                <Tag
                  color="success"
                  style={{ fontSize: 13, padding: "4px 14px", borderRadius: 20 }}
                >
                  Добавлено: {result.added}
                </Tag>
                <Tag
                  color="warning"
                  style={{ fontSize: 13, padding: "4px 14px", borderRadius: 20 }}
                >
                  Дубли: {result.duplicates}
                </Tag>
              </Space>
              {result.duplicate_list?.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <Typography.Text type="secondary" style={{ fontSize: 13 }}>
                    Дубликаты: {result.duplicate_list.join(", ")}
                  </Typography.Text>
                </div>
              )}
            </div>
          )}
        </Card>

        <Card
          title={
            <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontWeight: 600 }}>Последние добавленные</span>
              <Tag color="processing" style={{ borderRadius: 20, fontSize: 13 }}>
                {total}
              </Tag>
            </span>
          }
          className="hover-card"
          style={{ marginTop: 20 }}
        >
          <Table
            dataSource={parcels}
            rowKey="id"
            size="small"
            loading={tableLoading}
            pagination={{
              current: page,
              pageSize: 20,
              total,
              onChange: (p) => setPage(p),
              showSizeChanger: false,
              showTotal: (t) => `Всего: ${t}`,
            }}
            columns={[
              {
                title: "Трек-код",
                dataIndex: "track_id",
                render: (v: string) => (
                  <span style={{ fontFamily: "monospace", fontWeight: 500 }}>{v}</span>
                ),
              },
              {
                title: "Дата",
                dataIndex: "created_at",
                render: (v: string) => new Date(v).toLocaleString("ru-RU", {
                  day: "2-digit", month: "2-digit", year: "numeric",
                  hour: "2-digit", minute: "2-digit",
                }),
              },
            ]}
          />
        </Card>
      </div>
    </>
  );
}
