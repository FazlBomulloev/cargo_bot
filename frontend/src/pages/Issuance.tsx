import { useState } from "react";
import { Card, Input, Button, Table, Tag, Radio, message, Typography, Space, Statistic, List } from "antd";
import { SearchOutlined, ShoppingCartOutlined, UserOutlined } from "@ant-design/icons";
import { searchClients } from "../api/clients";
import { getParcels } from "../api/parcels";
import { getActiveTariffs } from "../api/tariffs";
import { createIssuance } from "../api/issuance";

export default function Issuance() {
  const [query, setQuery] = useState("");
  const [client, setClient] = useState<any>(null);
  const [candidates, setCandidates] = useState<any[]>([]);
  const [parcels, setParcels] = useState<any[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [tariffs, setTariffs] = useState<any[]>([]);
  const [paymentMethod, setPaymentMethod] = useState<string>("cash");
  const [paymentStatus, setPaymentStatus] = useState<string>("paid");
  const [loading, setLoading] = useState(false);

  const selectClient = async (c: any) => {
    setClient(c);
    setCandidates([]);
    const [p, t] = await Promise.all([
      getParcels({ client_id: c.id, status: "received_dushanbe", per_page: 100 }),
      getActiveTariffs(),
    ]);
    setParcels(p.data.items || []);
    setTariffs(t.data);
    setSelected([]);
  };

  const search = async () => {
    const { data } = await searchClients(query.trim());
    if (data.length === 0) { message.warning("Клиент не найден"); return; }
    if (data.length === 1) {
      await selectClient(data[0]);
    } else {
      setCandidates(data);
      setClient(null);
      setParcels([]);
      setSelected([]);
    }
  };

  const calcAmount = (p: any) => {
    const t = tariffs.find((t: any) => t.method === p.delivery_method);
    if (!t) return 0;
    if (p.delivery_method === "avia") return +(p.weight_kg * t.price_per_kg).toFixed(2);
    const byKg = p.weight_kg * t.price_per_kg;
    const byM3 = (p.volume_m3 || 0) * (t.price_per_m3 || 0);
    return +Math.max(byKg, byM3).toFixed(2);
  };

  const totalWeight = parcels.filter((p) => selected.includes(p.id)).reduce((s, p) => s + +p.weight_kg, 0);
  const totalAmount = parcels.filter((p) => selected.includes(p.id)).reduce((s, p) => s + calcAmount(p), 0);

  const handleIssue = async () => {
    if (!selected.length) { message.warning("Выберите посылки"); return; }
    setLoading(true);
    try {
      await createIssuance({
        client_id: client.id,
        parcel_ids: selected,
        payment_method: paymentStatus === "paid" ? paymentMethod : null,
        payment_status: paymentStatus,
      });
      message.success(`Выдача оформлена! Итого: ${totalWeight.toFixed(1)} кг, $${totalAmount.toFixed(2)}`);
      setClient(null); setParcels([]); setSelected([]); setQuery(""); setCandidates([]);
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
          Выдача товара
        </Typography.Title>
      </div>

      <div className="stagger-children">
        <Card className="hover-card" style={{ marginBottom: 20 }}>
          <Space.Compact style={{ width: "100%", maxWidth: 500 }}>
            <Input
              placeholder="TPS-код или телефон"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onPressEnter={search}
              prefix={<SearchOutlined style={{ color: "#919EAB" }} />}
              style={{ height: 48, borderRadius: "12px 0 0 12px", fontSize: 15 }}
            />
            <Button
              type="primary"
              onClick={search}
              style={{ height: 48, borderRadius: "0 12px 12px 0", paddingInline: 24 }}
            >
              Найти
            </Button>
          </Space.Compact>
        </Card>

        {candidates.length > 1 && !client && (
          <Card
            className="hover-card animate-scale-in"
            title={
              <span style={{ fontWeight: 600 }}>
                Найдено клиентов: {candidates.length} — выберите нужного
              </span>
            }
            style={{ marginBottom: 20 }}
          >
            <List
              dataSource={candidates}
              renderItem={(c: any) => (
                <List.Item
                  style={{ cursor: "pointer", padding: "12px 16px", borderRadius: 10, transition: "background 0.2s" }}
                  onClick={() => selectClient(c)}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "#F4F6F8")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  <List.Item.Meta
                    avatar={
                      <div
                        style={{
                          width: 40, height: 40, borderRadius: 10,
                          background: "linear-gradient(135deg, #00A76F, #5BE49B)",
                          display: "flex", alignItems: "center", justifyContent: "center",
                          color: "#fff", fontWeight: 700, fontSize: 16,
                        }}
                      >
                        {c.full_name?.charAt(0)?.toUpperCase()}
                      </div>
                    }
                    title={<span style={{ fontWeight: 600 }}>{c.full_name}</span>}
                    description={
                      <span style={{ color: "#637381" }}>
                        {c.tps_code} &bull; {c.phone}
                      </span>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        )}

        {client && (
          <Card
            className="hover-card animate-scale-in"
            title={
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: 10,
                    background: "linear-gradient(135deg, #00A76F, #5BE49B)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#fff",
                    fontWeight: 700,
                    fontSize: 16,
                  }}
                >
                  {client.full_name?.charAt(0)?.toUpperCase()}
                </div>
                <div>
                  <div style={{ fontWeight: 600 }}>{client.full_name}</div>
                  <div style={{ fontSize: 13, color: "#919EAB", fontWeight: 400 }}>
                    {client.tps_code} | {client.phone}
                  </div>
                </div>
              </div>
            }
          >
            <Table
              dataSource={parcels}
              rowKey="id"
              size="small"
              pagination={false}
              rowSelection={{
                selectedRowKeys: selected,
                onChange: (keys) => setSelected(keys as number[]),
              }}
              columns={[
                {
                  title: "Трек",
                  dataIndex: "track_id",
                  render: (v: string) => (
                    <span style={{ fontFamily: "monospace", fontWeight: 500 }}>{v}</span>
                  ),
                },
                {
                  title: "Вес",
                  dataIndex: "weight_kg",
                  render: (v: number) => <span style={{ fontWeight: 500 }}>{v} кг</span>,
                },
                {
                  title: "Объём",
                  dataIndex: "volume_m3",
                  render: (v: number) => v ? `${v} м³` : "—",
                },
                {
                  title: "Метод",
                  dataIndex: "delivery_method",
                  render: (v: string) => (
                    <Tag color={v === "avia" ? "blue" : "orange"} style={{ borderRadius: 20 }}>
                      {v === "avia" ? "Авиа" : "Фура"}
                    </Tag>
                  ),
                },
                {
                  title: "Сумма",
                  render: (_: any, r: any) => (
                    <span style={{ fontWeight: 600, color: "#00A76F" }}>
                      ${calcAmount(r).toFixed(2)}
                    </span>
                  ),
                },
              ]}
            />

            <div
              style={{
                marginTop: 24,
                padding: 20,
                background: "#F4F6F8",
                borderRadius: 16,
                display: "flex",
                gap: 32,
                alignItems: "center",
                flexWrap: "wrap",
              }}
            >
              <Statistic
                title="Вес"
                value={totalWeight.toFixed(1)}
                suffix="кг"
                valueStyle={{ fontWeight: 700, fontSize: 24 }}
              />
              <Statistic
                title="Сумма"
                value={totalAmount.toFixed(2)}
                prefix="$"
                valueStyle={{ fontWeight: 700, fontSize: 24, color: "#00A76F" }}
              />
              <div>
                <div style={{ marginBottom: 8 }}>
                  <Radio.Group value={paymentStatus} onChange={(e) => setPaymentStatus(e.target.value)}>
                    <Radio.Button value="paid" style={{ borderRadius: "10px 0 0 10px" }}>Оплачено</Radio.Button>
                    <Radio.Button value="debt" style={{ borderRadius: "0 10px 10px 0" }}>Долг</Radio.Button>
                  </Radio.Group>
                </div>
                {paymentStatus === "paid" && (
                  <Radio.Group value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)}>
                    <Radio.Button value="cash" style={{ borderRadius: "10px 0 0 10px" }}>Наличные</Radio.Button>
                    <Radio.Button value="transfer" style={{ borderRadius: "0 10px 10px 0" }}>Перевод</Radio.Button>
                  </Radio.Group>
                )}
              </div>
              <Button
                type="primary"
                size="large"
                onClick={handleIssue}
                loading={loading}
                icon={<ShoppingCartOutlined />}
                style={{ borderRadius: 12, height: 48, paddingInline: 32, fontWeight: 600 }}
              >
                Выдать
              </Button>
            </div>
          </Card>
        )}
      </div>
    </>
  );
}
