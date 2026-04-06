import client from './client';

export const getAISuggestions = async (params) =>
  (await client.get('/ai/suggestions', { params })).data;
export const getContactInsights = async (contactId) =>
  (await client.get(`/ai/contacts/${contactId}/insights`)).data;
export const queryAI = async (data) => (await client.post('/ai/query', data)).data;
