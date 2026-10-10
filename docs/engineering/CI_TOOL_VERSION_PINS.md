# CI security tool version pins

Base: `88ddd37ad278615903e2fdabd4fad29f2a6c134b`.
Owner: Arete0920; authorized October 9, 2026 CI hardening. Rollback: revert this PR.

Repository Policy downloads the existing actionlint 1.7.1 Linux/amd64 release
archive directly and verifies its reviewed SHA256 before extraction and execution.
The mutable installer fetched from `main` is removed. The archive hash was checked
against the upstream release checksum file and the local archive.

Policy YAML parsing, dependency security/license tools and Python/Node SBOM tools
now declare exact direct tool versions. A required policy check detects removal or
change of those reviewed pins and the actionlint checksum. Version upgrades require
updating the workflows and this guard together in a reviewed PR.

Three policy tests and actionlint pass locally. The Python tools install and report
their pinned versions; the backend requirements SBOM command produces valid JSON.
The CycloneDX positional requirements argument replaces the old `-i` argument,
which means an index URL in this pinned release.

Tool transitive dependencies still resolve through their package registries. This
outcome does not establish complete hashed tool environments, immutable Node
runtime versions, scanner database snapshots, or SBOMs of deployed container
digests. Requirements-derived backend SBOMs still omit unpinned resolved versions;
actual installed-image SBOM and signed provenance remain separate work.
