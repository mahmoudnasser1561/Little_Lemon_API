import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { categories as categoriesApi, parseFormErrors } from '@little-lemon/api-client';
import { Button, Card, FormField, Input, Pagination } from '@little-lemon/ui';

const schema = z.object({
  slug: z
    .string()
    .min(1, 'Required')
    .regex(/^[a-z0-9-]+$/, 'Lowercase letters, numbers and hyphens only'),
  title: z.string().min(1, 'Required'),
});
type FormValues = z.infer<typeof schema>;

export function Categories() {
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();

  const listQuery = useQuery({
    queryKey: ['categories', page],
    queryFn: () => categoriesApi.list(page),
  });

  const createMutation = useMutation({
    mutationFn: categoriesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      reset();
    },
  });

  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    try {
      await createMutation.mutateAsync(values);
    } catch (error) {
      const { fields, general } = parseFormErrors(error);
      for (const [field, message] of Object.entries(fields)) {
        setError(field as keyof FormValues, { message });
      }
      if (general) setError('root', { message: general });
    }
  }

  return (
    <div className="flex-grow">
      <div className="px-8 pt-8 pb-6">
        <h1 className="font-display text-[28px]">Categories</h1>
      </div>

      <div className="px-8 pb-12 grid grid-cols-[1fr_360px] gap-6 items-start">
        <Card className="p-2">
          {listQuery.isLoading && <p className="p-6 text-text-secondary">Loading…</p>}
          {listQuery.isError && <p className="p-6 text-danger">Couldn't load categories. Is the API running?</p>}
          {listQuery.data && (
            <>
              <table className="w-full">
                <thead>
                  <tr className="text-left text-[11px] font-bold uppercase tracking-wide text-text-tertiary">
                    <th className="px-4 pb-2.5">Title</th>
                    <th className="px-4 pb-2.5">Slug</th>
                  </tr>
                </thead>
                <tbody>
                  {listQuery.data.results.map((category) => (
                    <tr key={category.id} className="border-t border-border">
                      <td className="px-4 py-3.5 text-sm font-semibold">{category.title}</td>
                      <td className="px-4 py-3.5 text-sm text-text-secondary">{category.slug}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {listQuery.data.results.length === 0 && <p className="p-6 text-text-secondary">No categories yet.</p>}
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
          <h3 className="font-display text-[17px]">Add category</h3>
          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4" noValidate>
            <FormField label="Title" htmlFor="cat-title" error={errors.title?.message}>
              <Input id="cat-title" invalid={Boolean(errors.title)} {...register('title')} />
            </FormField>
            <FormField label="Slug" htmlFor="cat-slug" error={errors.slug?.message} hint="Lowercase, hyphens only.">
              <Input id="cat-slug" invalid={Boolean(errors.slug)} {...register('slug')} />
            </FormField>
            {errors.root?.message && <p className="text-sm text-danger font-medium">{errors.root.message}</p>}
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Adding…' : 'Add category'}
            </Button>
          </form>
          <p className="text-xs text-text-tertiary">
            Categories can only be added here, not renamed or removed — the API has no route for that yet.
          </p>
        </Card>
      </div>
    </div>
  );
}
