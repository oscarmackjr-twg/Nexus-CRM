import client from './client';

export const getFunding = async (dealId, params) =>
  (await client.get(`/deals/${dealId}/funding`, { params })).data;
export const createFunding = async (dealId, data) =>
  (await client.post(`/deals/${dealId}/funding`, data)).data;
export const updateFunding = async (dealId, id, data) =>
  (await client.patch(`/deals/${dealId}/funding/${id}`, data)).data;
export const deleteFunding = async (dealId, id) =>
  (await client.delete(`/deals/${dealId}/funding/${id}`)).data;
