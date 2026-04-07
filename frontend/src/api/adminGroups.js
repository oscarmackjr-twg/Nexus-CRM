import client from './client';

export const adminGroupsApi = {
  list: (includeInactive = false) =>
    client.get(`/admin/groups?include_inactive=${includeInactive}`).then((r) => r.data),
  create: (data) => client.post('/admin/groups', data).then((r) => r.data),
  update: (id, data) => client.patch(`/admin/groups/${id}`, data).then((r) => r.data),
};
