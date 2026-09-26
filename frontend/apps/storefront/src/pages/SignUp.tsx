import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { parseFormErrors } from '@little-lemon/api-client';
import { Button, FormField, Input } from '@little-lemon/ui';
import { useSignup } from '../hooks/useAuth';

const schema = z.object({
  username: z.string().min(1, 'Required'),
  email: z.string().email('Enter a valid email').optional().or(z.literal('')),
  password: z.string().min(8, 'At least 8 characters'),
});
type FormValues = z.infer<typeof schema>;

export function SignUp() {
  const navigate = useNavigate();
  const signup = useSignup();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    try {
      await signup.mutateAsync({ ...values, email: values.email || undefined });
      navigate('/');
    } catch (error) {
      const { fields, general } = parseFormErrors(error);
      for (const [field, message] of Object.entries(fields)) {
        setError(field as keyof FormValues, { message });
      }
      if (general) setError('root', { message: general });
    }
  }

  return (
    <div className="flex-grow flex items-center justify-center py-16">
      <div className="w-[440px] bg-surface border border-border rounded p-10 flex flex-col gap-5">
        <div>
          <h1 className="font-display text-[28px]">Create your account</h1>
          <p className="text-text-secondary text-sm mt-1.5">Browsing the menu doesn't need an account — only checkout does.</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4" noValidate>
          <FormField label="Username" htmlFor="username" error={errors.username?.message}>
            <Input id="username" autoComplete="username" invalid={Boolean(errors.username)} {...register('username')} />
          </FormField>
          <FormField label="Email (optional)" htmlFor="email" error={errors.email?.message} hint="Used only for password/username recovery.">
            <Input id="email" type="email" autoComplete="email" invalid={Boolean(errors.email)} {...register('email')} />
          </FormField>
          <FormField label="Password" htmlFor="password" error={errors.password?.message} hint="At least 8 characters, not too common or all-numeric.">
            <Input id="password" type="password" autoComplete="new-password" invalid={Boolean(errors.password)} {...register('password')} />
          </FormField>

          {errors.root?.message && <p className="text-sm text-danger font-medium">{errors.root.message}</p>}

          <Button type="submit" className="w-full mt-1" disabled={signup.isPending}>
            {signup.isPending ? 'Creating account…' : 'Create account'}
          </Button>
        </form>

        <p className="text-sm text-text-secondary text-center">
          Already have an account?{' '}
          <Link to="/login" className="text-accent font-semibold">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
