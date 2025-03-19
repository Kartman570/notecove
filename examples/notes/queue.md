# Delivery queue

A worker claims one pending message using a lease. Expired leases can be reclaimed after a crash. Retry transient HTTP failures with exponential backoff. Permanent failures go to a dead-letter queue for manual inspection.
