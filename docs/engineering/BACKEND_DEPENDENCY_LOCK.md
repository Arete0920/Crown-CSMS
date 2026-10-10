# Backend dependency lock foundation

Base: `88ddd37ad278615903e2fdabd4fad29f2a6c134b`.
Owner: Arete0920; authorized repository CI hardening on October 9, 2026.
Rollback: revert this outcome PR. No dependency admission or production activation is implied.

`tools/ci/requirements-linux-py312.lock` resolves the existing backend manifest for
Linux and Python 3.12. Direct and transitive dependencies use exact versions and
SHA256 distribution hashes. It is intentionally a separate foundation outcome;
runtime containers and test workflows continue using their existing inputs until
a separately verified adoption PR. Windows requires a separately generated lock.

The metadata records the source and lock hashes, target and pinned compiler.
Regenerate with Python 3.12 and `pip-tools==7.6.2` using the command in the metadata;
then update both hashes. Review the dependency changes before merging. These hashes
detect drift and are not signed build provenance or a reviewer approval record.

Repository Policy verifies metadata, manifest membership and hashed exact pins.
Pip validates dependency resolution and compatible distribution hashes with:

```bash
python -m pip install --dry-run --ignore-installed --require-hashes --only-binary=:all: -r tools/ci/requirements-linux-py312.lock
```

That command passed locally on Linux/Python 3.12. Five rejection/acceptance tests
pass. Hosted checks, complete suite validation of this lock and runtime adoption
remain unverified until their respective evidence is recorded.
