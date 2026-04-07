export const ROLE_LABELS = {
  admin: 'Admin',
  supervisor: 'Supervisor',
  principal: 'Principal',
  regular_user: 'Regular User',
};

export const ROLE_OPTIONS = Object.entries(ROLE_LABELS).map(([value, label]) => ({ value, label }));
