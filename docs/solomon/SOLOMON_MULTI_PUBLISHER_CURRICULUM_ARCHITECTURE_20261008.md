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


## Praeceptum Source Authority Hierarchy

Praeceptum ranks curriculum evidence by provenance rather than treating all public materials as equivalent:

1. **Publisher direct** — official publisher scope-and-sequence, curriculum maps, catalogs, standards references, and official product documentation.
2. **Publisher-authorized partner** — partner-hosted maps or crosswalks that the publisher explicitly makes available through a recognized mapping platform or partnership.
3. **Association/accreditor reference** — curriculum resources published by recognized Christian-school associations, accreditation bodies, or professional organizations.
4. **School public map** — a school's publicly shared curriculum map or pacing guide; useful as advisory implementation evidence, never as the canonical publisher source.
5. **Discovery only** — search indexes, document mirrors, or unattributed copies used only to locate a better provenance source.

Praeceptum should always prefer the highest available authority tier. Lower-tier sources may inform comparison or discovery but must not silently overwrite higher-authority records.

## Curriculum Record Model

Praeceptum tracks five distinct states:

```text
Intended -> Planned -> Delivered -> Assessed -> Mastered
```

- **Intended**: publisher objectives, school standards, Portrait of a Graduate outcomes, accreditation expectations, and school-authored curriculum targets.
- **Planned**: units, pacing, lesson plans, resources, and scheduled assessments.
- **Delivered**: what the teacher actually taught, including completion/deviation evidence.
- **Assessed**: objectives or standards actually evaluated through assignments, assessments, rubrics, or other evidence.
- **Mastered**: student or cohort evidence against school-defined mastery thresholds.

The architecture must preserve the distinction between these states so administrative reports can identify mapped-but-not-taught, taught-but-not-assessed, and assessed-but-not-mastered gaps.

## Product Independence Rule

Praeceptum must remain independently operable without a paid Atlas, Curriculum Trak, or other third-party curriculum-mapping subscription. Third-party map libraries may be referenced when legitimately public or licensed, but they are not runtime dependencies.

## Provisional Product Identity

Working module name: **CROWN Praeceptum**  
Descriptor: **Curriculum Mapping, Alignment & Tracking**  
Status: **provisional branding pending formal trademark clearance**

Praeceptum is the curriculum system of record. Solomon is the governed intelligence/guidance layer that may analyze Praeceptum data, identify gaps and overlaps, assist with crosswalks, and support teacher/administrator planning.
