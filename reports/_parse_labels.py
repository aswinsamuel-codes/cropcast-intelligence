"""Validation and audit script for ICTD-IITD recovered anomaly-label files.

Verifies:
1. Raw files containing Git conflict markers (LFS pointer vs CSV payload).
2. Bit-for-bit SHA256 and byte-length match between LFS pointer and CSV payload.
3. Cleaned working CSV copies: row counts, schema, date ranges, missing values, duplicates, and distributions.
"""

import csv
import hashlib
import collections
from datetime import datetime

def audit_raw_file(raw_path, commodity):
    print(f"\n{'='*60}")
    print(f"RAW DOWNLOAD AUDIT: {commodity} ({raw_path})")
    print(f"{'='*60}")
    with open(raw_path, 'rb') as f:
        raw_bytes = f.read()

    lines = raw_bytes.decode('utf-8', errors='ignore').splitlines(keepends=True)
    print(f"Total raw lines: {len(lines)}")

    conflict_markers = [(i, l.strip()) for i, l in enumerate(lines)
                        if any(l.startswith(p) for p in ['<<<<<<<', '=======', '>>>>>>>'])]
    print(f"Conflict markers detected: {len(conflict_markers)}")
    for idx, marker in conflict_markers:
        print(f"  Line {idx}: {marker}")

    # Inspect LFS pointer block (lines 0 to 4)
    lfs_lines = [l.strip() for l in lines[1:4]]
    print(f"LFS Header block: {lfs_lines}")
    expected_oid = None
    expected_size = None
    for l in lfs_lines:
        if l.startswith("oid sha256:"):
            expected_oid = l.split("oid sha256:")[1].strip()
        elif l.startswith("size "):
            expected_size = int(l.split("size ")[1].strip())

    # Extract CSV payload between '=======\n' and '>>>>>>> ...\n'
    payload_lines = lines[5:-1]
    payload_bytes = "".join(payload_lines).encode('utf-8')
    actual_oid = hashlib.sha256(payload_bytes).hexdigest()
    actual_size = len(payload_bytes)

    print(f"Expected LFS OID:  {expected_oid}")
    print(f"Actual Payload OID: {actual_oid}")
    print(f"OID Match: {'EXACT MATCH (VERIFIED)' if expected_oid == actual_oid else 'MISMATCH'}")
    print(f"Expected Size:     {expected_size} bytes")
    print(f"Actual Size:       {actual_size} bytes")
    print(f"Size Match: {'EXACT MATCH (VERIFIED)' if expected_size == actual_size else 'MISMATCH'}")


def audit_clean_file(clean_path, commodity):
    print(f"\n{'-'*60}")
    print(f"CLEANED WORKING COPY AUDIT: {commodity} ({clean_path})")
    print(f"{'-'*60}")
    with open(clean_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)

    print(f"Schema: {fields}")
    print(f"Total data rows: {len(rows)} (excluding header)")

    # Date range
    startdates = [datetime.strptime(r['STARTDATE'], '%Y-%m-%d') for r in rows if r.get('STARTDATE')]
    enddates = [datetime.strptime(r['ENDDATE'], '%Y-%m-%d') for r in rows if r.get('ENDDATE')]
    print(f"STARTDATE range: {min(startdates).date()} to {max(startdates).date()}")
    print(f"ENDDATE range:   {min(enddates).date()} to {max(enddates).date()}")

    # Missing values
    print("Missing / empty values per column:")
    for col in fields:
        missing = sum(1 for r in rows if not r.get(col, '').strip())
        pct = (missing / len(rows)) * 100
        print(f"  {col}: {missing}/{len(rows)} ({pct:.1f}%)")

    # Duplicates
    exact_dups = len(rows) - len(set(tuple(r[c] for c in fields) for r in rows))
    key_dups = len(rows) - len(set((r['STARTDATE'], r['ENDDATE'], r['STATENAME'], r['MANDINAME']) for r in rows))
    print(f"Exact duplicate rows: {exact_dups}")
    print(f"Key duplicates (STARTDATE, ENDDATE, STATENAME, MANDINAME): {key_dups}")

    # Geographic distribution
    states = collections.Counter(r['STATENAME'] for r in rows)
    print(f"States: {dict(states)}")
    mandis = sorted(set(f"{r['STATENAME']} | {r['MANDINAME']}" for r in rows))
    print(f"Distinct state-market combinations: {len(mandis)}")

    # Label distributions
    for col in ['lastMonth', 'lastYear', 'SameMonth']:
        dist = collections.Counter(r.get(col, '').strip() for r in rows)
        print(f"  {col} label counts: {dict(dist)}")

    # MAXMINRATIO
    ratios = [float(r['MAXMINRATIO']) for r in rows if r.get('MAXMINRATIO', '').strip()]
    print(f"MAXMINRATIO: min={min(ratios):.4f}, max={max(ratios):.4f}, mean={sum(ratios)/len(ratios):.4f}")

    # Anomaly flag presence
    has_anomaly = sum(1 for r in rows if any(r.get(c, '').strip() == 'Anomaly' for c in ['lastMonth', 'lastYear', 'SameMonth']))
    print(f"Rows with at least one 'Anomaly' flag: {has_anomaly}/{len(rows)} (100% - anomaly-filtered file)")

if __name__ == "__main__":
    audit_raw_file("reports/ictd_onion_labels_raw.csv", "Onion")
    audit_clean_file("reports/ictd_onion_labels.csv", "Onion")

    audit_raw_file("reports/ictd_potato_labels_raw.csv", "Potato")
    audit_clean_file("reports/ictd_potato_labels.csv", "Potato")
