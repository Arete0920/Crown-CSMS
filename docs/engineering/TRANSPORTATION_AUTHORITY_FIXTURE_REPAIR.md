# Transportation authority test repair

Base: b0a537fc6ce3bcb26eb6b007b43088bd3da1e2e1
Branch: test/transportation-authority-fixture-scope
Decision owner: TC Megahan; audit remediation authorized.

Outcome: restrict the historical role adapter to test_transportation so persistent-RBAC tests retain explicit grants and spoofed-role inputs. Align cross-school target rejection with the canonical resolver's documented 404 concealment contract, while adding a separate test proving that foreign-school grants cannot authorize home-school reads or writes (403).

Allowed: transportation tests/conftest.py, test_persistent_rbac.py, this evidence record. Forbidden: runtime permissions, global fixtures, migrations, dependencies, workflow gates, deployment.

Validation under focused Django 5.2.17 / SQLite settings with real transportation app, core models, canonical resolver and permissions: original persistent-RBAC suite 7 failures, all helper signature errors. After fixture correction, broader suite 51 passed and 1 failed due to obsolete 403 expectation for cross-school concealment. After contract correction and additional security case, entire transportation suite: 53 passed in 0.66s. No skipped assertions or weakened permission behavior.

Command: python -m pytest validation/backend/transportation/tests -q --nomigrations --tb=short (DJANGO_SETTINGS_MODULE=repair_settings).

Full production settings, middleware, migrations, PostgreSQL, exact-head CI and deployed runtime are NOT VERIFIED. CI startup is independently blocked. This is test repair, not release certification. Rollback: revert this test-only commit.
