import { ButtonHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export function Button({ className, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button className={cn('rounded-lg bg-accent px-4 py-2 hover:bg-cyan transition', className)} {...props} />;
}
