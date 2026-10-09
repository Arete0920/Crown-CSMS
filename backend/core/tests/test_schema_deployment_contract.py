from pathlib import Path
import re
import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
STARTUP_SCRIPTS = (
    REPOSITORY_ROOT / "entrypoint.sh",
    REPOSITORY_ROOT / "backend" / "scripts" / "startup.sh",
)
DEPLOY_WORKFLOWS = (
    REPOSITORY_ROOT / ".github" / "workflows" / "deploy-prod.yml",
    REPOSITORY_ROOT / ".github" / "workflows" / "deploy-prod-dispatch.yml",
)
CONTROLLED_MIGRATION_WORKFLOW = "./.github/workflows/schema-migration-stage.yml"
RESOLVED_SHA_EXPRESSION = "${{ needs.resolve-release.outputs.deploy_sha }}"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _job_block(workflow: str, job_name: str) -> str:
    pattern = re.compile(
        rf"(?ms)^  {re.escape(job_name)}:\n(?P<body>.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)"
    )
    match = pattern.search(workflow)
    assert match is not None, f"missing required job: {job_name}"
    return match.group(0)


def test_web_startup_verifies_schema_without_mutating_it() -> None:
    mutation_pattern = re.compile(
        r"python\s+manage\.py\s+migrate(?!\s+--check(?:\s|$))",
        re.IGNORECASE,
    )

    for path in STARTUP_SCRIPTS:
        source = _read(path)
        assert "python manage.py migrate --check" in source, (
            f"{path.relative_to(REPOSITORY_ROOT)} must fail closed when schema is stale"
        )
        assert mutation_pattern.search(source) is None, (
            f"{path.relative_to(REPOSITORY_ROOT)} must not mutate schema during web startup"
        )


def test_production_workflows_resolve_one_immutable_sha_before_migration() -> None:
    for path in DEPLOY_WORKFLOWS:
        workflow = _read(path)
        resolve_job = _job_block(workflow, "resolve-release")

        assert "deploy_sha:" in resolve_job
        assert "git rev-parse HEAD" in resolve_job
        assert "^[0-9a-f]{40}$" in resolve_job


def test_validated_candidate_precedes_migration_and_web_deployment() -> None:
    for path in DEPLOY_WORKFLOWS:
        workflow = _read(path)
        migration_job = _job_block(workflow, "production-migration")
        deploy_job = _job_block(workflow, "build-and-deploy")

        assert f"uses: {CONTROLLED_MIGRATION_WORKFLOW}" in migration_job
        assert f"expected_sha: {RESOLVED_SHA_EXPRESSION}" in migration_job
        assert "confirm_environment: production" in migration_job
        assert "secrets: inherit" in migration_job

        jobs = yaml.safe_load(workflow)["jobs"]
        assert {"resolve-release", "candidate-verification"} <= set(
            jobs["production-migration"]["needs"]
        ), "production migration must wait for the exact-SHA candidate validation"
        assert {"resolve-release", "production-migration", "candidate-verification"} <= set(
            jobs["build-and-deploy"]["needs"]
        ), "web deployment must wait for validated candidate and exact-SHA migration"
        assert "if" not in jobs["production-migration"]
        assert "if" not in jobs["build-and-deploy"]
        assert f"ref: {RESOLVED_SHA_EXPRESSION}" in deploy_job


def test_deployment_artifact_uses_the_same_sha_as_migration() -> None:
    for path in DEPLOY_WORKFLOWS:
        workflow = _read(path)
        deploy_job = _job_block(workflow, "build-and-deploy")

        assert RESOLVED_SHA_EXPRESSION in deploy_job
        assert "Verify exact checked-out SHA" in deploy_job
        assert "git rev-parse HEAD" in deploy_job


def test_production_appsettings_do_not_reenable_startup_migrations() -> None:
    for path in DEPLOY_WORKFLOWS:
        workflow = _read(path)
        assert "RUN_MIGRATIONS" not in workflow


def test_production_workflow_has_one_appsettings_application_path() -> None:
    workflow = _read(REPOSITORY_ROOT / ".github" / "workflows" / "deploy-prod.yml")

    assert workflow.count("- name: Build allowed appsettings JSON") == 1
    assert workflow.count("- name: Appsettings allowlist gate") == 1
    assert workflow.count("- name: Apply appsettings (allowlisted only)") == 1
    assert workflow.count('name: "Guard: verify BUILD_SHA app setting matches deployed SHA"') == 1
