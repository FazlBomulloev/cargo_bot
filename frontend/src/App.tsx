import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import ParcelsChina from "./pages/ParcelsChina";
import ParcelsDushanbe from "./pages/ParcelsDushanbe";
import ParcelsList from "./pages/ParcelsList";
import ParcelDetail from "./pages/ParcelDetail";
import Issuance from "./pages/Issuance";
import IssuanceHistory from "./pages/IssuanceHistory";
import Clients from "./pages/Clients";
import ClientDetail from "./pages/ClientDetail";
import Unresolved from "./pages/Unresolved";
import Warehouses from "./pages/Warehouses";
import Tariffs from "./pages/Tariffs";
import Staff from "./pages/Staff";
import Settings from "./pages/Settings";
import AuditLog from "./pages/AuditLog";
import Profile from "./pages/Profile";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/parcels-china" element={<ParcelsChina />} />
        <Route path="/parcels-dushanbe" element={<ParcelsDushanbe />} />
        <Route path="/parcels" element={<ParcelsList />} />
        <Route path="/parcels/:id" element={<ParcelDetail />} />
        <Route path="/issuance" element={<Issuance />} />
        <Route path="/issuance-history" element={<IssuanceHistory />} />
        <Route path="/clients" element={<Clients />} />
        <Route path="/clients/:id" element={<ClientDetail />} />
        <Route path="/unresolved" element={<Unresolved />} />
        <Route path="/warehouses" element={<Warehouses />} />
        <Route path="/tariffs" element={<Tariffs />} />
        <Route path="/staff" element={<Staff />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/audit" element={<AuditLog />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
