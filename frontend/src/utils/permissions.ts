type Role = "owner" | "admin_china" | "admin_dushanbe";

const matrix: Record<string, Role[]> = {
  dashboard: ["owner"],
  parcels_china: ["owner", "admin_china"],
  parcels_china_list: ["owner", "admin_china", "admin_dushanbe"],
  parcels_dushanbe: ["owner", "admin_dushanbe"],
  parcels_list: ["owner", "admin_dushanbe"],
  parcel_detail: ["owner", "admin_dushanbe"],
  issuance: ["owner", "admin_dushanbe"],
  issuance_history: ["owner", "admin_dushanbe"],
  clients: ["owner", "admin_dushanbe"],
  unresolved: ["owner", "admin_dushanbe"],
  warehouses: ["owner", "admin_dushanbe"],
  tariffs: ["owner", "admin_dushanbe"],
  staff: ["owner"],
  settings: ["owner", "admin_dushanbe"],
  audit: ["owner", "admin_dushanbe"],
};

export function hasAccess(page: string, role: Role): boolean {
  return matrix[page]?.includes(role) ?? false;
}
