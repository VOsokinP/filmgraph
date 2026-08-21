import type { ButtonHTMLAttributes, ReactNode } from 'react';

import { SpinnerIcon } from './Icons';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: 'sm' | 'md';
  block?: boolean;
  pending?: boolean;
  children?: ReactNode;
}

export default function Button({
  variant = 'secondary',
  size = 'md',
  block = false,
  pending = false,
  disabled,
  className,
  children,
  ...rest
}: Props) {
  const classes = [
    'btn',
    `btn--${variant}`,
    size === 'sm' && 'btn--sm',
    block && 'btn--block',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button
      type="button"
      className={classes}
      disabled={disabled || pending}
      aria-busy={pending || undefined}
      {...rest}
    >
      {pending && <SpinnerIcon size={size === 'sm' ? 12 : 14} />}
      {children}
    </button>
  );
}
