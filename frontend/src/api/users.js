import client from './client';

export const getUsers = async (params) => (await client.get('/users', { params })).data;
