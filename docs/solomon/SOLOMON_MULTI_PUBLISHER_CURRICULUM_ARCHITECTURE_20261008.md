# Solomon Multi-Publisher Curriculum Reference Architecture

Date: 2026-10-08
Status: Implementation baseline

## Objective

Make curriculum mapping and lesson planning publisher-neutral while preserving source provenance and publisher rights.

The reference layer supports schools that mix curricula across subjects and grades. A school can therefore map Abeka mathematics, BJU Press science, Purposeful Design language arts, Positive Action Bible, Summit worldview resources, or other approved publishers into one CROWN curriculum map without pretending that CROWN owns the underlying publisher content.

## Reference Model

Publisher -> edition/year -> grade band -> subject -> source kind -> official source -> school crosswalk -> curriculum map -> pacing -> lesson-planning reference

The registry is not a content mirror. It is a governed source-of-truth layer for locating and identifying curriculum references.

## Initial Publishers

- BJU Press
- Abeka
- Purposeful Design Publications / ACSI
- Positive Action for Christ
- Summit Ministries

The existing publisher-normalization registry remains authoritative for canonical publisher names and aliases.

## Rights Levels

### Public reference

Allowed by default:
- publisher and product names;
- edition/year;
- grade bands;
- subjects;
- official URLs;
- high-level factual structure;
- CROWN-authored summaries, mappings, and crosswalks.

Not automatically authorized:
- bulk objective extraction;
- full scope-and-sequence reproduction;
- teacher-edition content;
- lesson text;
- assessments;
- answer keys;
- copyrighted publisher lesson plans.

### School-licensed materials

A school may later attach legitimately licensed materials for that school's governed internal workflow when the applicable license permits it. Those materials must remain tenant-scoped and must not silently become shared Solomon corpus content.

### Publisher-authorized integration

A publisher agreement may explicitly authorize structured objective ingestion, deeper mapping, APIs, or other integration. Authorization must be recorded before the fail-closed ingestion flags are changed.

## Planning Use

Solomon/CROWN may use the public reference registry to:
- identify the publisher and edition used by a course;
- present verified official source links;
- organize school-authored curriculum maps;
- crosswalk school objectives against publisher structures;
- compare sequencing across publishers using school-authored or independently derived mappings;
- attach provenance to pacing and lesson-planning references.

## Governance Rule

Public availability is evidence that a source can be referenced, not evidence that its entire copyrighted contents can be republished or ingested. All structured publisher-content ingestion remains fail-closed until explicitly authorized.
