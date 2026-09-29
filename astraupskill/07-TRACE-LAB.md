# Trace lab

Trace A is a first run. Search returns story 42. The database has no thread. The service inserts thread `t`, fetches two pages, filters ten eligible comments, upserts them, updates status to parsing, and returns `t`. Trace B is an interrupted run: the insert committed, the process stopped before HTTP completed, and the next run finds `t`. The corrected path fetches again and repairs the children. The old path returned `t` with zero children.

Trace C is a duplicate delivery. The remote API returns comment 7 twice across pages. Both rows carry the same logical key. The database conflict rule makes the final state one child; the exact surviving raw text follows the database upsert behavior. Trace D is a nested reply. Its parent id differs from 42, so no write occurs. Trace E is empty text with the right parent; it also produces no write.

Now add a failure point after the first 500-row upsert. The thread and 500 children are durable. A retry refetches all comments and upserts all eligible rows; the existing 500 conflict, and the remaining rows are created. The invariant is restored without a cleanup delete. If your predicted trace differs, name the exact boundary—HTTP, filtering, conflict resolution, or status update—where the divergence begins.

Extend the trace with authorization: an untrusted caller cannot reach the admin trigger, while an authorized trigger still receives untrusted remote text. These are separate boundaries and should not be collapsed into one “safe” label. Extend it again with deletion: removing a thread cascades child rows according to the schema, but the importer itself never deletes. Trace ownership clarifies which component may change which data.
