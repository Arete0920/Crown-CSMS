"""Restored-copy safety contracts; only the explicit integration case uses PG15."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dev_backup_restore as recovery
import rehearse_dev_heritage_migrations as module
from run_dev_inquiry_migration import validate_plan, UnreviewedPlan

SHA = "a" * 40
DB = "crown_restore_123_2"


def plan():
    return [(SimpleNamespace(app_label=x.split(".", 1)[0], name=x.split(".", 1)[1]), False)
            for x in module.MIGRATIONS]


class RestoredCopyContracts(unittest.TestCase):
    def test_default_live_deploy_still_rejects_entire_graph(self):
        with self.assertRaises(UnreviewedPlan):
            validate_plan(plan())

    def test_exact_graph_accepts_independent_topological_order(self):
        self.assertEqual(len(module.verify_plan(plan())), 21)
        changed = plan()
        changed[10], changed[12] = changed[12], changed[10]
        self.assertEqual(len(module.verify_plan(changed)), 21)

    def test_unreviewed_missing_duplicate_or_backward_graph_is_denied(self):
        for mutation in ("extra", "missing", "duplicate", "backward", "empty"):
            value = plan()
            if mutation == "extra":
                value.append((SimpleNamespace(app_label="core", name="9999_unreviewed"), False))
            if mutation == "missing": value.pop()
            if mutation == "duplicate": value[0] = value[1]
            if mutation == "backward": value[0] = (value[0][0], True)
            if mutation == "empty": value = []
            with self.subTest(mutation=mutation), self.assertRaises(module.RehearsalBlocked):
                module.verify_plan(value)

    def test_every_reviewed_source_is_pinned_and_substitutions_are_denied(self):
        module.verify_manifest()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for identity in module.MIGRATIONS:
                app, name = identity.split(".", 1)
                relative = Path("backend") / app / "migrations" / (name + ".py")
                dest = root / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(module.ROOT / relative, dest)
            for identity in module.MIGRATIONS:
                app, name = identity.split(".", 1)
                path = root / "backend" / app / "migrations" / (name + ".py")
                before = path.read_bytes()
                path.write_bytes(before + b"\n# unreviewed substitution\n")
                with self.subTest(identity=identity), self.assertRaises(module.RehearsalBlocked):
                    module.verify_manifest(root)
                path.write_bytes(before)
            path.unlink()
            with self.assertRaises(module.RehearsalBlocked): module.verify_manifest(root)

    def test_wrong_database_role_cluster_or_major_is_denied(self):
        module.validate_target(DB, DB, "crown_drill", 150019, 123, "123")
        for db, actual, user, version, cluster in [
            ("postgres", "postgres", "crown_drill", 150019, 123),
            (DB, "production", "crown_drill", 150019, 123),
            (DB, DB, "admin", 150019, 123),
            (DB, DB, "crown_drill", 160015, 123),
            (DB, DB, "crown_drill", 150019, 456),
        ]:
            with self.subTest(actual=actual, user=user, version=version, cluster=cluster), \
                 self.assertRaises(module.RehearsalBlocked):
                module.validate_target(db, actual, user, version, cluster, "123")

    def test_child_does_not_inherit_source_credentials_or_activate_features(self):
        env = module.child_environment(DB, "5432", "123", SHA, {
            "PATH": "/bin", "HOME": "/tmp", "DATABASE_URL": "PRIVATE",
            "PGPASSWORD": "PRIVATE", "AZURE_CLIENT_SECRET": "PRIVATE",
            "CROWN_SIMPLEJWT_BLACKLIST_ENABLED": "true", "DJANGO_SECRET_KEY": "PRIVATE",
        })
        self.assertNotIn("PRIVATE", json.dumps(env))
        self.assertIn("@127.0.0.1:5432/" + DB, env["DATABASE_URL"])
        self.assertEqual(env["CROWN_SIMPLEJWT_BLACKLIST_ENABLED"], "false")
        for database, port in [("postgres", "5432"), (DB, "0"), (DB, "65536"), (DB, "PRIVATE")]:
            with self.subTest(database=database, port=port), self.assertRaises(module.RehearsalBlocked):
                module.child_environment(database, port, "123", SHA, {})

    def test_uncertain_failed_or_forged_child_receipt_is_denied_without_private_text(self):
        good = dict(result="PASS", source_sha=SHA, remaining_pending=0, reviewed_migrations=21,
                    target_postgres_major=15, existing_nonseed_table_values_preserved=True,
                    existing_table_counts_preserved=True, live_schema_write_performed=False,
                    baseline_migration_records=245, migrated_records=266, atomic_graph=True, legacy_inserts_preserved=True,
                    baseline_public_tables=467, baseline_fingerprint="c" * 64)
        def execute(record, code=0):
            return lambda *a, **kw: subprocess.CompletedProcess([], code, json.dumps(record), "PRIVATE")
        self.assertEqual(module.rehearse_clone(DB, "5432", "123", SHA, {}, run=execute(good)), good)
        for key, value in [("source_sha", "b" * 40), ("remaining_pending", 1),
                           ("reviewed_migrations", 18), ("target_postgres_major", 16),
                           ("existing_table_counts_preserved", False),
                           ("existing_nonseed_table_values_preserved", False),
                           ("remaining_pending", False), ("migrated_records", 267),
                           ("baseline_public_tables", False), ("baseline_public_tables", 0),
                           ("baseline_fingerprint", "PRIVATE"), ("baseline_fingerprint", None),
                           ("live_schema_write_performed", True)]:
            with self.subTest(key=key), self.assertRaises(module.RehearsalBlocked):
                module.rehearse_clone(DB, "5432", "123", SHA, {}, run=execute(dict(good, **{key: value})))
        with self.assertRaises(module.RehearsalBlocked) as caught:
            module.rehearse_clone(DB, "5432", "123", SHA, {}, run=execute({"reason": "PRIVATE"}, 1))
        self.assertNotIn("PRIVATE", str(caught.exception))
        self.assertNotIn("PRIVATE", json.dumps(caught.exception.receipt))
        with self.assertRaises(module.RehearsalBlocked):
            module.rehearse_clone(DB, "5432", "123", SHA, {}, run=execute(["PRIVATE"]))

    def test_failure_diagnostics_keep_only_reviewed_identity_and_sqlstate(self):
        record = dict(result="BLOCKED", reason="clone_migration_failed", migration=next(iter(module.MIGRATIONS)),
                      sqlstate="23505", exception="PRIVATE")
        def runner(*args, **kwargs):
            return subprocess.CompletedProcess([], 1, json.dumps(record), "PRIVATE")
        with self.assertRaises(module.RehearsalBlocked) as caught:
            module.rehearse_clone(DB, "5432", "123", SHA, {}, run=runner)
        self.assertEqual(caught.exception.receipt["sqlstate"], "23505")
        self.assertEqual(caught.exception.receipt["migration"], record["migration"])
        self.assertNotIn("PRIVATE", json.dumps(caught.exception.receipt))
        record.update(migration="PRIVATE", sqlstate="PRIVATE")
        with self.assertRaises(module.RehearsalBlocked) as denied:
            module.rehearse_clone(DB, "5432", "123", SHA, {}, run=runner)
        self.assertNotIn("migration", denied.exception.receipt)
        self.assertNotIn("sqlstate", denied.exception.receipt)

    def test_timeout_never_echoes_private_process_arguments(self):
        def timed_out(*args, **kwargs):
            raise subprocess.TimeoutExpired("PRIVATE", 1, stderr="PRIVATE")
        with self.assertRaises(module.RehearsalBlocked) as caught:
            module.rehearse_clone(DB, "5432", "123", SHA, {}, run=timed_out)
        self.assertNotIn("PRIVATE", str(caught.exception))

    def test_rehearsal_failure_keeps_restore_cleanup(self):
        cleaned = []
        @contextmanager
        def scope(*args):
            try: yield
            finally: cleaned.append(True)
        def denied(): raise module.RehearsalBlocked("existing_data_changed")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.dump"
            path.write_bytes(b"fixture")
            with patch.object(recovery, "disposable_database", scope), \
                 patch.object(recovery, "execute"), \
                 patch.object(recovery, "target_facts", return_value=({"x": 1}, [], [], 1)), \
                 self.assertRaises(module.RehearsalBlocked):
                recovery.restore_archive("b" * 64, {}, DB, path,
                                         ("snapshot", {"x": 1}, [], [], 150019), {}, after_restore=denied)
        self.assertEqual(cleaned, [True])

    def test_default_recovery_target_stays_pg16(self):
        with patch.object(recovery, "scalar", return_value="postgres|crown_drill|127.0.0.1|150019"):
            with self.assertRaises(recovery.RestoreBlocked):
                recovery.target_identity("b" * 64, {})
            recovery.target_identity("b" * 64, {}, expected_major=15)

    def test_workflow_denies_rehearsal_without_operational_authority(self):
        text = (module.ROOT / ".github/workflows/isolated-postgres-restore-drill.yml").read_text()
        command = next(x.split("run: ", 1)[1] for x in text.splitlines()
                       if 'run: test "$REHEARSE"' in x)
        for rehearsal, operational, allowed in [("true", "false", False), ("true", "true", True),
                                                 ("false", "false", True)]:
            result = subprocess.run(["bash", "-c", command], env=dict(os.environ, REHEARSE=rehearsal,
                                    OPERATIONAL=operational), capture_output=True)
            self.assertEqual(result.returncode == 0, allowed)


@unittest.skipUnless(os.environ.get("CROWN_REHEARSAL_TEST_PORT"), "requires disposable PostgreSQL15")
class PostgreSQL15MigrationProof(unittest.TestCase):
    def test_populated_pre19_graph_survives_all_reviewed_migrations(self):
        import psycopg
        from psycopg import sql
        port = os.environ["CROWN_REHEARSAL_TEST_PORT"]
        database = "crown_restore_9001_1"
        created = False
        with psycopg.connect(host="127.0.0.1", port=port, dbname="postgres", user="crown_drill",
                             password="crown-drill-password", autocommit=True) as admin:
            version = admin.execute("SHOW server_version_num").fetchone()[0]
            self.assertEqual(int(version) // 10000, 15)
            cluster = str(admin.execute("SELECT system_identifier FROM pg_control_system()").fetchone()[0])
            try:
                admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
                created = True
                sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=module.ROOT, text=True).strip()
                env = module.child_environment(database, port, cluster, sha, os.environ)
                bootstrap = '''
import django
django.setup()
from datetime import date, datetime
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone
from rehearse_dev_heritage_migrations import MIGRATIONS
e = MigrationExecutor(connection)
excluded = {tuple(x.split('.', 1)) for x in MIGRATIONS}
targets = [key for key, node in e.loader.graph.node_map.items() if key not in excluded
           and not any(child.key not in excluded for child in node.children)]
e.migrate(targets)
apps = e.loader.project_state(targets).apps
School = apps.get_model('core', 'School')
Household = apps.get_model('households', 'Household')
Student = apps.get_model('households', 'Student')
Attendance = apps.get_model('aftercare', 'AftercareAttendance')
school = School.objects.create(name='Fictional PG15 Rehearsal School')
household = Household.objects.create(school_id=school.pk, name='Fictional Historical Family')
child = Student.objects.create(school_id=school.pk, household=household,
                               first_name='Fictional', last_name='Camper', grade_level='4')
Attendance.objects.create(school_fk_id=school.pk, student_fk_id=child.pk, date=date(2025, 9, 3),
    checkin_time=timezone.make_aware(datetime(2025, 9, 3, 15, 0)),
    checkout_time=timezone.make_aware(datetime(2025, 9, 3, 17, 45)), pickup_verified=True, late_fee_cents=750)
print('Populated pre-nineteen synthetic graph ready')
'''
                # The test fixture program has no Azure credentials or DEV URL.
                env["PYTHONPATH"] += os.pathsep + str(Path(__file__).resolve().parent)
                result = subprocess.run([sys.executable, "-c", bootstrap], cwd=module.ROOT, env=env,
                                        capture_output=True, text=True, timeout=600)
                self.assertEqual(result.returncode, 0, result.stderr)
                rollback_probe = '''
import django
django.setup()
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
import rehearse_dev_heritage_migrations as probe
columns = probe.table_facts(connection)
before = {t: probe.row_digest(connection, t, names) for t, names in columns.items()}
history = set(MigrationRecorder(connection).applied_migrations())
def fail_after_complete_graph(*args):
    raise probe.RehearsalBlocked('existing_data_changed')
probe.verify_legacy_writes = fail_after_complete_graph
try:
    probe.migrate_restored_copy()
except probe.RehearsalBlocked as error:
    assert str(error) == 'existing_data_changed'
else:
    raise AssertionError('Injected late failure did not block')
assert set(MigrationRecorder(connection).applied_migrations()) == history
assert probe.table_facts(connection) == columns
assert {t: probe.row_digest(connection, t, names) for t, names in columns.items()} == before
print('Entire reviewed graph rolled back after an injected late failure')
'''
                rolled_back = subprocess.run([sys.executable, "-c", rollback_probe], cwd=module.ROOT, env=env,
                                             capture_output=True, text=True, timeout=120)
                self.assertEqual(rolled_back.returncode, 0, rolled_back.stderr)
                receipt = module.rehearse_clone(database, port, cluster, sha, os.environ)
                self.assertEqual(receipt["reviewed_migrations"], 21)
                self.assertEqual(receipt["remaining_pending"], 0)
                with psycopg.connect(host="127.0.0.1", port=port, dbname=database, user="crown_drill",
                                     password="crown-drill-password") as conn:
                    row = conn.execute('SELECT care_session,pickup_verified,late_fee_cents,handoff_verified '
                                       'FROM aftercare_aftercareattendance').fetchone()
                    self.assertEqual(row, ("PM", True, 750, False))
                legacy_insert = bootstrap[:bootstrap.index("e.migrate(targets)")] + '''
apps = e.loader.project_state(targets).apps
School = apps.get_model('core', 'School')
Student = apps.get_model('households', 'Student')
Attendance = apps.get_model('aftercare', 'AftercareAttendance')
school = School.objects.get(name='Fictional PG15 Rehearsal School')
child = Student.objects.get(school_id=school.pk)
Attendance.objects.create(school_fk_id=school.pk, student_fk_id=child.pk, date=date(2025, 9, 4),
    checkin_time=timezone.make_aware(datetime(2025, 9, 4, 15, 0)), pickup_verified=False)
apps.get_model('aftercare', 'AftercareProgramConfig').objects.create(school_fk_id=school.pk)
apps.get_model('aftercare', 'AftercareEnrollment').objects.create(school_fk_id=school.pk,
    student_fk_id=child.pk, start_date=date(2025, 9, 4), billing_model='FLAT_MONTHLY')
print('Historical care INSERT contracts passed after full graph')
'''
                legacy = subprocess.run([sys.executable, "-c", legacy_insert], cwd=module.ROOT, env=env,
                                        capture_output=True, text=True, timeout=60)
                self.assertEqual(legacy.returncode, 0, legacy.stderr)
            finally:
                if created:
                    admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database)))


if __name__ == "__main__":
    unittest.main()
