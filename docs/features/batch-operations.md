# Batch Operations

ReasonFlow supports batch operations for classifying and processing multiple emails asynchronously with progress tracking via in-memory storage.

## Overview

Batch operations allow users to:
- **Classify up to 100 emails** at once using AI intent classification
- **Process up to 50 emails** through the full agent pipeline
- **Track progress in real-time** with polling
- **Handle partial failures** with detailed error reporting

## API Endpoints

### POST /api/v1/emails/batch/classify

Queue multiple emails for background classification.

**Request:**
```json
{
  "email_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002"
  ]
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "cls_a1b2c3d4e5f67890",
  "status": "queued",
  "total": 3,
  "processed": 0,
  "message": "Batch classification job accepted and queued for processing"
}
```

**Limits:**
- Maximum 100 email IDs per request
- Returns 400 if email_ids is empty or exceeds limit
- Returns 404 if any email IDs don't exist or aren't owned by the user

### POST /api/v1/emails/batch/process

Queue multiple emails for full agent pipeline processing.

**Request:**
```json
{
  "email_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001"
  ]
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "prc_a1b2c3d4e5f67890",
  "status": "queued",
  "total": 2,
  "processed": 0,
  "message": "Batch processing job accepted and queued for processing"
}
```

**Limits:**
- Maximum 50 email IDs per request
- Returns 400 if email_ids is empty or exceeds limit
- Returns 404 if any email IDs don't exist or aren't owned by the user
- Returns 409 if any emails are already in "processing" or "sent" status

### GET /api/v1/emails/batch/status/{job_id}

Retrieve current status of a batch job.

**Response (queued/processing):**
```json
{
  "job_id": "cls_a1b2c3d4e5f67890",
  "status": "processing",
  "total": 3,
  "processed": 1,
  "succeeded": 1,
  "failed": 0,
  "errors": null,
  "created_at": "2026-02-19T10:30:00+00:00",
  "updated_at": "2026-02-19T10:30:05+00:00",
  "completed_at": null
}
```

**Response (completed with errors):**
```json
{
  "job_id": "cls_a1b2c3d4e5f67890",
  "status": "completed",
  "total": 3,
  "processed": 3,
  "succeeded": 2,
  "failed": 1,
  "errors": [
    {
      "email_id": "550e8400-e29b-41d4-a716-446655440002",
      "error": "Classification failed: API rate limit exceeded",
      "timestamp": "2026-02-19T10:30:15+00:00"
    }
  ],
  "created_at": "2026-02-19T10:30:00+00:00",
  "updated_at": "2026-02-19T10:30:15+00:00",
  "completed_at": "2026-02-19T10:30:15+00:00"
}
```

**Status values:**
- `queued` — Job accepted, waiting to start
- `processing` — Actively working on emails
- `completed` — All emails processed (may have partial failures)
- `failed` — All emails failed (rare)

**Note:** Job data is retained for 24 hours after completion, then automatically expired.

## Polling Strategy

### Recommended Frontend Implementation

```typescript
// React hook example for polling batch status
function useBatchStatus(jobId: string | null) {
  return useQuery({
    queryKey: ['batch-status', jobId],
    queryFn: () => fetchBatchStatus(jobId!),
    enabled: !!jobId,
    refetchInterval: (data) => {
      // Poll every 2 seconds while active
      if (data?.status === 'queued' || data?.status === 'processing') {
        return 2000;
      }
      // Stop polling when done
      return false;
    },
    refetchOnWindowFocus: false,
  });
}
```

### Polling Guidelines

1. **Interval:** 2-3 seconds recommended
   - Too frequent: Unnecessary server load
   - Too slow: Poor user experience

2. **Stop conditions:**
   - Status is `completed` or `failed`
   - User navigates away (cancel polling)
   - Maximum polling duration exceeded (e.g., 5 minutes)

3. **Progress calculation:**
   ```typescript
   const progressPercent = (status.processed / status.total) * 100;
   ```

## Frontend Requirements

### Batch Selection UI

1. **Email list with checkboxes:**
   - Individual row selection
   - "Select all" checkbox in header
   - Selection count indicator

2. **Bulk action toolbar:**
   - Appears when emails are selected
   - Actions: "Classify Selected", "Process Selected"
   - Shows count: "3 emails selected"

3. **Selection limits:**
   - Show warning when approaching limit
   - Disable action button if over limit
   - Auto-trim or block selection

### Progress Modal

```tsx
<BatchProgressModal
  isOpen={isProcessing}
  jobId={jobId}
  title="Processing Emails"
  onComplete={handleComplete}
  onCancel={handleCancel}
/>
```

**Features:**
- Progress bar with percentage
- Status text: "Processing 5 of 10 emails..."
- Success/failure counts
- Expandable error list
- Close button (disabled while processing)

### Progress Bar Component

```tsx
interface BatchProgressProps {
  total: number;
  processed: number;
  succeeded: number;
  failed: number;
  status: 'queued' | 'processing' | 'completed' | 'failed';
}

function BatchProgress({ total, processed, succeeded, failed, status }: BatchProgressProps) {
  const percent = Math.round((processed / total) * 100);
  
  return (
    <div className="batch-progress">
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${percent}%` }}
        />
      </div>
      <div className="progress-stats">
        <span>{processed} / {total} processed</span>
        {succeeded > 0 && <span className="success">{succeeded} succeeded</span>}
        {failed > 0 && <span className="error">{failed} failed</span>}
      </div>
    </div>
  );
}
```

## In-Memory Job Storage

Batch jobs are stored in a module-level dictionary (`dict[str, BatchJob]`) keyed by `job_id`. Each entry contains all job state:

```python
# In-memory structure (module-level dict)
_jobs: dict[str, BatchJob] = {}

# Each BatchJob holds:
#   status:    "queued" | "processing" | "completed" | "failed"
#   progress:  {"total": N, "processed": N, "succeeded": N, "failed": N}
#   errors:    [{"email_id": "...", "error": "...", "timestamp": "..."}]
#   metadata:  {"user_id": "...", "email_ids": [...], "job_type": "...", "created_at": "..."}
```

### Storage Details

| Field | Type | Description | Retention |
|-------|------|-------------|----------|
| `status` | str | Current job status | 24 hours (auto-evicted) |
| `progress` | dict | Progress counters | 24 hours (auto-evicted) |
| `errors` | list | Error list | 24 hours (auto-evicted) |
| `metadata` | dict | Job metadata | 24 hours (auto-evicted) |

### Job ID Format

- **Classification jobs:** `cls_{16-char-hex}` (e.g., `cls_a1b2c3d4e5f67890`)
- **Processing jobs:** `prc_{16-char-hex}` (e.g., `prc_a1b2c3d4e5f67890`)

Prefix helps identify job type when debugging.

## Error Handling

### Retry Strategy

Batch operations do not automatically retry failed emails. The frontend should:

1. Display failed emails to the user
2. Offer "Retry Failed" button to re-submit
3. Pre-populate selection with failed email IDs

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Email not found | Email deleted after selection | Refresh email list |
| Already processing | Concurrent batch/job | Wait for completion |
| Classification failed | LLM API error | Retry or classify manually |
| Agent pipeline failed | Tool execution error | Review in Needs Review queue |

## Performance Considerations

1. **Processing speed:**
   - Classification: ~500ms per email (LLM latency)
   - Full pipeline: ~3-5s per email (depends on tools)

2. **Concurrent batches:**
   - Multiple users can run batches simultaneously
   - Same user should avoid overlapping batches on same emails

3. **Memory usage:**
   - Background tasks hold minimal state
   - In-memory dict: ~1KB per job

## Security

1. **Ownership verification:**
   - All email IDs verified against current user
   - Returns 404 if any email not owned by user

2. **Rate limiting:**
   - Subject to existing API rate limits
   - Batch endpoints count as single request for rate limiting

3. **Data retention:**
   - Job data auto-expires after 24 hours
   - No sensitive data stored in memory (only IDs and counts); data is in-memory only, no persistence
