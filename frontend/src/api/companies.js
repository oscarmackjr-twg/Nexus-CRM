import client from './client';

export const getCompanies = async (params) => (await client.get('/companies', { params })).data;
export const getCompany = async (id) => (await client.get(`/companies/${id}`)).data;
export const getCompanyContacts = async (id) => (await client.get(`/companies/${id}/contacts`)).data;
export const getCompanyDeals = async (id) => (await client.get(`/companies/${id}/deals`)).data;
export const updateCompany = async (id, data) => (await client.patch(`/companies/${id}`, data)).data;
export const syncCompanyLinkedIn = async (id) => (await client.post(`/companies/${id}/linkedin-sync`)).data;
