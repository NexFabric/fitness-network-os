/** Canonical role names — must match backend/permissions.yml. */
export const ROLES = {
  PLATFORM_SUPER_ADMIN: 'PLATFORM_SUPER_ADMIN',
  FEDERATION_ADMIN: 'FEDERATION_ADMIN',
  FEDERATION_ANALYST: 'FEDERATION_ANALYST',
  FEDERATION_SUPPORT: 'FEDERATION_SUPPORT',
  GYM_OWNER: 'GYM_OWNER',
  GYM_ADMIN: 'GYM_ADMIN',
  GYM_MANAGER: 'GYM_MANAGER',
  ACCOUNTANT: 'ACCOUNTANT',
  FRONT_DESK: 'FRONT_DESK',
  TRAINER: 'TRAINER',
  MEMBER: 'MEMBER',
} as const

export type RoleName = (typeof ROLES)[keyof typeof ROLES]

export const FEDERATION_ROLES: RoleName[] = [
  ROLES.PLATFORM_SUPER_ADMIN,
  ROLES.FEDERATION_ADMIN,
  ROLES.FEDERATION_ANALYST,
  ROLES.FEDERATION_SUPPORT,
]

/** Roles that belong in the tenant operations console. */
export const OPS_ROLES: RoleName[] = [
  ROLES.GYM_OWNER,
  ROLES.GYM_ADMIN,
  ROLES.GYM_MANAGER,
  ROLES.ACCOUNTANT,
  ROLES.FRONT_DESK,
]

/** Front-desk reception workspace — must match backend reception:read grants. */
export const RECEPTION_ROLES: RoleName[] = [
  ROLES.GYM_OWNER,
  ROLES.GYM_ADMIN,
  ROLES.GYM_MANAGER,
  ROLES.FRONT_DESK,
]

export const TRAINER_ROLES: RoleName[] = [ROLES.TRAINER]

export const MEMBER_ROLES: RoleName[] = [ROLES.MEMBER]

/**
 * Where a principal lands after login.
 *
 * Ordered most-privileged first so a user holding several roles gets the
 * broadest console rather than being trapped in the narrowest one.
 */
export function homeRouteFor(roles: string[], isSuperuser: boolean): string {
  if (isSuperuser || roles.some((r) => FEDERATION_ROLES.includes(r as RoleName))) {
    return '/superadmin'
  }
  if (roles.some((r) => OPS_ROLES.includes(r as RoleName))) {
    return '/'
  }
  if (roles.includes(ROLES.TRAINER)) {
    return '/trainer'
  }
  if (roles.includes(ROLES.MEMBER)) {
    return '/member'
  }
  // Authenticated but holding no portal role — the gateway explains why.
  return '/portal'
}
