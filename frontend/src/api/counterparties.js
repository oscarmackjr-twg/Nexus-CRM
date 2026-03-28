import client from './client';

export const getCounterparties = async (dealId, params) =>
  (await client.get(`/deals/${dealId}/counterparties`, { params })).data;
export const createCounterparty = async (dealId, data) =>
  (await client.post(`/deals/${dealId}/counterparties`, data)).data;
export const updateCounterparty = async (dealId, id, data) =>
  (await client.patch(`/deals/${dealId}/counterparties/${id}`, data)).data;
export const deleteCounterparty = async (dealId, id) =>
  (await client.delete(`/deals/${dealId}/counterparties/${id}`)).data;
