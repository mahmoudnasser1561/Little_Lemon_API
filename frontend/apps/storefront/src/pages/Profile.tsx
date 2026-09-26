import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { parseFormErrors } from '@little-lemon/api-client';
import { Badge, Button, Card, FormField, Input } from '@little-lemon/ui';
import { useCurrentUser, useSetPassword, useUpdateProfile } from '../hooks/useAuth';

const profileSchema = z.object({
  email: z.string().email('Enter a valid email').optional().or(z.literal('')),
});
type ProfileValues = z.infer<typeof profileSchema>;

const passwordSchema = z.object({
  current_password: z.string().min(1, 'Required'),
  new_password: z.string().min(8, 'At least 8 characters'),
});
type PasswordValues = z.infer<typeof passwordSchema>;

const ROLE_LABEL: Record<string, string> = {
  manager: 'Manager',
  delivery_crew: 'Delivery crew',
  customer: 'Customer',
};

export function Profile() {
  const { data: user } = useCurrentUser();
  const updateProfile = useUpdateProfile();
  const setPassword = useSetPassword();

  const profileForm = useForm<ProfileValues>({ resolver: zodResolver(profileSchema) });
  const passwordForm = useForm<PasswordValues>({ resolver: zodResolver(passwordSchema) });

  useEffect(() => {
    if (user) profileForm.reset({ email: user.email });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  async function onProfileSubmit(values: ProfileValues) {
    try {
      await updateProfile.mutateAsync({ email: values.email || undefined });
    } catch (error) {
      const { fields, general } = parseFormErrors(error);
      for (const [field, message] of Object.entries(fields)) {
        profileForm.setError(field as keyof ProfileValues, { message });
      }
      if (general) profileForm.setError('root', { message: general });
    }
  }

  async function onPasswordSubmit(values: PasswordValues) {
    try {
      await setPassword.mutateAsync(values);
      passwordForm.reset();
    } catch (error) {
      const { fields, general } = parseFormErrors(error);
      for (const [field, message] of Object.entries(fields)) {
        passwordForm.setError(field as keyof PasswordValues, { message });
      }
      if (general) passwordForm.setError('root', { message: general });
    }
  }

  if (!user) return null;

  return (
    <div className="flex-grow">
      <div className="px-12 pt-12 pb-6">
        <h1 className="font-display text-[34px]">Your profile</h1>
      </div>

      <div className="px-12 pb-16 flex flex-col gap-6 max-w-[640px]">
        <Card className="p-7 flex flex-col gap-5">
          <div className="flex items-center gap-3.5">
            <div className="w-[52px] h-[52px] rounded-full bg-text text-white flex items-center justify-center text-lg font-bold">
              {user.username.charAt(0).toUpperCase()}
            </div>
            <div>
              <div className="font-semibold">{user.username}</div>
              <Badge tone="neutral" className="mt-1">
                {ROLE_LABEL[user.role] ?? user.role}
              </Badge>
            </div>
          </div>

          <div className="h-px bg-border" />

          <form onSubmit={profileForm.handleSubmit(onProfileSubmit)} className="flex flex-col gap-4" noValidate>
            <FormField label="Username" htmlFor="pf-username" hint="Change this from &quot;Forgot username&quot; — it can't be edited here.">
              <Input id="pf-username" value={user.username} disabled />
            </FormField>
            <FormField label="Email" htmlFor="pf-email" error={profileForm.formState.errors.email?.message}>
              <Input
                id="pf-email"
                type="email"
                invalid={Boolean(profileForm.formState.errors.email)}
                {...profileForm.register('email')}
              />
            </FormField>
            {profileForm.formState.errors.root?.message && (
              <p className="text-sm text-danger font-medium">{profileForm.formState.errors.root.message}</p>
            )}
            <Button type="submit" className="self-start" disabled={updateProfile.isPending}>
              {updateProfile.isPending ? 'Saving…' : 'Save changes'}
            </Button>
          </form>
        </Card>

        <Card className="p-7 flex flex-col gap-4">
          <h3 className="font-display text-[19px]">Change password</h3>
          <form onSubmit={passwordForm.handleSubmit(onPasswordSubmit)} className="flex flex-col gap-4" noValidate>
            <FormField label="Current password" htmlFor="pf-current" error={passwordForm.formState.errors.current_password?.message}>
              <Input
                id="pf-current"
                type="password"
                autoComplete="current-password"
                invalid={Boolean(passwordForm.formState.errors.current_password)}
                {...passwordForm.register('current_password')}
              />
            </FormField>
            <FormField label="New password" htmlFor="pf-new" error={passwordForm.formState.errors.new_password?.message}>
              <Input
                id="pf-new"
                type="password"
                autoComplete="new-password"
                invalid={Boolean(passwordForm.formState.errors.new_password)}
                {...passwordForm.register('new_password')}
              />
            </FormField>
            {passwordForm.formState.errors.root?.message && (
              <p className="text-sm text-danger font-medium">{passwordForm.formState.errors.root.message}</p>
            )}
            {setPassword.isSuccess && <p className="text-sm text-olive font-medium">Password updated.</p>}
            <Button type="submit" variant="secondary" className="self-start" disabled={setPassword.isPending}>
              {setPassword.isPending ? 'Updating…' : 'Update password'}
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
}
