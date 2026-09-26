import { Button } from './Button';

export interface PaginationProps {
  page: number;
  hasNext: boolean;
  hasPrevious: boolean;
  onNext: () => void;
  onPrevious: () => void;
  totalCount?: number;
}

/** Deliberately plain prev/next, not numbered pages: the API's pagination envelope
 * (Paginated<T> in @little-lemon/api-client) only ever gives us next/previous URLs, not
 * a total page count, and PAGE_SIZE=2 in this API means real pagination UI, not an
 * afterthought - this is used on every list page. */
export function Pagination({ page, hasNext, hasPrevious, onNext, onPrevious, totalCount }: PaginationProps) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-[13px] text-text-tertiary">
        {totalCount !== undefined ? `${totalCount} results · ` : ''}
        Page {page}
      </span>
      <div className="flex gap-2">
        <Button variant="secondary" size="sm" onClick={onPrevious} disabled={!hasPrevious}>
          Previous
        </Button>
        <Button variant="secondary" size="sm" onClick={onNext} disabled={!hasNext}>
          Next
        </Button>
      </div>
    </div>
  );
}
