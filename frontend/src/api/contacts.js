import client from './client';

export const getContacts = async (params) => (await client.get('/contacts', { params })).data;
export const getContact = async (id) => (await client.get(`/contacts/${id}`)).data;
export const createContact = async (data) => (await client.post('/contacts', data)).data;
export const updateContact = async (id, data) => (await client.patch(`/contacts/${id}`, data)).data;
export const syncContactLinkedIn = async (id) => (await client.post(`/contacts/${id}/linkedin-sync`)).data;
export const getContactDeals = async (id) => (await client.get(`/contacts/${id}/deals`)).data;
export const getContactActivities = async (id, params) => (await client.get(`/contacts/${id}/activities`, { params })).data;
export const logContactActivity = async (contactId, data) =>
  (await client.post(`/contacts/${contactId}/activities`, data)).data;
