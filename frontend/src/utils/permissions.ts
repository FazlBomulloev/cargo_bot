type Role = "owner" | "admin_china" | "admin_dushanbe";

export function hasAccess(page: string, role: Role, permissions?: string[]): boolean {
  if (role === "owner") return true;
  if (!permissions || permissions.length === 0) return false;
  return permissions.includes(page);
}
