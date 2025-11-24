#!/usr/bin/env python3

import os
import sys
import pandas as pd

COL_PROG     = "Programme recommended (Y/N)"
COL_LOC      = "Location (Johanneberg/Lindholmen/online)"
COL_FMT      = "Teaching format (lectures / proj)"
COL_HARD     = "Hardness (1–5)"
COL_WORK     = "Workload (1–5)"
COL_INTEREST = "Interest / fun (1–5)"
COL_USEFUL   = "Usefulness for career (1–5)"
COL_ALIGN    = "Alignment with SE master (1–5)"
COL_EXAM     = "Exam type (written / proj / mixed)"
COL_GROUP    = "Group work level (1–5)"


def clip01(x: float) -> float:
    """Clamp value to [0, 1]."""
    return max(0.0, min(1.0, x))


def util_prog(y_or_n):
    """Programme recommended (Y/N)."""
    text = str(y_or_n).strip().upper()
    if text == "Y":
        return 1.0
    if text == "N":
        return 0.6
    return 0.6


def util_location(loc):
    """Location (Lindholmen/Johanneberg/online)."""
    loc_s = str(loc).strip()
    if loc_s == "Lindholmen":
        return 1.0
    if loc_s == "Johanneberg":
        return 0.8
    if loc_s.lower() == "online":
        return 0.9
    return 0.9


def util_format(fmt):
    """Teaching format (lectures / proj / both)."""
    fmt_s = str(fmt).strip().lower()
    if "lecture" in fmt_s:
        return 1.0
    if "project" in fmt_s and "lecture" not in fmt_s:
        return 0.9
    if "both" in fmt_s or "bth" in fmt_s or "mixed" in fmt_s:
        return 0.85
    return 0.9


def util_exam(exam):
    """Exam type (written / proj / mixed)."""
    exam_s = str(exam).strip().lower()
    if "proj" in exam_s:
        return 1.0
    if "mix" in exam_s or "both" in exam_s:
        return 0.8
    if "written" in exam_s:
        return 0.7
    return 0.8


def util_cost(v):
    """
    Lower is better (Hardness, Workload).
    Maps 1..5 → 1..0 linearly.
    """
    try:
        x = float(v)
    except Exception:
        return 0.5
    u = (5.0 - x) / 4.0   
    return clip01(u)


def util_benefit(v):
    """
    Higher is better (Interest, Usefulness, Alignment).
    Maps 1..5 → 0..1 linearly.
    """
    try:
        x = float(v)
    except Exception:
        return 0.5
    u = (x - 1.0) / 4.0   
    return clip01(u)


def util_group(v):
    """
    Group work level, best around 3.
    3 → 1.0, 2/4 → 0.5, 1/5 → 0.0.
    """
    try:
        x = float(v)
    except Exception:
        return 0.5
    u = 1.0 - abs(x - 3.0) / 2.0
    return clip01(u)

w_prog     = 0.10   # Programme recommended
w_loc      = 0.05   # Location
w_fmt      = 0.05   # Teaching format
w_hard     = 0.10   # Hardness (lower better)
w_work     = 0.10   # Workload (lower better)
w_interest = 0.20   # Interest/fun
w_useful   = 0.20   # Usefulness for career
w_align    = 0.15   # Alignment with SE master
w_group    = 0.05   # Group work level
w_exam     = 0.00   # Exam type; set to >0 if you care about this


def compute_score(row):
    """Compute per-course utilities and final score."""
    u_prog   = util_prog(row.get(COL_PROG))
    u_loc    = util_location(row.get(COL_LOC))
    u_fmt    = util_format(row.get(COL_FMT))
    u_hard   = util_cost(row.get(COL_HARD))
    u_work   = util_cost(row.get(COL_WORK))
    u_inter  = util_benefit(row.get(COL_INTEREST))
    u_useful = util_benefit(row.get(COL_USEFUL))
    u_align  = util_benefit(row.get(COL_ALIGN))
    u_group  = util_group(row.get(COL_GROUP))
    u_exam   = util_exam(row.get(COL_EXAM))

    score = 100.0 * (
        w_prog     * u_prog   +
        w_loc      * u_loc    +
        w_fmt      * u_fmt    +
        w_hard     * u_hard   +
        w_work     * u_work   +
        w_interest * u_inter  +
        w_useful   * u_useful +
        w_align    * u_align  +
        w_group    * u_group  +
        w_exam     * u_exam
    )

    return {
        "u_prog": u_prog,
        "u_loc": u_loc,
        "u_fmt": u_fmt,
        "u_hard": u_hard,
        "u_work": u_work,
        "u_interest": u_inter,
        "u_useful": u_useful,
        "u_align": u_align,
        "u_group": u_group,
        "u_exam": u_exam,
        "Score": score,
    }


def main():
    csv_path = input("Enter path to your courses CSV (e.g. courses.csv): ").strip()
    if not csv_path:
        print("No path given, exiting.")
        sys.exit(1)

    if not os.path.isfile(csv_path):
        print(f"File not found: {csv_path}")
        sys.exit(1)

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)


    scores_df = df.apply(compute_score, axis=1, result_type="expand")
    df_out = pd.concat([df, scores_df], axis=1)

    # Sort
    df_out = df_out.sort_values("Score", ascending=False)

    base, ext = os.path.splitext(csv_path)
    out_path = base + "_scored" + (ext if ext else ".csv")

    try:
        df_out.to_csv(out_path, index=False)
    except Exception as e:
        print(f"Error writing output CSV: {e}")
        sys.exit(1)

    print(f"\nScored courses written to: {out_path}\n")
    print("Top 5 courses by Score:")
    cols_to_show = [c for c in df.columns if "Course" in c or "code" in c or "name" in c]
    cols_to_show = cols_to_show[:2] + ["Score"] 
    try:
        print(df_out[cols_to_show].head(5).to_string(index=False))
    except Exception:
        print(df_out[["Score"]].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
