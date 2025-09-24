#!/usr/bin/env python3
"""
plot_eeg_ecg.py
Scrollable multichannel EEG + ECG plot for QUASAR assignment.

Usage:
    python plot_eeg_ecg.py --input "EEG and ECG data_02_raw.csv" --output quasar_eeg_ecg.html
"""

import argparse
import io
import re
from typing import List

import numpy as np
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# EEG channel names from assignment
EEG_NAMES = [
    "Fz","Cz","P3","C3","F3","F4","C4","P4","Fp1","Fp2",
    "T3","T4","T5","T6","O1","O2","F7","F8","A1","A2","Pz"
]

def read_csv_skip_comments(path: str) -> pd.DataFrame:
    """Read CSV but skip lines starting with # so first non-comment row is header."""
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [line for line in f if not line.lstrip().startswith('#')]
    return pd.read_csv(io.StringIO(''.join(lines)))

def find_time_col(df: pd.DataFrame) -> str:
    for c in df.columns:
        if 'time' in c.lower():
            return c
    return df.columns[0]  # fallback

def find_eeg_cols(df: pd.DataFrame) -> List[str]:
    found = []
    for name in EEG_NAMES:
        for c in df.columns:
            if re.search(r'\b' + re.escape(name) + r'\b', c, flags=re.I):
                found.append(c)
    return list(dict.fromkeys(found))

def find_ecg_cols(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if re.search(r'\b(x1|x2|leog|reog)\b', c, flags=re.I)]

def find_cm_cols(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if re.search(r'\bcm\b|common[_ ]?mode', c, flags=re.I)]

def find_ignore_cols(df: pd.DataFrame) -> List[str]:
    patterns = r'\b(x3|trigger|time_?offset|adc_?status|adc_?sequence|event|comments)\b'
    return [c for c in df.columns if re.search(patterns, c, flags=re.I)]

def main():
    p = argparse.ArgumentParser(description="Scrollable EEG+ECG plotter (Plotly)")
    p.add_argument("--input", "-i", required=True, help="Path to CSV")
    p.add_argument("--output", "-o", default="eeg_ecg_plot.html", help="Output HTML file")
    p.add_argument("--downsample", "-d", type=int, default=1, help="Downsample factor (1 = full data)")
    args = p.parse_args()

    print("Reading CSV (skipping '#' lines)...")
    df = read_csv_skip_comments(args.input)
    print(f"Columns: {list(df.columns)}")

    time_col = find_time_col(df)
    eeg_cols = [c for c in find_eeg_cols(df) if c not in find_ignore_cols(df)]
    ecg_cols = [c for c in find_ecg_cols(df) if c not in find_ignore_cols(df)]
    cm_cols  = [c for c in find_cm_cols(df)  if c not in find_ignore_cols(df)]

    # fallback for EEG if none found
    if not eeg_cols:
        numeric = df.select_dtypes(include=[np.number]).columns
        ignore  = set([time_col] + ecg_cols + cm_cols + find_ignore_cols(df))
        eeg_cols = [c for c in numeric if c not in ignore]

    print("Detected:")
    print("  Time:", time_col)
    print("  EEG:", eeg_cols)
    print("  ECG:", ecg_cols)
    print("  CM :", cm_cols)

    if args.downsample > 1:
        df = df.iloc[::args.downsample].reset_index(drop=True)
        print(f"Downsampled by factor {args.downsample}. New length: {len(df)}")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    eeg_idx, ecg_idx, cm_idx = [], [], []

    # EEG on primary y-axis (µV)
    for c in eeg_cols:
        fig.add_trace(
            go.Scatter(x=df[time_col], y=df[c], name=c, mode='lines'),
            secondary_y=False
        )
        eeg_idx.append(len(fig.data)-1)

    # ECG on secondary y-axis (converted to mV)
    for c in ecg_cols:
        y = pd.to_numeric(df[c], errors='coerce')
        fig.add_trace(
            go.Scatter(x=df[time_col], y=y/1000.0, name=f"{c} (mV)", mode='lines'),
            secondary_y=True
        )
        ecg_idx.append(len(fig.data)-1)

    # CM on secondary y-axis (also mV, dashed)
    for c in cm_cols:
        y = pd.to_numeric(df[c], errors='coerce')
        fig.add_trace(
            go.Scatter(x=df[time_col], y=y/1000.0,
                       name=f"{c} (mV, CM)", mode='lines',
                       line=dict(dash='dot')),
            secondary_y=True
        )
        cm_idx.append(len(fig.data)-1)

    if not fig.data:
        raise SystemExit("No plottable channels found.")

    fig.update_layout(
        title="EEG + ECG Multichannel Plot",
        height=700,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1)
    )
    fig.update_xaxes(title_text="Time (s)", rangeslider_visible=True)
    fig.update_yaxes(title_text="EEG (µV)", secondary_y=False)
    fig.update_yaxes(title_text="ECG / CM (mV)", secondary_y=True)

    # Buttons to toggle groups
    total = len(fig.data)
    all_vis   = [True] * total
    eeg_vis   = [i in eeg_idx for i in range(total)]
    ecgcm_vis = [i in ecg_idx + cm_idx for i in range(total)]
    none_vis  = [False] * total
    fig.update_layout(
        updatemenus=[dict(
            type="buttons",
            direction="right",
            x=0.01, y=1.1,
            buttons=[
                dict(label="All",        method="update", args=[{"visible": all_vis}]),
                dict(label="EEG only",   method="update", args=[{"visible": eeg_vis}]),
                dict(label="ECG+CM only",method="update", args=[{"visible": ecgcm_vis}]),
                dict(label="Hide all",   method="update", args=[{"visible": none_vis}]),
            ]
        )]
    )

    fig.write_html(args.output, include_plotlyjs="cdn")
    print(f"Interactive plot saved to {args.output}")

if __name__ == "__main__":
    main()

