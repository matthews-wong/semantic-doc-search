# Terraform State Locking

Terraform tracks the real-world resources it manages in a state file. When more
than one person or pipeline runs Terraform against the same state, concurrent
writes can corrupt it. State locking prevents that by ensuring only one apply
mutates the state at a time.

## How locking works

When you run `terraform apply` (or `plan` with a refresh), Terraform acquires a
lock on the backend. Other runs block or fail fast until the lock is released.
If a run crashes and leaves a stale lock, you can clear it with
`terraform force-unlock LOCK_ID` -- but only after confirming no apply is
actually in progress.

## Remote backends

Local state does not support locking safely for teams. Use a remote backend:

- **S3 + DynamoDB**: store state in an S3 bucket and use a DynamoDB table for
  the lock. Enable bucket versioning so you can recover a corrupted state.
- **Terraform Cloud / Enterprise**: locking, versioning, and run queuing are
  built in.
- **Azure Blob / Google Cloud Storage**: both offer native locking.

## Recommendations

- Never commit `terraform.tfstate` to version control; it can contain secrets.
- Turn on versioning and encryption on the state bucket.
- Scope one state file per environment to keep blast radius small.
