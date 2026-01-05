import React from "react";

export type PaginationProps = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
};

const Pagination: React.FC<PaginationProps> = ({ page, pageSize, total, onPageChange }) => {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);

  return (
    <div className="pagination">
      <div className="pagination-info">
        Showing <span>{start}</span> to <span>{end}</span> of <span>{total}</span>
      </div>
      <div className="pagination-actions">
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={() => onPageChange(Math.max(1, page - 1))}
          disabled={page <= 1}
        >
          Prev
        </button>
        <span className="pagination-page">{page} / {totalPages}</span>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={() => onPageChange(Math.min(totalPages, page + 1))}
          disabled={page >= totalPages}
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default Pagination;
