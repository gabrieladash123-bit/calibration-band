import ast
from fractions import Fraction
import hashlib
from itertools import product
import json
from pathlib import Path
import re

import pytest


CONTRACT = "contracts/calibration_band.py"
SOURCE = "example/calibration-band/" + "e" * 40 + "/fixtures/restoration.json"
CRITERION = "The post-restart read recovered the pre-restart payload intact."
BODY = Path("fixtures/restoration.json").read_bytes()
DIGEST = hashlib.sha256(BODY).hexdigest()
LABELS = {
    "a01": "PASS", "a02": "PASS", "a03": "PASS", "a04": "FAIL",
    "b01": "FAIL", "b02": "FAIL", "b03": "UNKNOWN", "b04": "UNKNOWN",
    "c01": "PASS", "c02": "PASS", "c03": "PASS", "c04": "FAIL",
}


@pytest.fixture
def contract(direct_deploy):
    return direct_deploy(CONTRACT, sdk_version="v0.2.16")


def configure(vm, labels=LABELS, body=BODY):
    vm.mock_web(re.escape("https://raw.githubusercontent.com/" + SOURCE), {"status": 200, "body": body})
    vm.mock_llm("CalibrationBand benchmark adjudication", json.dumps(labels))


def test_fit_and_immutable_duplicate(direct_vm, contract, direct_bob):
    configure(direct_vm)
    with direct_vm.prank(direct_bob):
        fit_id = contract.fit(SOURCE, DIGEST, CRITERION)
    assert direct_vm.run_validator() is True
    stored = contract.get_fit(fit_id)
    assert stored["lower_blocks"] == [[20, 50, 3, 8], [80, 80, 3, 4]]
    assert stored["upper_blocks"] == [[20, 50, 5, 8], [80, 80, 3, 4]]
    assert contract.get_point(fit_id, 50) == {
        "score": 50, "counts": {"PASS": 0, "FAIL": 2, "UNKNOWN": 2},
        "lower": [3, 8], "upper": [5, 8],
    }
    assert contract.get_point(fit_id, 60) is None
    direct_vm.clear_mocks()
    with direct_vm.expect_revert("Fit already published"):
        contract.fit(SOURCE, DIGEST, CRITERION)
    assert contract.get_fit(fit_id) == stored


@pytest.mark.parametrize("replacement", ["PASS", "FAIL"])
def test_validator_rejects_any_changed_label(direct_vm, contract, replacement):
    configure(direct_vm)
    contract.fit(SOURCE, DIGEST, CRITERION)
    direct_vm.clear_mocks()
    configure(direct_vm, {**LABELS, "b03": replacement})
    assert direct_vm.run_validator() is False


def test_validator_refetches_report_and_checks_digest(direct_vm, contract):
    configure(direct_vm)
    contract.fit(SOURCE, DIGEST, CRITERION)
    direct_vm.clear_mocks()
    configure(direct_vm, body=BODY + b" ")
    assert direct_vm.run_validator() is False


@pytest.mark.parametrize("labels", [{"a01": "PASS"}, {**LABELS, "b03": True}, {**LABELS, "z99": "PASS"}])
def test_rejects_invalid_model_results(direct_vm, contract, labels):
    configure(direct_vm, labels)
    with direct_vm.expect_revert("Report acquisition or adjudication failed"):
        contract.fit(SOURCE, DIGEST, CRITERION)


def test_rejects_unpinned_source(contract, direct_vm):
    with direct_vm.expect_revert("Expected a commit-pinned report"):
        contract.fit(SOURCE.replace("e" * 40, "main"), DIGEST, CRITERION)


def test_changed_label_changes_calibrated_threshold(direct_vm, contract):
    configure(direct_vm, {**LABELS, "b03": "PASS"})
    fit_id = contract.fit(SOURCE, DIGEST, CRITERION)
    assert contract.get_point(fit_id, 20)["lower"] == [4, 8]
    assert contract.get_point(fit_id, 20)["upper"] == [5, 8]


def test_pav_matches_exact_min_max_and_bounds_every_completion():
    tree = ast.parse(Path(CONTRACT).read_text(encoding="utf-8"))
    funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in {"band", "pool_adjacent"}]
    namespace = {}
    exec(compile(ast.Module(body=funcs, type_ignores=[]), CONTRACT, "exec"), namespace)
    scores = [20, 20, 50, 80]
    bounds = namespace["band"]
    for labels in product(("PASS", "FAIL", "UNKNOWN"), repeat=len(scores)):
        points = bounds([{"score": score, "outcome": label} for score, label in zip(scores, labels)])["points"]
        options = [(0, 1) if label == "UNKNOWN" else (int(label == "PASS"),) for label in labels]
        completions = []
        for resolved in product(*options):
            totals = [sum(resolved[:2]), resolved[2], resolved[3]]
            weights = [2, 1, 1]
            completions.append([
                max(min(Fraction(sum(totals[start:end + 1]), sum(weights[start:end + 1]))
                        for end in range(index, 3)) for start in range(index + 1))
                for index in range(3)
            ])
        for index, point in enumerate(points):
            assert Fraction(*point["lower"]) == min(row[index] for row in completions)
            assert Fraction(*point["upper"]) == max(row[index] for row in completions)
