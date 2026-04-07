import client from './client';

export const adminUsersApi = {
  list: () => client.get('/admin/users').then((r) => r.data),
  create: (data) => client.post('/admin/users', data).then((r) => r.data),
  update: (id, data) => client.patch(`/admin/users/${id}`, data).then((r) => r.data),
};
