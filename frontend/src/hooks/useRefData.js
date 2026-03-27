import { useQuery } from '@tanstack/react-query';
import { getRefData } from '@/api/refData';

export function useRefData(category) {
  return useQuery({
    queryKey: ['ref', category],
    queryFn: () => getRefData(category),
    staleTime: 5 * 60 * 1000,
    enabled: Boolean(category),
  });
}
