import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Pencil, X } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '@/hooks/useAuth';
import { adminGroupsApi } from '@/api/adminGroups';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import { DataGrid } from '@/components/DataGrid';

const PAGE_SIZE_OPTIONS = [10, 20, 50];

export default function AdminGroupsPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const [includeInactive, setIncludeInactive] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  // Add dialog
  const [addOpen, setAddOpen] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');

  // Rename dialog
  const [renameGroup, setRenameGroup] = useState(null);
  const [renameValue, setRenameValue] = useState('');

  const groupsQuery = useQuery({
    queryKey: ['admin', 'groups', includeInactive],
    queryFn: () => adminGroupsApi.list(includeInactive),
  });

  const createMutation = useMutation({
    mutationFn: (data) => adminGroupsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'groups'] });
      toast.success('Group created');
      setAddOpen(false);
      setNewGroupName('');
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Failed to save changes'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => adminGroupsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'groups'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      toast.success('Group updated');
      setRenameGroup(null);
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

  function openRename(group) {
    setRenameGroup(group);
    setRenameValue(group.name);
  }

  function handleDeactivate(group) {
    if (
      window.confirm(
        `Deactivate "${group.name}"? Users in this group will lose their group assignment. This cannot be undone from the UI.`
      )
    ) {
      updateMutation.mutate({ id: group.id, data: { is_active: false } });
    }
  }

  function handleCreate() {
    if (!newGroupName.trim()) {
      toast.error('Group name is required');
      return;
    }
    createMutation.mutate({ name: newGroupName.trim() });
  }

  function handleRename() {
    if (!renameValue.trim()) {
      toast.error('Group name is required');
      return;
    }
    updateMutation.mutate({ id: renameGroup.id, data: { name: renameValue.trim() } });
  }

  const groups = groupsQuery.data || [];
  const totalGroups = groups.length;
  const totalPages = Math.max(1, Math.ceil(totalGroups / pageSize));
  const pagedGroups = groups.slice((page - 1) * pageSize, page * pageSize);

  const columns = [
    {
      key: 'name',
      label: 'Group Name',
    },
    {
      key: 'member_count',
      label: 'Members',
      render: (row) => row.member_count ?? 0,
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
            aria-label="Rename group"
            onClick={(e) => { e.stopPropagation(); openRename(row); }}
          >
            <Pencil className="h-4 w-4" />
          </Button>
          {row.is_active && (
            <Button
              variant="ghost"
              size="icon"
              aria-label="Deactivate group"
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
          <CardTitle>Group Management</CardTitle>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Switch
                id="show-inactive"
                checked={includeInactive}
                onCheckedChange={(checked) => {
                  setIncludeInactive(checked);
                  setPage(1);
                }}
              />
              <Label htmlFor="show-inactive" className="text-sm cursor-pointer">
                Show inactive
              </Label>
            </div>
            <Button onClick={() => { setNewGroupName(''); setAddOpen(true); }}>Add Group</Button>
          </div>
        </CardHeader>
        <CardContent className="p-6">
          {groupsQuery.isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-8 w-full rounded-md" />
              ))}
            </div>
          ) : (
            <DataGrid
              columns={columns}
              data={pagedGroups}
              total={totalGroups}
              page={page}
              pages={totalPages}
              size={pageSize}
              onPageChange={setPage}
              onSizeChange={(s) => { setPageSize(s); setPage(1); }}
              emptyHeading="No groups found"
              emptyBody="Create your first group to start organizing users."
            />
          )}
        </CardContent>
      </Card>

      {/* Create Group Dialog */}
      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Create Group</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <div className="space-y-2">
              <Label htmlFor="new-group-name">Group Name</Label>
              <Input
                id="new-group-name"
                value={newGroupName}
                onChange={(e) => setNewGroupName(e.target.value)}
                placeholder="Group name"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setAddOpen(false)}>
                Never Mind
              </Button>
              <Button
                onClick={handleCreate}
                disabled={createMutation.isPending}
              >
                Create Group
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Rename Group Dialog */}
      <Dialog open={!!renameGroup} onOpenChange={(open) => { if (!open) setRenameGroup(null); }}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Rename Group</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <div className="space-y-2">
              <Label htmlFor="rename-group-name">Group Name</Label>
              <Input
                id="rename-group-name"
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                placeholder="Group name"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setRenameGroup(null)}>
                Discard
              </Button>
              <Button
                onClick={handleRename}
                disabled={updateMutation.isPending}
              >
                Rename Group
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
