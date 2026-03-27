import client from './client';

export const getRefData = async (category) =>
  (await client.get('/admin/ref-data', { params: { category } })).data;

export const createRefData = async (data) =>
  (await client.post('/admin/ref-data', data)).data;

export const updateRefData = async (id, data) =>
  (await client.patch(`/admin/ref-data/${id}`, data)).data;
