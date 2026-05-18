# Chain-of-Custody Standard

Every candidate source requires a custody record.

## Minimum Custody Record

- Who acquired it
- When it was acquired
- From where it was acquired
- How it was acquired
- Whether it was modified
- Where the original is stored
- Whether an immutable reference exists
- Whether hash/checksum was captured
- Who reviewed it
- What decision was made

## Modification Rule

Candidate sources must not be altered prior to review.

If normalization is later authorized, the normalized copy must preserve a link to the original source and its custody record.

## Hashing Rule

Where technically possible, record:

- SHA256 hash
- file size
- file name
- original URI or storage location
- acquisition timestamp
