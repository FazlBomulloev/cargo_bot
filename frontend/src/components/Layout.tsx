import { useState } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  Layout as AntLayout,
  Menu,
  Button,
  Typography,
  Avatar,
  Dropdown,
  Breadcrumb,
  Badge,
} from "antd";
import {
  DashboardOutlined,
  SendOutlined,
  InboxOutlined,
  UnorderedListOutlined,
  ShoppingCartOutlined,
  HistoryOutlined,
  TeamOutlined,
  WarningOutlined,
  HomeOutlined,
  DollarOutlined,
  UserSwitchOutlined,
  SettingOutlined,
  AuditOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
  BellOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import { useAuth } from "../hooks/useAuth";
import { usePermissions } from "../hooks/usePermissions";

const { Sider, Header, Content } = AntLayout;

const routeTitles: Record<string, string> = {
  "/": "Дашборд",
  "/parcels-china": "Склад Китай",
  "/parcels-dushanbe": "Склад Душанбе",
  "/parcels": "Все посылки",
  "/issuance": "Выдача",
  "/issuance-history": "История выдач",
  "/clients": "Клиенты",
  "/unresolved": "Проблемные",
  "/warehouses": "Склады",
  "/tariffs": "Тарифы",
  "/staff": "Сотрудники",
  "/settings": "Настройки",
  "/audit": "Журнал",
};

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout } = useAuth();
  const { can } = usePermissions();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const items = [
    can("dashboard") && {
      key: "/",
      icon: <DashboardOutlined />,
      label: <Link to="/">Дашборд</Link>,
    },
    can("parcels_china") && {
      key: "/parcels-china",
      icon: <SendOutlined />,
      label: <Link to="/parcels-china">Склад Китай</Link>,
    },
    can("parcels_dushanbe") && {
      key: "/parcels-dushanbe",
      icon: <InboxOutlined />,
      label: <Link to="/parcels-dushanbe">Склад Душанбе</Link>,
    },
    can("parcels_list") && {
      key: "/parcels",
      icon: <UnorderedListOutlined />,
      label: <Link to="/parcels">Все посылки</Link>,
    },
    can("issuance") && {
      key: "/issuance",
      icon: <ShoppingCartOutlined />,
      label: <Link to="/issuance">Выдача</Link>,
    },
    can("issuance_history") && {
      key: "/issuance-history",
      icon: <HistoryOutlined />,
      label: <Link to="/issuance-history">История выдач</Link>,
    },
    can("clients") && {
      key: "/clients",
      icon: <TeamOutlined />,
      label: <Link to="/clients">Клиенты</Link>,
    },
    can("unresolved") && {
      key: "/unresolved",
      icon: <WarningOutlined />,
      label: <Link to="/unresolved">Проблемные</Link>,
    },
    can("warehouses") && {
      key: "/warehouses",
      icon: <HomeOutlined />,
      label: <Link to="/warehouses">Склады</Link>,
    },
    can("tariffs") && {
      key: "/tariffs",
      icon: <DollarOutlined />,
      label: <Link to="/tariffs">Тарифы</Link>,
    },
    can("staff") && {
      key: "/staff",
      icon: <UserSwitchOutlined />,
      label: <Link to="/staff">Сотрудники</Link>,
    },
    can("settings") && {
      key: "/settings",
      icon: <SettingOutlined />,
      label: <Link to="/settings">Настройки</Link>,
    },
    can("audit") && {
      key: "/audit",
      icon: <AuditOutlined />,
      label: <Link to="/audit">Журнал</Link>,
    },
  ].filter(Boolean) as any[];

  const userMenuItems = [
    {
      key: "profile",
      icon: <UserOutlined />,
      label: "Профиль",
    },
    {
      key: "settings",
      icon: <SettingOutlined />,
      label: "Настройки",
      onClick: () => navigate("/settings"),
    },
    { type: "divider" as const },
    {
      key: "logout",
      icon: <LogoutOutlined />,
      label: "Выйти",
      danger: true,
      onClick: handleLogout,
    },
  ];

  const roleColors: Record<string, string> = {
    owner: "#00A76F",
    admin_china: "#00B8D9",
    admin_dushanbe: "#FFAB00",
  };

  const roleLabels: Record<string, string> = {
    owner: "Владелец",
    admin_china: "Админ Китай",
    admin_dushanbe: "Админ Душанбе",
  };

  return (
    <AntLayout style={{ minHeight: "100vh" }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        breakpoint="lg"
        width={280}
        collapsedWidth={80}
        className="custom-sidebar"
        trigger={null}
        style={{
          background: "#1C252E",
          overflow: "auto",
          height: "100vh",
          position: "fixed",
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 100,
          transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        }}
      >
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">C</div>
          {!collapsed && (
            <span className="sidebar-logo-text">Cargo TPS</span>
          )}
        </div>

        <div
          style={{
            margin: collapsed ? "12px 8px" : "12px 16px",
            padding: collapsed ? "12px 8px" : "14px 16px",
            background: "rgba(145, 158, 171, 0.08)",
            borderRadius: 12,
            display: "flex",
            alignItems: "center",
            gap: 12,
            transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
            overflow: "hidden",
          }}
        >
          <Avatar
            size={36}
            style={{
              background: (user?.role ? roleColors[user.role] : undefined) || "#00A76F",
              flexShrink: 0,
              fontSize: 14,
              fontWeight: 600,
            }}
          >
            {user?.full_name?.charAt(0)?.toUpperCase() || "U"}
          </Avatar>
          {!collapsed && (
            <div style={{ overflow: "hidden", minWidth: 0 }}>
              <div
                style={{
                  color: "#fff",
                  fontWeight: 600,
                  fontSize: 14,
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {user?.full_name}
              </div>
              <div
                style={{
                  color: "rgba(145, 158, 171, 0.8)",
                  fontSize: 12,
                }}
              >
                {(user?.role ? roleLabels[user.role] : undefined) || user?.role}
              </div>
            </div>
          )}
        </div>

        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={items}
          style={{ marginTop: 8 }}
        />
      </Sider>

      <AntLayout
        style={{
          marginLeft: collapsed ? 80 : 280,
          transition: "margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
          background: "#F4F6F8",
        }}
      >
        <Header
          className="main-header"
          style={{
            padding: "0 24px",
            height: 64,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            position: "sticky",
            top: 0,
            zIndex: 99,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              style={{
                fontSize: 18,
                width: 40,
                height: 40,
                borderRadius: 10,
              }}
            />
            <Breadcrumb
              items={[
                { title: "Cargo TPS" },
                { title: routeTitles[location.pathname] || "Страница" },
              ]}
              style={{ display: "none" }}
            />
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Button
              type="text"
              icon={<SearchOutlined />}
              style={{ width: 40, height: 40, borderRadius: 10 }}
            />
            <Badge count={0} offset={[-4, 4]}>
              <Button
                type="text"
                icon={<BellOutlined />}
                style={{ width: 40, height: 40, borderRadius: 10 }}
              />
            </Badge>
            <Dropdown
              menu={{ items: userMenuItems }}
              placement="bottomRight"
              trigger={["click"]}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  cursor: "pointer",
                  padding: "6px 12px",
                  borderRadius: 10,
                  transition: "all 0.3s",
                  marginLeft: 4,
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.background = "rgba(145,158,171,0.08)")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.background = "transparent")
                }
              >
                <Avatar
                  size={36}
                  style={{
                    background: (user?.role ? roleColors[user.role] : undefined) || "#00A76F",
                    fontWeight: 600,
                  }}
                >
                  {user?.full_name?.charAt(0)?.toUpperCase() || "U"}
                </Avatar>
                <div style={{ lineHeight: 1.3, textAlign: "right" }}>
                  <div
                    style={{
                      fontWeight: 600,
                      fontSize: 14,
                      color: "#1C252E",
                    }}
                  >
                    {user?.full_name}
                  </div>
                  <div style={{ fontSize: 12, color: "#919EAB" }}>
                    {(user?.role ? roleLabels[user.role] : undefined) || user?.role}
                  </div>
                </div>
              </div>
            </Dropdown>
          </div>
        </Header>

        <Content
          style={{
            margin: 24,
            minHeight: "calc(100vh - 64px - 48px)",
          }}
        >
          <div className="page-content">
            <Outlet />
          </div>
        </Content>
      </AntLayout>
    </AntLayout>
  );
}
