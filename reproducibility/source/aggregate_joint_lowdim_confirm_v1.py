#!/usr/bin/env python3
"""Evidence-gated aggregation for the formal joint low-dimensional confirm run.

The independent evidentiary unit is one scenario x outer split block.  The
five training seeds are averaged inside a block before any across-block
summary is formed.  The script therefore reports descriptive cross-block
variation, not a 300-run pseudo-replication analysis.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


VERSION = "joint_lowdim_confirm_aggregate_v1"
RUNNER_VERSION = "z3_joint_lowdim_v1"
REPORT_NAME = "z3_joint_lowdim_transfer_report.json"
SCENARIOS = ("S2", "S3", "S23")
SPLITS = (20260748, 20260749, 20260750, 20260751)
STAGE1_MODELS = (
    "shared_global_only",
    "action_groups_degree1_stage1",
    "degree1_deviation_stage1",
)
RESOLVED_MODELS = (
    "action_groups_degree1_selection_resolved",
    "degree1_deviation_selection_resolved",
)
MODEL_ORDER = (*STAGE1_MODELS, *RESOLVED_MODELS)
METRICS = {
    "mean_candidate_tv": "lower",
    "p95_candidate_tv": "lower",
    "mean_excess_kl": "lower",
    "candidate_argmax_agreement": "higher",
}
PRIMARY_COMPARISONS = (
    ("action_groups_degree1", "action_groups_degree1_selection_resolved", "selection_resolved"),
    ("degree1_deviation", "degree1_deviation_selection_resolved", "selection_resolved"),
    ("action_groups_degree1", "action_groups_degree1_stage1", "stage1_pre_correction"),
    ("degree1_deviation", "degree1_deviation_stage1", "stage1_pre_correction"),
)
LAMBDA_THRESHOLD = 0.01
EPS = 1e-12


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def mean(values: Iterable[float]) -> float | None:
    values = list(values)
    return sum(values) / len(values) if values else None


def sample_sd(values: list[float]) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return 0.0
    center = mean(values)
    return math.sqrt(sum((value - center) ** 2 for value in values) / (len(values) - 1))


def descriptive_summary(values: Iterable[float]) -> dict[str, Any]:
    xs = [float(value) for value in values if value is not None]
    if not xs:
        return {"n": 0, "mean": None, "sample_sd": None, "se": None, "descriptive_mean_pm_1_96_se": None, "min": None, "max": None}
    center = mean(xs)
    sd = sample_sd(xs)
    se = sd / math.sqrt(len(xs)) if sd is not None else None
    return {
        "n": len(xs),
        "mean": center,
        "sample_sd": sd,
        "se": se,
        "descriptive_mean_pm_1_96_se": [center - 1.96 * se, center + 1.96 * se] if se is not None else None,
        "min": min(xs),
        "max": max(xs),
    }


def block_id(scenario: str, split_seed: int) -> str:
    return f"{scenario}/split_{split_seed}"


def expected_blocks() -> set[tuple[str, int]]:
    return {(scenario, split) for scenario in SCENARIOS for split in SPLITS}


def report_files(input_dir: Path) -> list[Path]:
    return sorted(input_dir.rglob(REPORT_NAME))


def validate_reports(input_dir: Path, frozen: dict[str, Any], verify_artifacts: bool) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    expected_candidates = frozen.get("candidate_order")
    if expected_candidates != ["shared_global_only", "action_groups_degree1", "degree1_deviation"]:
        raise RuntimeError(f"STOP: frozen candidate order mismatch: {expected_candidates}")
    reports: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    artifact_count = 0
    for path in report_files(input_dir):
        report = load_json(path)
        scenario, split = report.get("scenario"), report.get("split_seed")
        key = (scenario, split)
        if report.get("status") != "PASS":
            raise RuntimeError(f"STOP: non-PASS report: {path}")
        if report.get("runner_version") != RUNNER_VERSION or report.get("condition") != "joint":
            raise RuntimeError(f"STOP: incompatible report identity: {path}")
        if report.get("candidate_order") != expected_candidates:
            raise RuntimeError(f"STOP: candidate order drift: {path}")
        if key not in expected_blocks() or key in seen:
            raise RuntimeError(f"STOP: unexpected or duplicate report block {key}: {path}")
        seen.add(key)
        runs = report.get("per_run", [])
        if len(runs) != 25:
            raise RuntimeError(f"STOP: expected 25 per_run entries in {path}, found {len(runs)}")
        by_model: dict[str, set[int]] = defaultdict(set)
        for run in runs:
            model, seed = run.get("model"), run.get("seed")
            by_model[model].add(seed)
            if verify_artifacts:
                artifact = run.get("artifact", {}).get("path")
                if not artifact or not (path.parent / artifact).is_file():
                    raise RuntimeError(f"STOP: missing artifact for {path}: {artifact}")
                artifact_count += 1
        if set(by_model) != set(MODEL_ORDER) or any(seeds != set(range(5)) for seeds in by_model.values()):
            raise RuntimeError(f"STOP: model/seed coverage mismatch: {path}")
        for candidate in ("action_groups_degree1", "degree1_deviation"):
            payload = report.get("stage2", {}).get(candidate)
            if not isinstance(payload, dict) or payload.get("status") not in {"PASS", "STRUCTURAL_NO_OP"}:
                raise RuntimeError(f"STOP: malformed stage2 payload {candidate}: {path}")
        reports.append({"path": path, "report": report})
    missing = expected_blocks() - seen
    if missing or len(reports) != 12:
        raise RuntimeError(f"STOP: incomplete formal block matrix; missing={sorted(missing)} found={len(reports)}")
    runner_hashes = {item["report"].get("provenance", {}).get("runner_sha256") for item in reports}
    if len(runner_hashes) != 1 or None in runner_hashes:
        raise RuntimeError(f"STOP: runner provenance mismatch: {runner_hashes}")
    return reports, {
        "report_files": len(reports),
        "blocks": [block_id(scenario, split) for scenario, split in sorted(seen)],
        "runner_sha256": next(iter(runner_hashes)),
        "artifacts_verified": verify_artifacts,
        "artifact_count": artifact_count if verify_artifacts else None,
    }


def metric_records(reports: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    overall, per_action = [], []
    for item in reports:
        path, report = item["path"], item["report"]
        block = block_id(report["scenario"], int(report["split_seed"]))
        for run in report["per_run"]:
            metrics = run.get("metrics", {})
            for metric, value in metrics.get("primary_target_cells", {}).items():
                if metric in METRICS and isinstance(value, (int, float)):
                    overall.append({"block": block, "scenario": report["scenario"], "split_seed": int(report["split_seed"]), "model": run["model"], "seed": int(run["seed"]), "metric": metric, "value": float(value), "source": str(path)})
            for action, values in metrics.get("primary_target_per_action", {}).items():
                n_cells = values.get("n_cells", 0)
                if not isinstance(n_cells, (int, float)) or n_cells <= 0:
                    continue
                for metric, value in values.items():
                    if metric in METRICS and isinstance(value, (int, float)):
                        per_action.append({"block": block, "scenario": report["scenario"], "split_seed": int(report["split_seed"]), "model": run["model"], "seed": int(run["seed"]), "action": str(action), "metric": metric, "value": float(value), "n_cells": int(n_cells), "source": str(path)})
    return overall, per_action


def block_average(records: list[dict[str, Any]], fields: tuple[str, ...]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        grouped[tuple(row[field] for field in fields)].append(row)
    out = []
    for key, rows in sorted(grouped.items(), key=str):
        record = {field: value for field, value in zip(fields, key)}
        record["value"] = mean(row["value"] for row in rows)
        record["n_seed_runs"] = len(rows)
        if "n_cells" in rows[0]:
            n_cells = {row["n_cells"] for row in rows}
            if len(n_cells) != 1:
                raise RuntimeError(f"STOP: action-cell count varies across seeds: {record}")
            record["n_cells"] = next(iter(n_cells))
        out.append(record)
    return out


def aggregate_metric_table(rows: list[dict[str, Any]], group_fields: tuple[str, ...], label: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[field] for field in group_fields)].append(row)
    out = []
    for key, items in sorted(grouped.items(), key=str):
        row = {field: value for field, value in zip(group_fields, key)}
        row["direction"] = METRICS[row["metric"]]
        row[label] = descriptive_summary(item["value"] for item in items)
        row["block_values"] = [{"block": item["block"], "value": item["value"]} for item in sorted(items, key=lambda x: x["block"])]
        out.append(row)
    return out


def paired_comparisons(block_metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lookup = {(row["block"], row["model"], row["metric"]): row for row in block_metrics}
    blocks = sorted({row["block"] for row in block_metrics})
    out = []
    for candidate_name, candidate_model, comparison_role in PRIMARY_COMPARISONS:
        for metric, direction in METRICS.items():
            rows = []
            for block in blocks:
                control = lookup.get((block, "shared_global_only", metric))
                candidate = lookup.get((block, candidate_model, metric))
                if control is None or candidate is None:
                    continue
                raw_delta = candidate["value"] - control["value"]
                improvement = -raw_delta if direction == "lower" else raw_delta
                rows.append({"block": block, "scenario": control["scenario"], "split_seed": control["split_seed"], "control_value": control["value"], "candidate_value": candidate["value"], "candidate_minus_control": raw_delta, "direction_aligned_improvement": improvement})
            for scope, scoped_rows in [("all_scenarios", rows), *[(scenario, [row for row in rows if row["scenario"] == scenario]) for scenario in SCENARIOS]]:
                if not scoped_rows:
                    continue
                improvements = [row["direction_aligned_improvement"] for row in scoped_rows]
                out.append({
                    "comparison_role": comparison_role,
                    "candidate": candidate_name,
                    "candidate_model": candidate_model,
                    "control_model": "shared_global_only",
                    "scope": scope,
                    "metric": metric,
                    "direction": direction,
                    "positive_means": "candidate improves on shared_global_only",
                    "direction_aligned_improvement": descriptive_summary(improvements),
                    "win_count": sum(value > EPS for value in improvements),
                    "tie_count": sum(abs(value) <= EPS for value in improvements),
                    "loss_count": sum(value < -EPS for value in improvements),
                    "block_deltas": scoped_rows,
                })
    return out


def per_action_and_worst(block_actions: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    per_action = aggregate_metric_table(block_actions, ("scenario", "model", "action", "metric"), "summary_over_outer_blocks")
    all_action = aggregate_metric_table(block_actions, ("model", "action", "metric"), "summary_over_outer_blocks")
    for row in per_action:
        row["scope"] = row["scenario"]
    for row in all_action:
        row["scope"] = "all_scenarios"
    by_block_metric: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in block_actions:
        by_block_metric[(row["block"], row["model"], row["metric"])].append(row)
    worst_by_block, variance_by_block = [], []
    for (block, model, metric), rows in sorted(by_block_metric.items()):
        values = [row["value"] for row in rows]
        center = mean(values)
        variance = sum((value - center) ** 2 for value in values) / len(values)
        direction = METRICS[metric]
        worst = max(rows, key=lambda row: row["value"]) if direction == "lower" else min(rows, key=lambda row: row["value"])
        worst_by_block.append({"block": block, "scenario": worst["scenario"], "model": model, "metric": metric, "worst_action": worst["action"], "worst_value": worst["value"], "n_held_actions": len(rows)})
        variance_by_block.append({"block": block, "scenario": worst["scenario"], "model": model, "metric": metric, "n_held_actions": len(rows), "action_variance": variance, "action_sd": math.sqrt(variance)})
    worst_summary, variance_summary = [], []
    for scope, source in [("all_scenarios", worst_by_block), *[(scenario, [row for row in worst_by_block if row["scenario"] == scenario]) for scenario in SCENARIOS]]:
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in source:
            grouped[(row["model"], row["metric"])].append(row)
        for (model, metric), rows in sorted(grouped.items()):
            worst_summary.append({"scope": scope, "model": model, "metric": metric, "worst_value_summary": descriptive_summary(row["worst_value"] for row in rows), "worst_action_counts": dict(sorted(Counter(row["worst_action"] for row in rows).items())), "n_outer_blocks": len(rows)})
    for scope, source in [("all_scenarios", variance_by_block), *[(scenario, [row for row in variance_by_block if row["scenario"] == scenario]) for scenario in SCENARIOS]]:
        grouped = defaultdict(list)
        for row in source:
            grouped[(row["model"], row["metric"])].append(row)
        for (model, metric), rows in sorted(grouped.items()):
            variance_summary.append({"scope": scope, "model": model, "metric": metric, "action_variance_summary": descriptive_summary(row["action_variance"] for row in rows), "mean_action_sd": mean(row["action_sd"] for row in rows), "n_outer_blocks": len(rows)})
    return per_action + all_action, worst_summary, variance_summary


def stage2_audit(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for item in reports:
        report = item["report"]
        for candidate, payload in report["stage2"].items():
            records.append({"block": block_id(report["scenario"], int(report["split_seed"])), "scenario": report["scenario"], "split_seed": int(report["split_seed"]), "candidate": candidate, "structural_status": payload.get("status"), "selected_candidate": payload.get("selected_candidate"), "selected_ridge": payload.get("selected_ridge"), "nullspace_audit": payload.get("nullspace_audit", {})})
    out = []
    for scope, rows in [("all_scenarios", records), *[(scenario, [row for row in records if row["scenario"] == scenario]) for scenario in SCENARIOS]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[row["candidate"]].append(row)
        for candidate, items in sorted(grouped.items()):
            selected = Counter(str(item["selected_candidate"]) for item in items)
            statuses = Counter(str(item["structural_status"]) for item in items)
            ridges = [float(item["selected_ridge"]) for item in items if isinstance(item["selected_ridge"], (int, float))]
            out.append({"scope": scope, "candidate": candidate, "n_outer_blocks": len(items), "structural_status_counts": dict(sorted(statuses.items())), "selected_candidate_counts": dict(sorted(selected.items())), "structural_no_op_count": statuses["STRUCTURAL_NO_OP"], "selected_no_op_count": selected["no_op"], "selected_non_no_op_count": len(items) - selected["no_op"], "selected_ridge_summary_excluding_no_op": descriptive_summary(ridges), "by_block": sorted(items, key=lambda x: x["block"])})
    return out


def lambda_audit(reports: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records = []
    for item in reports:
        report = item["report"]
        for model, payload in report["stage1"].items():
            for trace in payload.get("selector_trace", []):
                if isinstance(trace.get("chosen_lambda"), (int, float)):
                    records.append({"block": block_id(report["scenario"], int(report["split_seed"])), "scenario": report["scenario"], "split_seed": int(report["split_seed"]), "model": model, "coordinate": trace.get("coordinate"), "chosen_lambda": float(trace["chosen_lambda"])})
    coordinate_summary = []
    for scope, rows in [("all_scenarios", records), *[(scenario, [row for row in records if row["scenario"] == scenario]) for scenario in SCENARIOS]]:
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[(row["model"], row["coordinate"])].append(row)
        for (model, coordinate), items in sorted(grouped.items()):
            values = [item["chosen_lambda"] for item in items]
            coordinate_summary.append({"scope": scope, "model": model, "coordinate": coordinate, "n_outer_blocks": len(items), "lambda_counts": dict(sorted(Counter(str(value) for value in values).items())), "lambda_summary": descriptive_summary(values), "active_low_penalty_rate_lambda_le_0_01": sum(value <= LAMBDA_THRESHOLD for value in values) / len(values), "by_block": sorted(items, key=lambda x: x["block"])})
    counterpart = {
        "action_groups_degree1": "degree1_action_group_deviation",
        "degree1_deviation": "degree1_deviation",
    }
    model_by_candidate = {"action_groups_degree1": "action_groups_degree1", "degree1_deviation": "degree1_deviation"}
    comparisons = []
    for candidate, deviation_coordinate in counterpart.items():
        model = model_by_candidate[candidate]
        relevant = [row for row in records if row["model"] == model]
        by_block: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        for row in relevant:
            by_block[row["block"]][row["coordinate"]] = row
        pairs = []
        for block, values in by_block.items():
            if "degree1_global" in values and deviation_coordinate in values:
                global_lambda = values["degree1_global"]["chosen_lambda"]
                deviation_lambda = values[deviation_coordinate]["chosen_lambda"]
                relation = "global_more_active" if global_lambda < deviation_lambda else "deviation_more_active" if global_lambda > deviation_lambda else "tie"
                pairs.append({"block": block, "scenario": values["degree1_global"]["scenario"], "global_lambda": global_lambda, "deviation_lambda": deviation_lambda, "relation": relation})
        for scope, scoped in [("all_scenarios", pairs), *[(scenario, [row for row in pairs if row["scenario"] == scenario]) for scenario in SCENARIOS]]:
            if not scoped:
                continue
            counts = Counter(row["relation"] for row in scoped)
            comparisons.append({"scope": scope, "candidate": candidate, "global_coordinate": "degree1_global", "deviation_coordinate": deviation_coordinate, "n_outer_blocks": len(scoped), "global_more_active_rate": counts["global_more_active"] / len(scoped), "deviation_more_active_rate": counts["deviation_more_active"] / len(scoped), "tie_rate": counts["tie"] / len(scoped), "relation_counts": dict(sorted(counts.items())), "by_block": sorted(scoped, key=lambda x: x["block"])})
    return coordinate_summary, comparisons


def validate_geometry(geometry_path: Path | None) -> dict[str, Any] | None:
    if geometry_path is None:
        return None
    geometry = load_json(geometry_path)
    if geometry.get("schema_version") != "joint_lowdim_geometry_audit_v1":
        raise RuntimeError("STOP: unsupported joint geometry audit schema")
    summary = {row["candidate"]: row for row in geometry.get("candidate_summary", [])}
    required = {"degree1_deviation", "action_groups_degree1"}
    if not required <= set(summary):
        raise RuntimeError("STOP: geometry audit lacks formal joint candidates")
    if not summary["degree1_deviation"].get("all_splits_pipeline_eligible"):
        raise RuntimeError("STOP: degree1_deviation geometry is not pipeline eligible")
    if not summary["action_groups_degree1"].get("all_splits_pipeline_eligible"):
        raise RuntimeError("STOP: action_groups_degree1 geometry is not pipeline eligible")
    return {"path": str(geometry_path), "sha256": sha256(geometry_path), "status": geometry.get("status"), "outcome_blind": geometry.get("outcome_blind"), "candidate_summary": summary}


def csv_rows(rows: list[dict[str, Any]], fields: list[str], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def fmt(value: Any) -> str:
    return "—" if value is None else f"{float(value):.6g}" if isinstance(value, (int, float)) else str(value)


def markdown(result: dict[str, Any]) -> str:
    lines = ["# Formal joint low-dimensional confirm aggregation", "", "## Scope and evidence boundary", "", "- Research question: whether the two pre-registered compact joint mechanisms improve held joint state-action-cell prediction over the shared-global control.", "- Estimand: test-cell TV/KL/argmax agreement, with five training seeds averaged within each scenario x split block.", "- Outer evidence units: 12 blocks (S2/S3/S23 x four confirmatory splits); training seeds are not independent outer experiments.", "- Eligibility: pipeline and predictive eligible for this synthetic predictive estimand; not causal eligible. No policy, rollout, encoder, real-data, or causal claim follows.", "", "## Integrity", "", f"- Reports: {result['metadata']['report_files']}/12 PASS; artifacts verified: {result['metadata']['artifact_count']}/300.", f"- Runner SHA256: `{result['metadata']['runner_sha256']}`.", f"- Geometry audit: `{result['metadata']['geometry_audit']['status']}` (outcome blind: `{result['metadata']['geometry_audit']['outcome_blind']}`).", "", "## Primary selection-resolved comparisons: all scenarios", "", "Positive improvement means lower TV/KL or higher agreement than `shared_global_only`; the interval is descriptive mean +/- 1.96 SE across outer blocks, not a causal or pseudo-replicated test.", "", "| candidate | metric | mean improvement | descriptive interval | wins/ties/losses |", "|---|---|---:|---|---:|"]
    primary = [row for row in result["paired_comparisons"] if row["comparison_role"] == "selection_resolved" and row["scope"] == "all_scenarios"]
    for row in primary:
        summary = row["direction_aligned_improvement"]
        interval = summary["descriptive_mean_pm_1_96_se"]
        lines.append(f"| {row['candidate']} | {row['metric']} | {fmt(summary['mean'])} | [{fmt(interval[0])}, {fmt(interval[1])}] | {row['win_count']}/{row['tie_count']}/{row['loss_count']} |")
    lines += ["", "## Mean TV by scenario: selection-resolved versus control", "", "| candidate | scenario | mean improvement | wins/ties/losses |", "|---|---|---:|---:|"]
    for row in result["paired_comparisons"]:
        if row["comparison_role"] == "selection_resolved" and row["scope"] != "all_scenarios" and row["metric"] == "mean_candidate_tv":
            lines.append(f"| {row['candidate']} | {row['scope']} | {fmt(row['direction_aligned_improvement']['mean'])} | {row['win_count']}/{row['tie_count']}/{row['loss_count']} |")
    lines += ["", "## Stage-2 selection audit", "", "| candidate | selected candidates across 12 blocks | structural no-op |", "|---|---|---:|"]
    for row in result["stage2_audit"]:
        if row["scope"] == "all_scenarios":
            lines.append(f"| {row['candidate']} | `{row['selected_candidate_counts']}` | {row['structural_no_op_count']} |")
    lines += ["", "## Lambda audit: degree-1 global versus declared deviation coordinate", "", "A smaller lambda is operationally treated as a more active coordinate. This is a selector description, not proof that a degree is scientifically correct.", "", "| candidate | global more active | deviation more active | tie |", "|---|---:|---:|---:|"]
    for row in result["lambda_global_vs_deviation"]:
        if row["scope"] == "all_scenarios":
            lines.append(f"| {row['candidate']} | {row['global_more_active_rate']:.3f} | {row['deviation_more_active_rate']:.3f} | {row['tie_rate']:.3f} |")
    lines += ["", "## Worst held action: selection-resolved models", "", "| model | metric | mean block-wise worst value | worst-action counts |", "|---|---|---:|---|"]
    for row in result["worst_action"]:
        if row["scope"] == "all_scenarios" and row["model"] in RESOLVED_MODELS:
            lines.append(f"| {row['model']} | {row['metric']} | {fmt(row['worst_value_summary']['mean'])} | `{row['worst_action_counts']}` |")
    lines += ["", "## Files", "", "- `joint_lowdim_confirm_aggregate.json`: complete machine-readable audit and all block values.", "- `joint_lowdim_paired_deltas.csv`: primary and stage-1 paired comparisons at the outer-block level.", "- `joint_lowdim_per_action.csv`: per-action summaries with held-cell coverage.", "- `joint_lowdim_lambda_audit.csv`: coordinate lambda summaries.", "", "## Next falsification test", "", "The present result can establish only whether these frozen mechanisms transfer in this synthetic joint protocol. A high-N scaling or structured-holdout replication remains necessary to test robustness beyond these four outer splits."]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--frozen-config", required=True, type=Path)
    parser.add_argument("--geometry-audit", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--verify-artifacts", action="store_true")
    args = parser.parse_args()
    input_dir, output_dir = args.input_dir.resolve(), args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError(f"STOP: refusing to overwrite non-empty output directory: {output_dir}")
    frozen = load_json(args.frozen_config.resolve())
    if frozen.get("contract_version") != "z3_joint_lowdim_v1" or frozen.get("status") != "FROZEN_BEFORE_SMOKE":
        raise RuntimeError("STOP: joint frozen config mismatch")
    reports, metadata = validate_reports(input_dir, frozen, args.verify_artifacts)
    geometry = validate_geometry(args.geometry_audit.resolve())
    overall_records, action_records = metric_records(reports)
    block_metrics = block_average(overall_records, ("block", "scenario", "split_seed", "model", "metric"))
    block_actions = block_average(action_records, ("block", "scenario", "split_seed", "model", "action", "metric"))
    overall_summary = aggregate_metric_table(block_metrics, ("model", "metric"), "summary_over_outer_blocks")
    scenario_summary = aggregate_metric_table(block_metrics, ("scenario", "model", "metric"), "summary_over_outer_blocks")
    per_action_summary, worst_action, action_variance = per_action_and_worst(block_actions)
    comparisons = paired_comparisons(block_metrics)
    stage2 = stage2_audit(reports)
    lambda_coordinates, lambda_comparisons = lambda_audit(reports)
    result = {
        "schema_version": VERSION,
        "metadata": {**metadata, "input_dir": str(input_dir), "frozen_config": str(args.frozen_config.resolve()), "frozen_config_sha256": sha256(args.frozen_config.resolve()), "geometry_audit": geometry, "outer_unit": "scenario_x_confirmatory_split", "outer_unit_count": 12, "within_outer_unit_training_seeds": 5, "metrics": METRICS, "lambda_active_low_penalty_threshold": LAMBDA_THRESHOLD},
        "research_protocol": {"question": "Under joint state-and-action holdout, do compact degree-1 deviation or action-group mechanisms transfer to unseen state-action cells?", "estimand": "test-cell candidate TV/KL and argmax agreement, paired against shared-global control", "intervention_variable": "declared mechanism columns and selection-resolved fit-nullspace correction", "pipeline_eligible": True, "predictive_eligible": True, "causal_eligible": False, "non_claims": frozen["non_claims"]},
        "overall_model_metrics": overall_summary,
        "scenario_model_metrics": scenario_summary,
        "per_action_metrics": per_action_summary,
        "worst_action": worst_action,
        "action_variance": action_variance,
        "paired_comparisons": comparisons,
        "stage2_audit": stage2,
        "lambda_coordinate_audit": lambda_coordinates,
        "lambda_global_vs_deviation": lambda_comparisons,
        "block_metrics": block_metrics,
        "block_action_metrics": block_actions,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "joint_lowdim_confirm_aggregate.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "joint_lowdim_confirm_aggregate.md").write_text(markdown(result), encoding="utf-8")
    paired_csv = []
    for row in comparisons:
        for block in row["block_deltas"]:
            paired_csv.append({"comparison_role": row["comparison_role"], "candidate": row["candidate"], "scope": row["scope"], "metric": row["metric"], "direction": row["direction"], **block})
    csv_rows(paired_csv, ["comparison_role", "candidate", "scope", "metric", "direction", "block", "scenario", "split_seed", "control_value", "candidate_value", "candidate_minus_control", "direction_aligned_improvement"], output_dir / "joint_lowdim_paired_deltas.csv")
    action_csv = []
    for row in per_action_summary:
        summary = row["summary_over_outer_blocks"]
        action_csv.append({"scenario": row.get("scenario", "all_scenarios"), "model": row["model"], "action": row["action"], "metric": row["metric"], "direction": row["direction"], "n_outer_blocks": summary["n"], "mean": summary["mean"], "sample_sd": summary["sample_sd"], "min": summary["min"], "max": summary["max"]})
    csv_rows(action_csv, ["scenario", "model", "action", "metric", "direction", "n_outer_blocks", "mean", "sample_sd", "min", "max"], output_dir / "joint_lowdim_per_action.csv")
    lambda_csv = []
    for row in lambda_coordinates:
        summary = row["lambda_summary"]
        lambda_csv.append({"scope": row["scope"], "model": row["model"], "coordinate": row["coordinate"], "n_outer_blocks": row["n_outer_blocks"], "lambda_counts": json.dumps(row["lambda_counts"], ensure_ascii=False), "mean_lambda": summary["mean"], "active_low_penalty_rate_lambda_le_0_01": row["active_low_penalty_rate_lambda_le_0_01"]})
    csv_rows(lambda_csv, ["scope", "model", "coordinate", "n_outer_blocks", "lambda_counts", "mean_lambda", "active_low_penalty_rate_lambda_le_0_01"], output_dir / "joint_lowdim_lambda_audit.csv")
    print(json.dumps({"status": "PASS", "output_dir": str(output_dir), "reports": len(reports), "outer_blocks": 12, "artifacts_verified": args.verify_artifacts}, ensure_ascii=False))


if __name__ == "__main__":
    main()
