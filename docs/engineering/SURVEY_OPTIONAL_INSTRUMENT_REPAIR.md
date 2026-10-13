# Survey optional instrument validation repair

Base: `1e1849ed6f2cb22cc97881434967a624a8878e00`. Issue: #204.

Scope: reject malformed question definitions before skipping unanswered optional
questions. Optional malformed choices previously reached publication snapshot
creation; nested choices could raise a raw TypeError, while mixed text/nontext
choices could be published. Every definition now receives the same type and
choice-bound checks, whether or not an answer is present.

Validation: behavioral validator cases, transactional publication rejection and
existing survey submission/publication/draft/reporting/consumer regressions;
required exact-head CI before source acceptance. No public collection route,
invitation, legal approval or operational pilot is enabled by this repair.

Decision owner: repository owner under the configured solo-maintainer path;
no independent human review is claimed. Rollback: revert this bounded repair.
The root issue remains open for the collection and operational acceptance work.
