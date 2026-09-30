/** Bound browser resource use while retaining ordered, complete route results. */
export async function certifyWithConcurrency(items, limit, certify) {
  if (!Number.isInteger(limit) || limit < 1) throw new Error("Invalid certification concurrency");
  const results = new Array(items.length);
  let nextIndex = 0;
  const workers = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (nextIndex < items.length) {
      const index = nextIndex++;
      results[index] = await certify(items[index], index);
    }
  });
  // Settle every worker before failing so active browser contexts can close.
  const outcomes = await Promise.allSettled(workers);
  const failure = outcomes.find((outcome) => outcome.status === "rejected");
  if (failure) throw failure.reason;
  return results;
}
