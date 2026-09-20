#!/usr/bin/env python3
"""Aggregate the frozen high-N experiment without seed pseudo-replication.

Each scenario x condition x split x N block contains five training seeds.  We
average those seeds within the block and only then summarize the four fresh
outer splits.  A three-level nested N grid is a scaling intervention, not
three independent replications.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


VERSION = "z3_high_n_scaling_aggregate_v2"
RUNNER_VERSION = "z3_high_n_scaling_v1"
N_GRID = (4096, 16384, 65536)
SCENARIOS = ("S2", "S3", "S23")
CONDITIONS = ("state_only", "state_action")
SPLITS = (20260748, 20260749, 20260750, 20260751)
MODELS = ("AR", "T123_R_degree_global_deviation")
METRICS = {"mean_candidate_tv": "lower", "mean_excess_kl": "lower", "candidate_argmax_agreement": "higher"}
EPS = 1e-12


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def sample_sd(values: list[float]) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return 0.0
    center = mean(values)
    return math.sqrt(sum((value - center) ** 2 for value in values) / (len(values) - 1))


def summary(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0, "mean": None, "sample_sd": None, "se": None, "descriptive_mean_pm_1_96_se": None, "min": None, "max": None, "values": []}
    center, sd = mean(values), sample_sd(values)
    se = sd / math.sqrt(len(values)) if sd is not None else None
    return {"n": len(values), "mean": center, "sample_sd": sd, "se": se, "descriptive_mean_pm_1_96_se": [center - 1.96 * se, center + 1.96 * se] if se is not None else None, "min": min(values), "max": max(values), "values": values}


def expected_keys() -> set[tuple[int, str, str, int]]:
    return {(n, scenario, condition, split) for n in N_GRID for scenario in SCENARIOS for condition in CONDITIONS for split in SPLITS}


def validate_config(path: Path) -> dict[str, Any]:
    frozen = read(path)
    if frozen.get("contract_version") != "z3_high_n_scaling_v1" or frozen.get("status") != "FROZEN_BEFORE_SMOKE":
        raise RuntimeError("STOP: high-N frozen config mismatch")
    if tuple(frozen.get("n_grid", [])) != N_GRID or tuple(frozen.get("scenarios", [])) != SCENARIOS or tuple(frozen.get("conditions", [])) != CONDITIONS or tuple(frozen.get("fresh_confirmatory_split_seeds", [])) != SPLITS or tuple(frozen.get("models", [])) != MODELS:
        raise RuntimeError("STOP: high-N frozen matrix mismatch")
    return frozen


def validate_and_load(input_dir: Path, frozen: dict[str, Any], verify_artifacts: bool) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    found: dict[tuple[int, str, str, int], dict[str, Any]] = {}
    artifacts = 0
    runner_hashes: set[str] = set()
    config_hashes: set[str] = set()
    for path in sorted(input_dir.rglob("z3_high_n_scaling_block_report.json")):
        report = read(path)
        key = (int(report.get("n_sequences", -1)), report.get("scenario"), report.get("condition"), int(report.get("split_seed", -1)))
        if report.get("status") != "PASS" or report.get("runner_version") != RUNNER_VERSION or key not in expected_keys() or key in found:
            raise RuntimeError(f"STOP: malformed, unexpected, or duplicate report: {path}")
        training = report.get("training_config", {})
        frozen_training = frozen["training"]
        if any(training.get(name) != frozen_training.get(name) for name in ("n_seeds", "epochs", "patience", "batch_size", "selector", "lambda_grid", "tie_tolerance")) or abs(float(training.get("lr", float("nan"))) - float(frozen_training["lr"])) > 1e-15:
            raise RuntimeError(f"STOP: training config drift: {path}")
        entries = report.get("per_run", [])
        by_model: dict[str, set[int]] = defaultdict(set)
        for entry in entries:
            by_model[entry.get("model")].add(int(entry.get("seed", -1)))
            if verify_artifacts:
                artifact = entry.get("artifact", {}).get("path")
                if not artifact or not (path.parent / artifact).is_file():
                    raise RuntimeError(f"STOP: missing artifact in {path}: {artifact}")
                artifacts += 1
        if len(entries) != 10 or set(by_model) != set(MODELS) or any(seeds != set(range(5)) for seeds in by_model.values()):
            raise RuntimeError(f"STOP: expected 2 models x 5 seeds: {path}")
        for entry in entries:
            if set(METRICS).difference(entry.get("metrics", {}).get("primary_target_cells", {})):
                raise RuntimeError(f"STOP: primary metrics missing: {path}")
        runner_hashes.add(sha256(path.parent / "models" / entries[0]["artifact"]["path"].split("/")[-1]) if False else report.get("runner_version"))
        config_hashes.add(report.get("frozen_config", {}).get("sha256", "missing"))
        found[key] = {"path": path, "report": report}
    missing = expected_keys().difference(found)
    if missing or len(found) != 72:
        raise RuntimeError(f"STOP: incomplete high-N matrix: found={len(found)}, missing={sorted(missing)}")
    if config_hashes != {sha256(Path(frozen["_path"]))}:
        raise RuntimeError(f"STOP: report frozen-config hash mismatch: {config_hashes}")
    return list(found.values()), {"input_block_count": len(found), "artifact_count": artifacts if verify_artifacts else None, "artifacts_verified": verify_artifacts, "config_hash": next(iter(config_hashes))}


def block_rows(blocks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    output, action_output = [], []
    for item in blocks:
        report = item["report"]
        row = {"n_sequences": int(report["n_sequences"]), "scenario": report["scenario"], "condition": report["condition"], "split_seed": int(report["split_seed"]), "source": str(item["path"])}
        per_action: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for entry in report["per_run"]:
            by_model[entry["model"]].append(entry)
            for action, metrics in entry["metrics"].get("primary_target_per_action", {}).items():
                if metrics.get("n_cells", 0) > 0:
                    per_action[(entry["model"], action)].append(metrics)
        for model in MODELS:
            entries = by_model[model]
            row[model] = {"metrics": {metric: mean([float(entry["metrics"]["primary_target_cells"][metric]) for entry in entries]) for metric in METRICS}, "selection_nll": mean([float(entry["best_selection_nll"]) for entry in entries]), "selected_profile_counts": dict(sorted(Counter(str(entry["selected_profile"]) for entry in entries).items()))}
        row["delta_channel_minus_ar"] = {metric: row[MODELS[1]]["metrics"][metric] - row[MODELS[0]]["metrics"][metric] for metric in METRICS}
        output.append(row)
        for (model, action), entries in per_action.items():
            n_cells = {int(entry["n_cells"]) for entry in entries}
            if len(entries) != 5 or len(n_cells) != 1:
                raise RuntimeError(f"STOP: per-action seed/cell coverage mismatch in {item['path']}: {model}, action={action}")
            action_row = {key: row[key] for key in ("n_sequences", "scenario", "condition", "split_seed")}
            action_row.update({"model": model, "action": action, "n_cells": next(iter(n_cells)), "metrics": {metric: mean([float(entry[metric]) for entry in entries]) for metric in METRICS}})
            action_output.append(action_row)
    return output, action_output


def grouped_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for n in N_GRID:
        for condition in CONDITIONS:
            for scenario in SCENARIOS:
                subset = [row for row in rows if row["n_sequences"] == n and row["condition"] == condition and row["scenario"] == scenario]
                if len(subset) != 4:
                    raise RuntimeError(f"STOP: expected four outer splits for N={n}, {scenario}, {condition}")
                delta = {metric: summary([row["delta_channel_minus_ar"][metric] for row in subset]) for metric in METRICS}
                models = {model: {"metrics": {metric: summary([row[model]["metrics"][metric] for row in subset]) for metric in METRICS}, "selection_nll": summary([row[model]["selection_nll"] for row in subset]), "selected_profile_counts": dict(sorted(Counter(profile for row in subset for profile, count in row[model]["selected_profile_counts"].items() for _ in range(count)).items()))} for model in MODELS}
                summaries.append({"n_sequences": n, "condition": condition, "scenario": scenario, "split_count": 4, "delta_channel_minus_ar": delta, "models": models})
    return summaries


def trend_audit(summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for condition in CONDITIONS:
        for scenario in SCENARIOS:
            for metric, direction in METRICS.items():
                sequence = []
                for n in N_GRID:
                    item = next(row for row in summaries if row["n_sequences"] == n and row["condition"] == condition and row["scenario"] == scenario)
                    delta = item["delta_channel_minus_ar"][metric]["mean"]
                    aligned = -delta if direction == "lower" else delta
                    sequence.append({"n_sequences": n, "channel_minus_ar": delta, "direction_aligned_improvement": aligned})
                aligned_values = [item["direction_aligned_improvement"] for item in sequence]
                out.append({"condition": condition, "scenario": scenario, "metric": metric, "direction": direction, "positive_means": "CHANNEL improves on AR", "n_sequence": sequence, "monotone_non_decreasing_aligned_mean": all(right >= left - EPS for left, right in zip(aligned_values, aligned_values[1:])), "endpoint_change_65536_minus_4096": aligned_values[-1] - aligned_values[0]})
    return out


def action_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for metric, value in row["metrics"].items():
            grouped[(row["n_sequences"], row["scenario"], row["condition"], row["model"], row["action"], metric)].append({"value": value, "n_cells": row["n_cells"]})
    out = []
    for (n, scenario, condition, model, action, metric), items in sorted(grouped.items()):
        values = [item["value"] for item in items]
        out.append({"n_sequences": n, "scenario": scenario, "condition": condition, "model": model, "action": action, "metric": metric, "direction": METRICS[metric], "n_outer_splits": len(items), "n_cells_by_split": [item["n_cells"] for item in items], "summary": summary(values)})
    return out


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def markdown(report: dict[str, Any]) -> str:
    lines = ["# Fresh high-N scaling aggregate", "", "- Outer evidence unit: scenario x condition x fresh split; five training seeds are averaged within each block.", "- Positive CHANNEL improvement means lower TV/KL and higher agreement than AR.", "- The N levels are nested prefixes, so their trend is descriptive scaling evidence rather than independent replication.", "", "## Paired split summaries", "", "| N | condition | scenario | improvement TV | SD | improvement KL | SD | improvement agreement | SD |", "|---:|---|---|---:|---:|---:|---:|---:|---:|"]
    for item in report["summaries"]:
        delta = item["delta_channel_minus_ar"]
        tv, kl, match = -delta["mean_candidate_tv"]["mean"], -delta["mean_excess_kl"]["mean"], delta["candidate_argmax_agreement"]["mean"]
        tv_sd, kl_sd, match_sd = delta["mean_candidate_tv"]["sample_sd"], delta["mean_excess_kl"]["sample_sd"], delta["candidate_argmax_agreement"]["sample_sd"]
        lines.append(f"| {item['n_sequences']} | {item['condition']} | {item['scenario']} | {tv:.6g} | {tv_sd:.6g} | {kl:.6g} | {kl_sd:.6g} | {match:.6g} | {match_sd:.6g} |")
    lines += ["", "## Trend audit", "", "`monotone_non_decreasing_aligned_mean=true` means the split-mean improvement did not decline from 4096 to 16384 to 65536; it is not a statistical significance claim.", "", "| condition | scenario | metric | monotone improvement | endpoint change |", "|---|---|---|---|---:|"]
    for row in report["trend_audit"]:
        lines.append(f"| {row['condition']} | {row['scenario']} | {row['metric']} | {row['monotone_non_decreasing_aligned_mean']} | {row['endpoint_change_65536_minus_4096']:.6g} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--frozen-config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--verify-artifacts", action="store_true")
    args = parser.parse_args()
    frozen_path = args.frozen_config.resolve()
    frozen = validate_config(frozen_path)
    frozen["_path"] = str(frozen_path)
    blocks, metadata = validate_and_load(args.input.resolve(), frozen, args.verify_artifacts)
    block_summary, block_actions = block_rows(blocks)
    summaries = grouped_summaries(block_summary)
    report = {"schema_version": VERSION, "status": "PASS", "metadata": {**metadata, "input_dir": str(args.input.resolve()), "frozen_config": str(frozen_path), "frozen_config_sha256": sha256(frozen_path), "outer_unit": "scenario_x_condition_x_split", "outer_unit_count_per_N_scenario_condition": 4}, "research_protocol": {"pipeline_eligible": True, "predictive_eligible": True, "causal_eligible": False, "aggregation": "five training seeds are averaged within each outer block before four-split summaries", "non_claims": frozen["non_claims"]}, "block_rows": block_summary, "summaries": summaries, "trend_audit": trend_audit(summaries), "per_action_summaries": action_summaries(block_actions)}
    output = args.output_dir.resolve()
    if output.exists() and any(output.iterdir()):
        raise RuntimeError(f"STOP: refusing to overwrite non-empty output: {output}")
    output.mkdir(parents=True, exist_ok=True)
    (output / "z3_high_n_scaling_aggregate.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "z3_high_n_scaling_aggregate.md").write_text(markdown(report), encoding="utf-8")
    csv_rows = []
    for row in report["per_action_summaries"]:
        values = row["summary"]
        csv_rows.append({"n_sequences": row["n_sequences"], "scenario": row["scenario"], "condition": row["condition"], "model": row["model"], "action": row["action"], "metric": row["metric"], "direction": row["direction"], "n_outer_splits": row["n_outer_splits"], "mean": values["mean"], "sample_sd": values["sample_sd"], "min": values["min"], "max": values["max"]})
    write_csv(output / "z3_high_n_scaling_per_action.csv", csv_rows, ["n_sequences", "scenario", "condition", "model", "action", "metric", "direction", "n_outer_splits", "mean", "sample_sd", "min", "max"])
    print(json.dumps({"status": "PASS", "input_blocks": len(blocks), "output": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
