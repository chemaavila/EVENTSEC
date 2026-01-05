import React from "react";

type TableSkeletonProps = {
  rows?: number;
  columns?: number;
};

const TableSkeleton: React.FC<TableSkeletonProps> = ({ rows = 6, columns = 6 }) => (
  <div className="table-wrap">
    <table className="table">
      <thead>
        <tr>
          {Array.from({ length: columns }).map((_, idx) => (
            <th key={idx}>
              <span className="loading-skeleton-line" />
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {Array.from({ length: rows }).map((_, rowIdx) => (
          <tr key={rowIdx}>
            {Array.from({ length: columns }).map((__, colIdx) => (
              <td key={colIdx}>
                <span className="loading-skeleton-line" />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

export default TableSkeleton;
