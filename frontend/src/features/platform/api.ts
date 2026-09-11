import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { platformApiClient } from '@/lib/platform-api-client'
import type {
  InstitutionAdminCreateInput,
  InstitutionAdminCreateResult,
  InstitutionAdminRead,
  InstitutionAdminResetPasswordResult,
  InstitutionCreateInput,
  InstitutionCreateResult,
  InstitutionRead,
  InstitutionStatus,
  PermissionCatalogueEntry,
  RoleTemplateCreateInput,
  RoleTemplateRead,
  RoleTemplateResyncResult,
  RoleTemplateUpdateInput,
} from '@/features/platform/types'

export function useInstitutions() {
  return useQuery<InstitutionRead[]>({
    queryKey: ['platform', 'institutions'],
    queryFn: async () => (await platformApiClient.get<InstitutionRead[]>('/institutions')).data,
  })
}

export function useCreateInstitution() {
  const queryClient = useQueryClient()
  return useMutation<InstitutionCreateResult, unknown, InstitutionCreateInput>({
    mutationFn: async (payload) =>
      (await platformApiClient.post<InstitutionCreateResult>('/institutions', payload)).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['platform', 'institutions'] })
    },
  })
}

export function useUpdateInstitutionStatus() {
  const queryClient = useQueryClient()
  return useMutation<InstitutionRead, unknown, { institutionId: string; status: InstitutionStatus }>({
    mutationFn: async ({ institutionId, status }) =>
      (
        await platformApiClient.patch<InstitutionRead>(`/institutions/${institutionId}/status`, {
          status,
        })
      ).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['platform', 'institutions'] })
    },
  })
}

export function useInstitutionAdmins(institutionId: string | null) {
  return useQuery<InstitutionAdminRead[]>({
    queryKey: ['platform', 'institutions', institutionId, 'admins'],
    queryFn: async () =>
      (
        await platformApiClient.get<InstitutionAdminRead[]>(
          `/institutions/${institutionId}/admins`,
        )
      ).data,
    enabled: institutionId !== null,
  })
}

export function useCreateInstitutionAdmin(institutionId: string | null) {
  const queryClient = useQueryClient()
  return useMutation<InstitutionAdminCreateResult, unknown, InstitutionAdminCreateInput>({
    mutationFn: async (payload) =>
      (
        await platformApiClient.post<InstitutionAdminCreateResult>(
          `/institutions/${institutionId}/admins`,
          payload,
        )
      ).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['platform', 'institutions', institutionId, 'admins'],
      })
    },
  })
}

export function useResetInstitutionAdminPassword(institutionId: string | null) {
  return useMutation<InstitutionAdminResetPasswordResult, unknown, { userId: string }>({
    mutationFn: async ({ userId }) =>
      (
        await platformApiClient.post<InstitutionAdminResetPasswordResult>(
          `/institutions/${institutionId}/admins/${userId}/reset-password`,
        )
      ).data,
  })
}

export function usePermissionCatalogue() {
  return useQuery<PermissionCatalogueEntry[]>({
    queryKey: ['platform', 'permission-catalogue'],
    queryFn: async () =>
      (await platformApiClient.get<PermissionCatalogueEntry[]>('/role-templates/permission-catalogue'))
        .data,
  })
}

export function useRoleTemplates() {
  return useQuery<RoleTemplateRead[]>({
    queryKey: ['platform', 'role-templates'],
    queryFn: async () =>
      (await platformApiClient.get<RoleTemplateRead[]>('/role-templates')).data,
  })
}

export function useCreateRoleTemplate() {
  const queryClient = useQueryClient()
  return useMutation<RoleTemplateRead, unknown, RoleTemplateCreateInput>({
    mutationFn: async (payload) =>
      (await platformApiClient.post<RoleTemplateRead>('/role-templates', payload)).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['platform', 'role-templates'] })
    },
  })
}

export function useUpdateRoleTemplate() {
  const queryClient = useQueryClient()
  return useMutation<RoleTemplateRead, unknown, { id: string; body: RoleTemplateUpdateInput }>({
    mutationFn: async ({ id, body }) =>
      (await platformApiClient.patch<RoleTemplateRead>(`/role-templates/${id}`, body)).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['platform', 'role-templates'] })
    },
  })
}

export function useDeleteRoleTemplate() {
  const queryClient = useQueryClient()
  return useMutation<void, unknown, string>({
    mutationFn: async (id) => {
      await platformApiClient.delete(`/role-templates/${id}`)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['platform', 'role-templates'] })
    },
  })
}

/** Re-applies the current role-template catalogue to every already-
 * provisioned institution — a template create/edit above only affects
 * *new* institutions until this runs (app.services.tenancy.resync_role_templates). */
export function useResyncRoleTemplates() {
  return useMutation<RoleTemplateResyncResult, unknown, void>({
    mutationFn: async () =>
      (await platformApiClient.post<RoleTemplateResyncResult>('/role-templates/resync')).data,
  })
}
