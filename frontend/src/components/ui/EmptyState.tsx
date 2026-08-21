import type { ReactNode } from 'react';

interface Props {
  icon?: ReactNode;
  title: string;
  body?: string;
  action?: ReactNode;
}

export default function EmptyState({ icon, title, body, action }: Props) {
  return (
    <div className="empty">
      {icon && <span className="empty__icon">{icon}</span>}
      <p className="empty__title">{title}</p>
      {body && <p className="empty__body">{body}</p>}
      {action}
    </div>
  );
}
