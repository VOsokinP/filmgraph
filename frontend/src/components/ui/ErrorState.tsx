import Button from './Button';
import EmptyState from './EmptyState';
import { AlertIcon } from './Icons';

interface Props {
  message: string;
  title?: string;
  onRetry?: () => void;
}

export default function ErrorState({ message, title = "Couldn't load this page", onRetry }: Props) {
  return (
    <div className="panel" role="alert">
      <EmptyState
        icon={<AlertIcon size={32} />}
        title={title}
        body={message}
        action={
          onRetry ? (
            <Button variant="primary" onClick={onRetry}>
              Try again
            </Button>
          ) : undefined
        }
      />
    </div>
  );
}
