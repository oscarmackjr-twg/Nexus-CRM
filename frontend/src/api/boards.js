import client from './client';

export const getBoards = async (params) => (await client.get('/boards', { params })).data;
export const getBoard = async (id) => (await client.get(`/boards/${id}`)).data;
export const createBoard = async (data) => (await client.post('/boards', data)).data;
export const updateBoard = async (id, data) => (await client.patch(`/boards/${id}`, data)).data;
export const deleteBoard = async (id) => (await client.delete(`/boards/${id}`)).data;
