"""
Compare scenario run JSONs and produce an interactive HTML report.

Each input file must be the output of `python scenario.py <scenario> --json`.

Usage:
    python compare.py run1.json run2.json ... [--output comparison.html]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def load_run(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def damage_guarantee_curve(damages: list[int]) -> tuple[list[int], list[float]]:
    """Return (sorted_unique_damages, P(total >= damage)) step function data."""
    if not damages:
        return [], []
    sorted_dmg = sorted(damages)
    n = len(sorted_dmg)
    xs: list[int] = []
    ys: list[float] = []
    for i, d in enumerate(sorted_dmg):
        xs.append(d)
        ys.append((n - i) / n)
    return xs, ys


def build_figure(runs: list[dict]) -> go.Figure:
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2"]

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Distribution des dégâts totaux", "Garantie de dégâts — P(total ≥ X)"),
        vertical_spacing=0.15,
    )

    for i, run in enumerate(runs):
        color = colors[i % len(colors)]
        damages = run["total_damages"]
        summary = run["total_summary"]
        name = run["name"]
        legend_label = (
            f"{name} — min={summary['min']:.0f} "
            f"med={summary['median']:.0f} avg={summary['avg']:.0f} max={summary['max']:.0f}"
        )

        fig.add_trace(
            go.Histogram(
                x=damages,
                name=legend_label,
                marker_color=color,
                nbinsx=40,
                histnorm="probability",
                legendgroup=name,
                showlegend=True,
                hovertemplate=f"<b>{name}</b><br>dégâts=%{{x}}<br>proba=%{{y:.1%}}<extra></extra>",
            ),
            row=1, col=1,
        )

        xs, ys = damage_guarantee_curve(damages)
        fig.add_trace(
            go.Scatter(
                x=xs, y=ys,
                mode="lines",
                name=legend_label,
                line=dict(color=color, shape="hv", width=2),
                legendgroup=name,
                showlegend=False,
                hovertemplate=f"<b>{name}</b><br>X=%{{x}}<br>P(total ≥ X)=%{{y:.1%}}<extra></extra>",
            ),
            row=2, col=1,
        )

    fig.update_layout(
        barmode="group",
        title="Comparaison de scénarios",
        height=800,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(title_text="Dégâts totaux", row=1, col=1)
    fig.update_yaxes(title_text="Probabilité", tickformat=".0%", row=1, col=1)
    fig.update_xaxes(title_text="Seuil X", row=2, col=1)
    fig.update_yaxes(title_text="Probabilité (total ≥ X)", tickformat=".0%", row=2, col=1)
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare scenario run JSONs (from `scenario.py --json`)")
    parser.add_argument("runs", nargs="+", help="Paths to run JSON files (2+ recommended)")
    parser.add_argument("-o", "--output", default="comparison.html", help="Output HTML file (default: comparison.html)")
    args = parser.parse_args()

    runs = [load_run(p) for p in args.runs]
    if not runs:
        print("No runs loaded", file=sys.stderr)
        sys.exit(1)

    fig = build_figure(runs)
    output_path = Path(args.output)
    fig.write_html(str(output_path), include_plotlyjs="cdn")
    print(f"Wrote {output_path.resolve()}")


if __name__ == "__main__":
    main()
