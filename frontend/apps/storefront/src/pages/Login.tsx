import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { parseFormErrors } from '@little-lemon/api-client';
import { Button, FormField, Input } from '@little-lemon/ui';
import { useLogin } from '../hooks/useAuth';

const schema = z.object({
  username: z.string().min(1, 'Required'),
  password: z.string().min(1, 'Required'),
});
type FormValues = z.infer<typeof schema>;

interface LocationState {
  from?: { pathname: string };
}

export function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const login = useLogin();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    try {
      await login.mutateAsync(values);
      const from = (location.state as LocationState | null)?.from?.pathname ?? '/';
      navigate(from);
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
      <div className="w-[420px] bg-surface border border-border rounded p-10 flex flex-col gap-5">
        <div>
          <h1 className="font-display text-[28px]">Welcome back</h1>
          <p className="text-text-secondary text-sm mt-1.5">Log in to your Little Lemon account.</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4" noValidate>
          <FormField label="Username" htmlFor="username" error={errors.username?.message}>
            <Input id="username" autoComplete="username" invalid={Boolean(errors.username)} {...register('username')} />
          </FormField>
          <FormField label="Password" htmlFor="password" error={errors.password?.message}>
            <Input id="password" type="password" autoComplete="current-password" invalid={Boolean(errors.password)} {...register('password')} />
          </FormField>

          {errors.root?.message && <p className="text-sm text-danger font-medium">{errors.root.message}</p>}

          <Button type="submit" className="w-full mt-1" disabled={login.isPending}>
            {login.isPending ? 'Logging in…' : 'Log in'}
          </Button>
        </form>

        <p className="text-sm text-text-secondary text-center">
          New here?{' '}
          <Link to="/signup" className="text-accent font-semibold">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
}
