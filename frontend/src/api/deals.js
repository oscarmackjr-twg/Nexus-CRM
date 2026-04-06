import client from './client';

export const getDeals = async (params) => (await client.get('/deals', { params })).data;
export const getDeal = async (id) => (await client.get(`/deals/${id}`)).data;
export const createDeal = async (data) => (await client.post('/deals', data)).data;
export const updateDeal = async (id, data) => (await client.patch(`/deals/${id}`, data)).data;
export const deleteDeal = async (id) => (await client.delete(`/deals/${id}`)).data;
export const getDealActivities = async (id, params) =>
  (await client.get(`/deals/${id}/activities`, { params })).data;
export const logDealActivity = async (dealId, data) =>
  (await client.post(`/deals/${dealId}/activities`, data)).data;
export const moveDealStage = async (dealId, data) =>
  (await client.post(`/deals/${dealId}/move`, data)).data;
