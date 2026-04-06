import client from './client';

export const getFunds = async (params) => (await client.get('/funds', { params })).data;
export const getFund = async (id) => (await client.get(`/funds/${id}`)).data;
export const createFund = async (data) => (await client.post('/funds', data)).data;
export const updateFund = async (id, data) => (await client.patch(`/funds/${id}`, data)).data;
export const deleteFund = async (id) => (await client.delete(`/funds/${id}`)).data;
