"""Collect source-only DEV stage safety tests in governed backend coverage.

This module imports tests only: it never invokes a staging command or opens
an Azure/PostgreSQL connection. The source-only script remains disconnected
from every deployment or migration-writing workflow.
"""
from pathlib import Path
import sys

OPS_TESTS = Path(__file__).resolve().parents[2] / "scripts" / "ops"
sys.path.insert(0, str(OPS_TESTS))
from test_stage_dev_heritage_graph import StageContractTests as TestStageContract
