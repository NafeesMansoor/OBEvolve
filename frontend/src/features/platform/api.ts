import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { platformApiClient } from '@/lib/platform-api-client'
import type { InstitutionCreateInput, InstitutionRead } from '@/features/platform/types'

export function useInstitutions() {
  return useQuery<InstitutionRead[]>({
    queryKey: ['platform', 'institutions'],
    queryFn: async () => (await platformApiClient.get<InstitutionRead[]>('/institutions')).data,
  })
}

export function useCreateInstitution() {
  const queryClient = useQueryClient()
  return useMutation<InstitutionRead, unknown, InstitutionCreateInput>({
    mutationFn: async (payload) =>
      (await platformApiClient.post<InstitutionRead>('/institutions', payload)).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['platform', 'institutions'] })
    },
  })
}
