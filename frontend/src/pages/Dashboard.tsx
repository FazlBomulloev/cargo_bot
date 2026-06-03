import { useEffect, useState } from "react";
import { Card, Col, DatePicker, Row, Select, Table, Typography } from "antd";
import {
  SendOutlined,
  InboxOutlined,
  DollarOutlined,
  UserAddOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  DatabaseOutlined,
} from "@ant-design/icons";
import {
  getOverview,
  getTopClients,
  getStuckParcels,
  getParcelsByDay,
  getRevenue,
} from "../api/stats";
import { Line, Column } from "@ant-design/charts";
import dayjs from "dayjs";

const { RangePicker } = DatePicker;

export default function Dashboard() {
  const [period, setPeriod] = useState("30d");
  const [customRange, setCustomRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);
  const [overview, setOverview] = useState<any>({});
  const [topClients, setTopClients] = useState<any[]>([]);
  const [stuck, setStuck] = useState<any[]>([]);
  const [parcelsByDay, setParcelsByDay] = useState<any[]>([]);
  const [revenue, setRevenue] = useState<any[]>([]);

  useEffect(() => {
    if (period === "custom" && !customRange) return;
    const fromDate = period === "custom" && customRange ? customRange[0].format("YYYY-MM-DD") : undefined;
    const toDate = period === "custom" && customRange ? customRange[1].format("YYYY-MM-DD") : undefined;
    getOverview(period, fromDate, toDate).then((r) => setOverview(r.data)).catch(() => {});
    getTopClients(10, "amount").then((r) => setTopClients(r.data)).catch(() => {});
    getStuckParcels(14).then((r) => setStuck(r.data)).catch(() => {});
    getParcelsByDay().then((r) => setParcelsByDay(Array.isArray(r.data) ? r.data : [])).catch(() => {});
    getRevenue("week").then((r) => setRevenue(Array.isArray(r.data) ? r.data : [])).catch(() => {});
  }, [period, customRange]);

  const stats = [
    {
      title: "Посылок в Китае",
      value: overview.china_count ?? 0,
      icon: <SendOutlined style={{ fontSize: 28 }} />,
      className: "stat-card stat-card-green",
      color: "#1B5E20",
      bg: "linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%)",
    },
    {
      title: "В Душанбе",
      value: overview.dushanbe_count ?? 0,
      icon: <InboxOutlined style={{ fontSize: 28 }} />,
      className: "stat-card stat-card-blue",
      color: "#0D47A1",
      bg: "linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%)",
    },
    {
      title: "Выручка",
      value: `$${(overview.revenue ?? 0).toLocaleString("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      icon: <DollarOutlined style={{ fontSize: 28 }} />,
      className: "stat-card stat-card-orange",
      color: "#E65100",
      bg: "linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%)",
    },
    {
      title: "Общий вес",
      value: (() => {
        const w = overview.total_weight ?? 0;
        return w >= 1000 ? `${(w / 1000).toFixed(2)} т` : `${w.toFixed(1)} кг`;
      })(),
      icon: <DatabaseOutlined style={{ fontSize: 28 }} />,
      className: "stat-card stat-card-teal",
      color: "#006064",
      bg: "linear-gradient(135deg, #E0F2F1 0%, #B2DFDB 100%)",
    },
    {
      title: "Новых клиентов",
      value: overview.new_clients ?? 0,
      icon: <UserAddOutlined style={{ fontSize: 28 }} />,
      className: "stat-card stat-card-purple",
      color: "#4A148C",
      bg: "linear-gradient(135deg, #F3E5F5 0%, #E1BEE7 100%)",
    },
  ];

  const lineConfig = {
    data: parcelsByDay,
    xField: "date",
    yField: "count",
    smooth: true,
    height: 300,
    color: "#00A76F",
    areaStyle: {
      fill: "l(270) 0:rgba(0,167,111,0.01) 1:rgba(0,167,111,0.15)",
    },
    line: {
      style: { lineWidth: 3 },
    },
    point: {
      size: 0,
      style: { fill: "#00A76F" },
    },
    xAxis: {
      label: {
        formatter: (v: string) => {
          const d = new Date(v);
          return `${d.getDate()}.${String(d.getMonth() + 1).padStart(2, "0")}`;
        },
      },
    },
    tooltip: {
      formatter: (datum: any) => ({
        name: "Посылки",
        value: datum.count,
      }),
    },
  };

  const columnConfig = {
    data: revenue,
    xField: "period",
    yField: "amount",
    height: 300,
    color: "#00A76F",
    columnStyle: {
      radius: [6, 6, 0, 0],
    },
    tooltip: {
      formatter: (datum: any) => ({
        name: "Выручка",
        value: `$${datum.amount}`,
      }),
    },
  };

  return (
    <>
      <div className="page-header">
        <Typography.Title className="page-title" level={3}>
          Дашборд
        </Typography.Title>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <Select
            value={period}
            onChange={(v) => { setPeriod(v); if (v !== "custom") setCustomRange(null); }}
            style={{ width: 180 }}
            options={[
              { value: "today", label: "Сегодня" },
              { value: "7d", label: "7 дней" },
              { value: "30d", label: "30 дней" },
              { value: "90d", label: "90 дней" },
              { value: "all", label: "За всё время" },
              { value: "custom", label: "Свой диапазон" },
            ]}
          />
          {period === "custom" && (
            <RangePicker
              value={customRange}
              onChange={(dates) => setCustomRange(dates as [dayjs.Dayjs, dayjs.Dayjs] | null)}
              format="DD.MM.YYYY"
              style={{ borderRadius: 8 }}
            />
          )}
        </div>
      </div>

      <Row gutter={[20, 20]} className="stagger-children">
        {stats.map((s, i) => (
          <Col xs={12} sm={12} lg={6} key={i}>
            <div
              className={s.className}
              style={{
                padding: "24px",
                borderRadius: 16,
                background: s.bg,
                position: "relative",
                overflow: "hidden",
                cursor: "default",
              }}
            >
              <div
                style={{
                  position: "absolute",
                  top: -20,
                  right: -20,
                  width: 120,
                  height: 120,
                  borderRadius: "50%",
                  background: s.color,
                  opacity: 0.08,
                }}
              />
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  marginBottom: 16,
                  position: "relative",
                }}
              >
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: 12,
                    background: s.color,
                    opacity: 0.12,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <span
                    style={{
                      position: "absolute",
                      color: s.color,
                    }}
                  >
                    {s.icon}
                  </span>
                </div>
              </div>
              <div
                style={{
                  fontSize: 32,
                  fontWeight: 700,
                  color: s.color,
                  lineHeight: 1.2,
                  marginBottom: 4,
                  position: "relative",
                }}
              >
                {s.value}
              </div>
              <div
                style={{
                  fontSize: 14,
                  color: s.color,
                  opacity: 0.72,
                  fontWeight: 500,
                  position: "relative",
                }}
              >
                {s.title}
              </div>
            </div>
          </Col>
        ))}
      </Row>

      <Row gutter={[20, 20]} style={{ marginTop: 20 }}>
        <Col xs={24} lg={parcelsByDay.length > 0 ? 14 : 24}>
          {parcelsByDay.length > 0 && (
            <Card
              title={
                <span style={{ fontWeight: 600, fontSize: 16 }}>
                  Посылки по дням
                </span>
              }
              className="animate-fade-in-up hover-card"
              style={{ animationDelay: "0.3s" }}
            >
              <Line {...(lineConfig as any)} />
            </Card>
          )}
          {parcelsByDay.length === 0 && revenue.length === 0 && null}
        </Col>
        {revenue.length > 0 && (
          <Col xs={24} lg={parcelsByDay.length > 0 ? 10 : 24}>
            <Card
              title={
                <span style={{ fontWeight: 600, fontSize: 16 }}>
                  Выручка по неделям
                </span>
              }
              className="animate-fade-in-up hover-card"
              style={{ animationDelay: "0.4s" }}
            >
              <Column {...(columnConfig as any)} />
            </Card>
          </Col>
        )}
      </Row>

      <Row gutter={[20, 20]} style={{ marginTop: 20 }}>
        <Col xs={24} lg={12}>
          <Card
            title={
              <span style={{ fontWeight: 600, fontSize: 16 }}>
                Топ-10 клиентов
              </span>
            }
            className="animate-fade-in-up hover-card"
            style={{ animationDelay: "0.5s" }}
          >
            <Table
              dataSource={topClients}
              rowKey="client_id"
              size="small"
              pagination={false}
              columns={[
                {
                  title: "TPS",
                  dataIndex: "tps_code",
                  width: 100,
                  render: (v: string) => (
                    <span style={{ fontWeight: 600, color: "#00A76F" }}>
                      {v}
                    </span>
                  ),
                },
                { title: "Имя", dataIndex: "full_name" },
                {
                  title: "Сумма",
                  dataIndex: "total_amount",
                  render: (v: number) => (
                    <span style={{ fontWeight: 600 }}>
                      ${v?.toFixed(2) ?? "0.00"}
                    </span>
                  ),
                },
              ]}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card
            title={
              <span style={{ fontWeight: 600, fontSize: 16 }}>
                Зависшие посылки (14+ дней)
              </span>
            }
            className="animate-fade-in-up hover-card"
            style={{ animationDelay: "0.6s" }}
            extra={
              stuck.length > 0 && (
                <span
                  style={{
                    background: "#FFF2E8",
                    color: "#E65100",
                    padding: "4px 12px",
                    borderRadius: 20,
                    fontSize: 12,
                    fontWeight: 600,
                  }}
                >
                  {stuck.length} шт.
                </span>
              )
            }
          >
            <Table
              dataSource={stuck}
              rowKey="parcel_id"
              size="small"
              pagination={false}
              columns={[
                {
                  title: "Трек",
                  dataIndex: "track_id",
                  width: 140,
                  render: (v: string) => (
                    <span style={{ fontFamily: "monospace", fontSize: 13 }}>
                      {v}
                    </span>
                  ),
                },
                { title: "Клиент", dataIndex: "full_name" },
                {
                  title: "Дней",
                  dataIndex: "waiting_days",
                  width: 70,
                  render: (v: number) => (
                    <span
                      style={{
                        color: v > 21 ? "#FF5630" : "#FFAB00",
                        fontWeight: 600,
                      }}
                    >
                      {v}
                    </span>
                  ),
                },
                { title: "Телефон", dataIndex: "phone" },
              ]}
            />
          </Card>
        </Col>
      </Row>
    </>
  );
}
