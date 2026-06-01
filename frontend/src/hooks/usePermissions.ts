import { useAuth } from "./useAuth";
import { hasAccess } from "../utils/permissions";

export function usePermissions() {
  const { user } = useAuth();
  const role = user?.role ?? "admin_china";
  return {
    can: (page: string) => hasAccess(page, role),
    role,
  };
}
