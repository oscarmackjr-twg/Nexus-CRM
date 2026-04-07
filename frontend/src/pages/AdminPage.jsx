import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Pencil, RotateCcw, X } from 'lucide-react';
import { toast } from 'sonner';
import { getUsers } from '@/api/users';
import { getAllRefData, createRefData, updateRefData } from '@/api/refData';
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';
import { REF_CATEGORIES } from '@/lib/refCategories';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function AdminPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  // Users tab state
  const usersQuery = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: () => getUsers({ size: 100 }).then((data) => data.items || data),
    enabled: user?.role === 'admin',
  });

  // Reference Data tab state
  const [selectedCategory, setSelectedCategory] = useState('sector');
  const [modalOpen, setModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formLabel, setFormLabel] = useState('');
  const [formPosition, setFormPosition] = useState('');

  const itemsQuery = useQuery({
    queryKey: ['admin', 'ref-data', selectedCategory],
    queryFn: () => getAllRefData(selectedCategory),
    enabled: Boolean(selectedCategory),
  });

  const createMutation = useMutation({
    mutationFn: (data) => createRefData(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ref'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'ref-data'] });
      toast.success('Item added');
      setModalOpen(false);
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Failed to add item'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => updateRefData(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ref'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'ref-data'] });
      toast.success('Item updated');
      setModalOpen(false);
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Failed to update item'),
  });

  if (user?.role !== 'admin') {
    return (
      <Card>
        <CardContent className="p-6 text-sm text-muted-foreground">
          Admin access is restricted to org and super admins.
        </CardContent>
      </Card>
    );
  }

  function openAddModal() {
    setEditingItem(null);
    setFormLabel('');
    setFormPosition('');
    setModalOpen(true);
  }

  function openEditModal(item) {
    setEditingItem(item);
    setFormLabel(item.label);
    setFormPosition(item.position != null ? String(item.position) : '');
    setModalOpen(true);
  }

  function handleSave() {
    if (!formLabel.trim()) {
      toast.error('Label is required');
      return;
    }
    if (editingItem) {
      updateMutation.mutate({
        id: editingItem.id,
        data: {
          label: formLabel.trim(),
          ...(formPosition !== '' ? { position: Number(formPosition) } : {}),
        },
      });
    } else {
      createMutation.mutate({
        category: selectedCategory,
        label: formLabel.trim(),
        value: formLabel.trim().toLowerCase().replace(/\s+/g, '_'),
        ...(formPosition !== '' ? { position: Number(formPosition) } : {}),
      });
    }
  }

  function handleToggleActive(item) {
    updateMutation.mutate({ id: item.id, data: { is_active: !item.is_active } });
  }

  const items = itemsQuery.data || [];
  const sortedItems = [...items].sort((a, b) => {
    const posA = a.position ?? Number.MAX_SAFE_INTEGER;
    const posB = b.position ?? Number.MAX_SAFE_INTEGER;
    if (posA !== posB) return posA - posB;
    return a.label.localeCompare(b.label);
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Admin</h1>
      </div>

      <Tabs defaultValue="users">
        <TabsList>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="ref-data">Reference Data</TabsTrigger>
        </TabsList>

        {/* Users tab */}
        <TabsContent value="users" className="space-y-6 pt-4">
          {usersQuery.isLoading ? (
            <Skeleton className="h-80 w-full" />
          ) : (
            <>
              <Card>
                <CardHeader><CardTitle>Org snapshot</CardTitle></CardHeader>
                <CardContent className="flex gap-3">
                  {['admin', 'supervisor', 'principal', 'regular_user'].map((role) => (
                    <Badge key={role}>
                      {role}: {(usersQuery.data || []).filter((m) => m.role === role).length}
                    </Badge>
                  ))}
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Users</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  {(usersQuery.data || []).map((member) => (
                    <div key={member.id} className="rounded-xl bg-muted/40 p-4">
                      <p className="font-medium">{member.full_name || member.username}</p>
                      <p className="text-sm text-muted-foreground">{member.email}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Reference Data tab */}
        <TabsContent value="ref-data" className="pt-4">
          <div className="flex gap-6">
            {/* Category sidebar */}
            <div className="w-48 shrink-0 space-y-1">
              {REF_CATEGORIES.map((cat) => (
                <button
                  key={cat.slug}
                  onClick={() => setSelectedCategory(cat.slug)}
                  className={cn(
                    'w-full text-left px-3 py-2 rounded-lg text-sm',
                    selectedCategory === cat.slug
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  )}
                >
                  {cat.label}
                </button>
              ))}
            </div>

            {/* Items panel */}
            <div className="flex-1">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-medium">
                  {REF_CATEGORIES.find((c) => c.slug === selectedCategory)?.label}
                </h2>
                <Button size="sm" onClick={openAddModal}>+ Add Item</Button>
              </div>

              {itemsQuery.isLoading ? (
                <Skeleton className="h-64 w-full" />
              ) : sortedItems.length === 0 ? (
                <p className="text-sm text-muted-foreground py-8 text-center">
                  No items in this category. Add the first one.
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Label</TableHead>
                      <TableHead>Position</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="w-20">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {sortedItems.map((item) => (
                      <TableRow key={item.id} className={item.is_active ? '' : 'opacity-50'}>
                        <TableCell className="font-medium">{item.label}</TableCell>
                        <TableCell>{item.position ?? '—'}</TableCell>
                        <TableCell>
                          <Badge variant={item.is_active ? 'default' : 'secondary'}>
                            {item.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => openEditModal(item)}
                            >
                              <Pencil className="h-4 w-4" />
                            </Button>
                            {item.is_active ? (
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleToggleActive(item)}
                              >
                                <X className="h-4 w-4" />
                              </Button>
                            ) : (
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleToggleActive(item)}
                              >
                                <RotateCcw className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* Add / Edit modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingItem ? 'Edit Item' : 'Add Item'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <div className="space-y-2">
              <Label htmlFor="ref-label">Label</Label>
              <Input
                id="ref-label"
                value={formLabel}
                onChange={(e) => setFormLabel(e.target.value)}
                placeholder="Item label"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="ref-position">Position</Label>
              <Input
                id="ref-position"
                type="number"
                value={formPosition}
                onChange={(e) => setFormPosition(e.target.value)}
                placeholder="Position (optional)"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setModalOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                disabled={createMutation.isPending || updateMutation.isPending}
              >
                Save
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
