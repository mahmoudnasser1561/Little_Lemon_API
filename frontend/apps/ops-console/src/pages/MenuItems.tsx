import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { categories as categoriesApi, menu as menuApi, parseFormErrors, type MenuItem } from '@little-lemon/api-client';
import { Badge, Button, Card, FormField, Input, Pagination } from '@little-lemon/ui';

const schema = z.object({
  title: z.string().min(1, 'Required'),
  price: z.string().regex(/^\d+(\.\d{1,2})?$/, 'Enter a valid price, e.g. 12.50'),
  category_id: z.string().min(1, 'Choose a category'),
  featured: z.boolean(),
  image: z.any().optional(),
});
type FormValues = z.infer<typeof schema>;

export function MenuItems() {
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<MenuItem | null>(null);
  const queryClient = useQueryClient();

  const listQuery = useQuery({
    queryKey: ['menu-items', page],
    queryFn: () => menuApi.list({ page }),
  });
  const categoriesQuery = useQuery({
    queryKey: ['categories-all'],
    queryFn: () => categoriesApi.listAll(),
  });

  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { featured: false } });

  useEffect(() => {
    if (editing) {
      reset({
        title: editing.title,
        price: editing.price,
        category_id: String(editing.category.id),
        featured: editing.featured,
      });
    } else {
      reset({ title: '', price: '', category_id: '', featured: false });
    }
  }, [editing, reset]);

  const saveMutation = useMutation({
    mutationFn: (values: FormValues) => {
      const image = (values.image as FileList | undefined)?.[0] ?? null;
      const payload = {
        title: values.title,
        price: values.price,
        featured: values.featured,
        category_id: Number(values.category_id),
        image,
      };
      return editing ? menuApi.update(editing.id, payload) : menuApi.create(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menu-items'] });
      setEditing(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => menuApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menu-items'] });
    },
  });

  async function onSubmit(values: FormValues) {
    try {
      await saveMutation.mutateAsync(values);
    } catch (error) {
      const { fields, general } = parseFormErrors(error);
      for (const [field, message] of Object.entries(fields)) {
        setError(field as keyof FormValues, { message });
      }
      if (general) setError('root', { message: general });
    }
  }

  function handleDelete(item: MenuItem) {
    if (window.confirm(`Delete "${item.title}"? This can't be undone.`)) {
      deleteMutation.mutate(item.id);
      if (editing?.id === item.id) setEditing(null);
    }
  }

  return (
    <div className="flex-grow">
      <div className="px-8 pt-8 pb-6">
        <h1 className="font-display text-[28px]">Menu items</h1>
      </div>

      <div className="px-8 pb-12 grid grid-cols-[1fr_360px] gap-6 items-start">
        <Card className="p-2">
          {listQuery.isLoading && <p className="p-6 text-text-secondary">Loading…</p>}
          {listQuery.isError && <p className="p-6 text-danger">Couldn't load menu items. Is the API running?</p>}
          {listQuery.data && (
            <>
              <table className="w-full">
                <thead>
                  <tr className="text-left text-[11px] font-bold uppercase tracking-wide text-text-tertiary">
                    <th className="px-4 pb-2.5">Title</th>
                    <th className="px-4 pb-2.5">Category</th>
                    <th className="px-4 pb-2.5">Price</th>
                    <th className="px-4 pb-2.5"></th>
                    <th className="px-4 pb-2.5"></th>
                  </tr>
                </thead>
                <tbody>
                  {listQuery.data.results.map((item) => (
                    <tr key={item.id} className="border-t border-border">
                      <td className="px-4 py-3 text-sm font-semibold">
                        {item.title}
                        {item.featured && (
                          <Badge tone="accent" className="ml-2">
                            Featured
                          </Badge>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-text-secondary">{item.category.title}</td>
                      <td className="px-4 py-3 text-sm tabular-nums">${item.price}</td>
                      <td className="px-4 py-3">
                        <Button type="button" variant="ghost" size="sm" onClick={() => setEditing(item)}>
                          Edit
                        </Button>
                      </td>
                      <td className="px-4 py-3">
                        <Button type="button" variant="danger" size="sm" onClick={() => handleDelete(item)}>
                          Delete
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {listQuery.data.results.length === 0 && <p className="p-6 text-text-secondary">No menu items yet.</p>}
              <div className="p-4">
                <Pagination
                  page={page}
                  hasPrevious={Boolean(listQuery.data.previous)}
                  hasNext={Boolean(listQuery.data.next)}
                  onPrevious={() => setPage((p) => Math.max(1, p - 1))}
                  onNext={() => setPage((p) => p + 1)}
                  totalCount={listQuery.data.count}
                />
              </div>
            </>
          )}
        </Card>

        <Card className="p-6 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-[17px]">{editing ? `Edit "${editing.title}"` : 'Add menu item'}</h3>
            {editing && (
              <button type="button" onClick={() => setEditing(null)} className="text-xs font-semibold text-text-tertiary hover:text-text">
                Cancel
              </button>
            )}
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4" noValidate>
            <FormField label="Title" htmlFor="mi-title" error={errors.title?.message}>
              <Input id="mi-title" invalid={Boolean(errors.title)} {...register('title')} />
            </FormField>
            <FormField label="Price" htmlFor="mi-price" error={errors.price?.message}>
              <Input id="mi-price" placeholder="12.50" invalid={Boolean(errors.price)} {...register('price')} />
            </FormField>
            <FormField label="Category" htmlFor="mi-category" error={errors.category_id?.message}>
              <select
                id="mi-category"
                className="h-11 px-3.5 rounded-sm border border-border-strong bg-white text-sm w-full"
                {...register('category_id')}
              >
                <option value="">Choose…</option>
                {categoriesQuery.data?.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.title}
                  </option>
                ))}
              </select>
            </FormField>
            <label className="flex items-center gap-2.5 text-sm font-medium">
              <input type="checkbox" className="w-[18px] h-[18px] accent-accent" {...register('featured')} />
              Featured
            </label>
            <FormField label="Image" htmlFor="mi-image" hint={editing?.image ? 'Uploading a new one replaces the current photo.' : undefined}>
              <input id="mi-image" type="file" accept="image/*" className="text-sm" {...register('image')} />
            </FormField>

            {errors.root?.message && <p className="text-sm text-danger font-medium">{errors.root.message}</p>}

            <Button type="submit" disabled={saveMutation.isPending}>
              {saveMutation.isPending ? 'Saving…' : editing ? 'Save changes' : 'Add item'}
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
}
