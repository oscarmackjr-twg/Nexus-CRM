import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Pencil, X } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '@/hooks/useAuth';
import { adminUsersApi } from '@/api/adminUsers';
import { adminGroupsApi } from '@/api/adminGroups';
import { ROLE_LABELS, ROLE_OPTIONS } from '@/lib/roles';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { DataGrid } from '@/components/DataGrid';

const ROLE_BADGE_VARIANT = {
  admin: 'default',
  supervisor: 'secondary',
  principal: 'outline',
  regular_user: 'outline',
};

const PAGE_SIZE_OPTIONS = [10, 20, 50];

export default function AdminUsersPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [addOpen, setAddOpen] = useState(false);
  const [editUser, setEditUser] = useState(null);

  // Form state — create
  const [newName, setNewName] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState('regular_user');
  const [newGroupId, setNewGroupId] = useState('');

  // Form state — edit
  const [editRole, setEditRole] = useState('');
  const [editGroupId, setEditGroupId] = useState('');

  const usersQuery = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: () => adminUsersApi.list(),
    enabled: user?.role === 'admin',
  });

  const groupsQuery = useQuery({
    queryKey: ['admin', 'groups'],
    queryFn: () => adminGroupsApi.list(false),
    enabled: user?.role === 'admin',
  });

  const createMutation = useMutation({
    mutationFn: (data) => adminUsersApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      toast.success('User created');
      setAddOpen(false);
      resetAddForm();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Failed to save changes'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => adminUsersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      toast.success('User updated');
      setEditUser(null);
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Failed to save changes'),
  });

  if (user?.role !== 'admin') {
    return (
      <Card>
        <CardContent className="p-6 text-sm text-muted-foreground">
          Admin access is restricted to admins.
        </CardContent>
      </Card>
    );
  }

  function resetAddForm() {
    setNewName('');
    setNewEmail('');
    setNewPassword('');
    setNewRole('regular_user');
    setNewGroupId('');
  }

  function openEdit(u) {
    setEditUser(u);
    setEditRole(u.role);
    setEditGroupId(u.team_id || '');
  }

  function handleDeactivate(u) {
    if (window.confirm(`Deactivate ${u.full_name || u.email}? They will no longer be able to log in.`)) {
      updateMutation.mutate({ id: u.id, data: { is_active: false } });
    }
  }

  function handleCreate() {
    if (!newName.trim() || !newEmail.trim() || !newPassword.trim()) {
      toast.error('Name, email, and password are required');
      return;
    }
    const payload = {
      full_name: newName.trim(),
      email: newEmail.trim(),
      password: newPassword,
      role: newRole,
    };
    if (newGroupId) payload.team_id = newGroupId;
    createMutation.mutate(payload);
  }

  function handleUpdate() {
    const payload = { role: editRole };
    if (editGroupId) payload.team_id = editGroupId;
    updateMutation.mutate({ id: editUser.id, data: payload });
  }

  const users = usersQuery.data || [];
  const activeGroups = (groupsQuery.data || []).filter((g) => g.is_active);
  const totalUsers = users.length;
  const totalPages = Math.max(1, Math.ceil(totalUsers / pageSize));
  const pagedUsers = users.slice((page - 1) * pageSize, page * pageSize);

  const columns = [
    {
      key: 'full_name',
      label: 'Name',
      render: (row) => row.full_name || '—',
    },
    {
      key: 'email',
      label: 'Email',
    },
    {
      key: 'group_name',
      label: 'Group',
      render: (row) => row.group_name || '—',
    },
    {
      key: 'role',
      label: 'Role',
      sortable: false,
      render: (row) => (
        <Badge variant={ROLE_BADGE_VARIANT[row.role] || 'outline'}>
          {ROLE_LABELS[row.role] || row.role}
        </Badge>
      ),
    },
    {
      key: 'is_active',
      label: 'Status',
      sortable: false,
      render: (row) => (
        <Badge variant={row.is_active ? 'default' : 'secondary'}>
          {row.is_active ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
    {
      key: '_actions',
      label: 'Actions',
      sortable: false,
      render: (row) => (
        <div className="invisible group-hover:visible flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            aria-label="Edit user"
            onClick={(e) => { e.stopPropagation(); openEdit(row); }}
          >
            <Pencil className="h-4 w-4" />
          </Button>
          {row.is_active && (
            <Button
              variant="ghost"
              size="icon"
              aria-label="Deactivate user"
              onClick={(e) => { e.stopPropagation(); handleDeactivate(row); }}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>User Management</CardTitle>
          <Button onClick={() => { resetAddForm(); setAddOpen(true); }}>Add User</Button>
        </CardHeader>
        <CardContent className="p-6">
          {usersQuery.isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-8 w-full rounded-md" />
              ))}
            </div>
          ) : (
            <DataGrid
              columns={columns}
              data={pagedUsers}
              total={totalUsers}
              page={page}
              pages={totalPages}
              size={pageSize}
              onPageChange={setPage}
              onSizeChange={(s) => { setPageSize(s); setPage(1); }}
              emptyHeading="No users found"
              emptyBody="Add your first user to get started."
            />
          )}
        </CardContent>
      </Card>

      {/* Create User Dialog */}
      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Add User</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <div className="space-y-2">
              <Label htmlFor="new-user-name">Name</Label>
              <Input
                id="new-user-name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Full name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-user-email">Email</Label>
              <Input
                id="new-user-email"
                type="email"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                placeholder="email@example.com"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-user-password">Password</Label>
              <Input
                id="new-user-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Password"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-user-role">Role</Label>
              <Select value={newRole} onValueChange={setNewRole}>
                <SelectTrigger id="new-user-role">
                  <SelectValue placeholder="Select role" />
                </SelectTrigger>
                <SelectContent>
                  {ROLE_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-user-group">Group</Label>
              <Select value={newGroupId} onValueChange={setNewGroupId}>
                <SelectTrigger id="new-user-group">
                  <SelectValue placeholder="Select group (optional)" />
                </SelectTrigger>
                <SelectContent>
                  {activeGroups.map((g) => (
                    <SelectItem key={g.id} value={g.id}>
                      {g.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setAddOpen(false)}>
                Never Mind
              </Button>
              <Button
                onClick={handleCreate}
                disabled={createMutation.isPending}
              >
                Add User
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog open={!!editUser} onOpenChange={(open) => { if (!open) setEditUser(null); }}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Edit User</DialogTitle>
          </DialogHeader>
          {editUser && (
            <div className="space-y-4 pt-2">
              <div className="space-y-2">
                <Label htmlFor="edit-user-name">Name</Label>
                <Input
                  id="edit-user-name"
                  value={editUser.full_name || ''}
                  disabled
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-user-email">Email</Label>
                <Input
                  id="edit-user-email"
                  value={editUser.email}
                  disabled
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-user-role">Role</Label>
                <Select value={editRole} onValueChange={setEditRole}>
                  <SelectTrigger id="edit-user-role">
                    <SelectValue placeholder="Select role" />
                  </SelectTrigger>
                  <SelectContent>
                    {ROLE_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-user-group">Group</Label>
                <Select value={editGroupId} onValueChange={setEditGroupId}>
                  <SelectTrigger id="edit-user-group">
                    <SelectValue placeholder="Select group (optional)" />
                  </SelectTrigger>
                  <SelectContent>
                    {activeGroups.map((g) => (
                      <SelectItem key={g.id} value={g.id}>
                        {g.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={() => setEditUser(null)}>
                  Discard Changes
                </Button>
                <Button
                  onClick={handleUpdate}
                  disabled={updateMutation.isPending}
                >
                  Update User
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
