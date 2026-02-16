#!/usr/bin/env python3
"""Generate text timeline reports for modified EHR FHIR bundles."""

import sys
import os
import glob

# Add parent directory to path so we can import the fhir_reader library
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "orchestrator"))

from fhir_reader import load_and_convert


def main():
    ehr_dir = os.path.dirname(os.path.abspath(__file__))
    json_files = sorted(glob.glob(os.path.join(ehr_dir, "mod_*.json")))

    if not json_files:
        print("No mod_*.json files found in", ehr_dir)
        sys.exit(1)

    for json_path in json_files:
        basename = os.path.splitext(os.path.basename(json_path))[0]
        out_path = os.path.join(ehr_dir, f"{basename}_report.txt")

        print(f"Converting {os.path.basename(json_path)} ...")
        timeline = load_and_convert(json_path)

        with open(out_path, "w") as f:
            f.write(timeline)

        print(f"  -> {os.path.basename(out_path)}")

    print("Done.")


if __name__ == "__main__":
    main()
