import client from './client';

export const getPipelines = async () => (await client.get('/pipelines')).data;
