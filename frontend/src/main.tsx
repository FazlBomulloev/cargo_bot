import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ConfigProvider } from "antd";
import ruRU from "antd/locale/ru_RU";
import App from "./App";
import "./global.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={ruRU}
      theme={{
        token: {
          colorPrimary: "#00A76F",
          colorSuccess: "#22C55E",
          colorWarning: "#FFAB00",
          colorError: "#FF5630",
          colorInfo: "#00B8D9",
          borderRadius: 10,
          fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
          fontSize: 14,
          colorBgContainer: "#FFFFFF",
          colorBgLayout: "#F4F6F8",
          colorText: "#1C252E",
          colorTextSecondary: "#637381",
          controlHeight: 40,
        },
        components: {
          Button: {
            borderRadius: 10,
            controlHeight: 40,
            fontWeight: 600,
          },
          Card: {
            borderRadius: 16,
          },
          Input: {
            borderRadius: 10,
            controlHeight: 40,
          },
          Select: {
            borderRadius: 10,
            controlHeight: 40,
          },
          Table: {
            borderRadius: 12,
            headerBg: "#F4F6F8",
            headerColor: "#637381",
          },
          Tag: {
            borderRadiusSM: 6,
          },
          Modal: {
            borderRadius: 16,
          },
          Menu: {
            itemBorderRadius: 8,
          },
        },
      }}
    >
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ConfigProvider>
  </React.StrictMode>,
);
