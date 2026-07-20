import { useMemo, useState } from "react";
import { ArrowUpDown, ArrowUp, ArrowDown, Search, ChevronLeft, ChevronRight } from "lucide-react";

// A reusable enterprise data table: sortable columns, optional search, sticky
// header, zebra-free hover rows, and pagination. Columns:
//   { key, label, align?, sortable?, sortValue?(row), render?(row), width? }
export default function DataTable({
  columns, rows, initialSort, pageSize = 8, searchable = true,
  searchKeys, searchPlaceholder = "Search…", onRowClick, empty = "No results.",
}) {
  const [q, setQ] = useState("");
  const [sort, setSort] = useState(initialSort || null); // { key, dir }
  const [page, setPage] = useState(0);

  const filtered = useMemo(() => {
    if (!q.trim()) return rows;
    const needle = q.toLowerCase();
    const keys = searchKeys || columns.map((c) => c.key);
    return rows.filter((r) =>
      keys.some((k) => String(r[k] ?? "").toLowerCase().includes(needle))
    );
  }, [rows, q, searchKeys, columns]);

  const sorted = useMemo(() => {
    if (!sort) return filtered;
    const col = columns.find((c) => c.key === sort.key);
    const val = col?.sortValue || ((r) => r[sort.key]);
    const dir = sort.dir === "asc" ? 1 : -1;
    return [...filtered].sort((a, b) => {
      const av = val(a), bv = val(b);
      if (av === bv) return 0;
      return (av > bv ? 1 : -1) * dir;
    });
  }, [filtered, sort, columns]);

  const pages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const clamped = Math.min(page, pages - 1);
  const view = sorted.slice(clamped * pageSize, clamped * pageSize + pageSize);

  function toggleSort(key) {
    setPage(0);
    setSort((s) =>
      !s || s.key !== key ? { key, dir: "desc" } : s.dir === "desc" ? { key, dir: "asc" } : null
    );
  }

  return (
    <div>
      {searchable && (
        <div className="mb-3 flex items-center gap-2">
          <label className="flex h-9 w-full max-w-xs items-center gap-2 rounded-md border border-line bg-surface px-2.5 text-muted focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20">
            <Search className="h-4 w-4 shrink-0" />
            <input
              value={q}
              onChange={(e) => { setQ(e.target.value); setPage(0); }}
              placeholder={searchPlaceholder}
              className="w-full bg-transparent text-[13px] text-ink placeholder:text-muted/70 focus:outline-none"
            />
          </label>
          <span className="ml-auto text-xs text-muted">
            <span className="tnum text-ink-soft">{sorted.length}</span> results
          </span>
        </div>
      )}

      <div className="overflow-x-auto rounded-lg border border-line">
        <table className="w-full border-collapse text-[13px]">
          <thead className="thead">
            <tr>
              {columns.map((c) => {
                const activeSort = sort?.key === c.key;
                return (
                  <th
                    key={c.key}
                    style={{ width: c.width }}
                    className={`whitespace-nowrap px-3 py-2.5 font-semibold ${c.align === "right" ? "text-right" : "text-left"}`}
                  >
                    {c.sortable ? (
                      <button
                        onClick={() => toggleSort(c.key)}
                        className={`inline-flex items-center gap-1 transition-colors hover:text-ink ${activeSort ? "text-ink" : ""} ${c.align === "right" ? "flex-row-reverse" : ""}`}
                      >
                        {c.label}
                        {activeSort ? (
                          sort.dir === "asc" ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />
                        ) : (
                          <ArrowUpDown className="h-3 w-3 opacity-40" />
                        )}
                      </button>
                    ) : (
                      c.label
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {view.length === 0 ? (
              <tr><td colSpan={columns.length} className="px-3 py-10 text-center text-muted">{empty}</td></tr>
            ) : (
              view.map((row, i) => (
                <tr
                  key={row.id ?? i}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  className={`trow ${onRowClick ? "cursor-pointer" : ""}`}
                >
                  {columns.map((c) => (
                    <td key={c.key} className={`px-3 py-2.5 ${c.align === "right" ? "text-right" : "text-left"}`}>
                      {c.render ? c.render(row) : <span className="text-ink-soft">{row[c.key]}</span>}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {pages > 1 && (
        <div className="mt-3 flex items-center justify-between text-xs text-muted">
          <span>Page <span className="tnum text-ink-soft">{clamped + 1}</span> of <span className="tnum">{pages}</span></span>
          <div className="flex items-center gap-1">
            <button disabled={clamped === 0} onClick={() => setPage(clamped - 1)}
                    className="icon-btn disabled:opacity-40"><ChevronLeft className="h-4 w-4" /></button>
            <button disabled={clamped >= pages - 1} onClick={() => setPage(clamped + 1)}
                    className="icon-btn disabled:opacity-40"><ChevronRight className="h-4 w-4" /></button>
          </div>
        </div>
      )}
    </div>
  );
}
