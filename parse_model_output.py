"""parse_model_output.py
Parses 1costingFE model_output.txt and writes data.json for the
fusion-tea-walkthrough-visualization GitHub Pages site.

Usage:
    python parse_model_output.py model_output.txt         # writes data.json
    python parse_model_output.py model_output.txt out.json
"""
import re, json, sys
from datetime import datetime, timezone
from pathlib import Path

def parse(text: str) -> dict:
    d = {}

    # Top-level LCOE / overnight
    m = re.search(r"LCOE:\s*([\d.]+)\s*\$/MWh\s*\(1 GWe NOAK", text)
    d["lcoe_1gw"] = float(m.group(1)) if m else None

    m = re.search(r"Native LCOE\s*=\s*([\d.]+)\s*\$/MWh", text)
    d["lcoe_native"] = float(m.group(1)) if m else None

    m = re.search(r"Overnight:.*?1 GWe\s+([\d.]+)\s*\$/kW", text)
    d["overnight_1gw"] = float(m.group(1)) if m else None

    m = re.search(r"Overnight: generic\s+([\d.]+)", text)
    d["overnight_native"] = float(m.group(1)) if m else None

    # CAS top-level table (1 GWe column)
    cas_top = {}
    for line in text.splitlines():
        m = re.match(r"^(CAS\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", line.strip())
        if m:
            cas_top[m.group(1)] = {
                "generic": float(m.group(2)),
                "native":  float(m.group(3)),
                "gw1":     float(m.group(4)),
            }
    d["cas_top"] = cas_top

    # CAS22 sub-accounts (1 GWe column)
    cas22 = {}
    in_block = False
    for line in text.splitlines():
        if "CAS22 sub-account" in line:
            in_block = True
            continue
        if not in_block:
            continue
        m = re.match(r"^(C22\w+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", line.strip())
        if m:
            cas22[m.group(1)] = {
                "generic": float(m.group(2)),
                "native":  float(m.group(3)),
                "gw1":     float(m.group(4)),
            }
    d["cas22"] = cas22

    # Sensitivity sweeps
    # p_input sweep
    p_input_sweep = []
    for m in re.finditer(r"p_input=([\d.]+)\s*MW:\s*LCOE=([\d.]+)", text):
        p_input_sweep.append({"p_input": float(m.group(1)), "lcoe": float(m.group(2))})
    d["p_input_sweep"] = p_input_sweep

    # elon sweep
    elon_sweep = []
    for m in re.finditer(r"elon=([\d.]+):\s*LCOE=([\d.]+)", text):
        elon_sweep.append({"elon": float(m.group(1)), "lcoe": float(m.group(2))})
    d["elon_sweep"] = elon_sweep

    # Metadata
    d["parsed_at"] = datetime.now(timezone.utc).isoformat()
    d["source"] = "1cFE/fusion-tea - 21-spherical-tokamak-hts/model_output.txt"

    return d


if __name__ == "__main__":
    src  = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("model_output.txt")
    dest = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data.json")
    text = src.read_text(encoding="utf-8", errors="replace")
    out  = parse(text)
    dest.write_text(json.dumps(out, indent=2))
    print(f"Wrote {dest}  (LCOE={out['lcoe_1gw']} $/MWh, OC={out['overnight_1gw']} $/kW)")
