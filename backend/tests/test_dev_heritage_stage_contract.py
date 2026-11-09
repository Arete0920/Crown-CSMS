"""Collect source-only DEV stage safety tests in governed backend coverage.

This module imports tests only: it never invokes a staging command or opens
an Azure/PostgreSQL connection. The guarded stage is default-OFF in canonical DEV Deploy and requires explicit
live DEV authority; tests never execute the stage or contact Azure.
"""
from pathlib import Path
import sys

OPS_TESTS = Path(__file__).resolve().parents[2] / "scripts" / "ops"
sys.path.insert(0, str(OPS_TESTS))
from test_stage_dev_heritage_graph import StageContractTests as TestStageContract

from test_dev_reviewed24_workflow import Reviewed24WorkflowContracts as TestReviewed24Workflow
