import { useAuth } from "./useAuth";
import { hasAccess } from "../utils/permissions";

export function usePermissions() {
  const { user } = useAuth();
  const role = user?.role ?? "admin_china";
  const permissions = user?.permissions ?? [];
  return {
    can: (page: string) => hasAccess(page, role, permissions),
    role,
  };
}
