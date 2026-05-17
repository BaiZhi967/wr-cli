import csv
import json
import os
import sys


def _collect_keys(rows):
    keys = []
    seen = set()
    for row in rows:
        for k in row:
            if k not in seen:
                keys.append(k)
                seen.add(k)
    return keys


def _flatten_value(v):
    if isinstance(v, (list, tuple)):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False)
    return v


def _write_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _write_delimited(data, path, delimiter=","):
    if not data:
        open(path, "w").close()
        return
    keys = _collect_keys(data)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys, delimiter=delimiter,
                                quoting=csv.QUOTE_ALL, extrasaction="ignore")
        writer.writeheader()
        for row in data:
            flat = {k: _flatten_value(v) for k, v in row.items()}
            writer.writerow(flat)


def _write_markdown_table(data, path):
    if not data:
        open(path, "w").close()
        return
    keys = _collect_keys(data)
    lines = []
    lines.append("| " + " | ".join(keys) + " |")
    lines.append("| " + " | ".join("---" for _ in keys) + " |")
    for row in data:
        vals = [str(_flatten_value(row.get(k, ""))).replace("|", "\\|") for k in keys]
        lines.append("| " + " | ".join(vals) + " |")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _write_txt(data, path):
    with open(path, "w", encoding="utf-8") as f:
        for i, row in enumerate(data):
            if i > 0:
                f.write("\n")
            for k, v in row.items():
                f.write(f"{k}: {_flatten_value(v)}\n")
            f.write("---\n")


def write_output(data, path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        _write_json(data, path)
    elif ext == ".csv":
        _write_delimited(data, path, delimiter=",")
    elif ext == ".tsv":
        _write_delimited(data, path, delimiter="\t")
    elif ext in (".md", ".markdown"):
        _write_markdown_table(data, path)
    elif ext == ".txt":
        _write_txt(data, path)
    else:
        print(f"错误: 不支持的导出格式 '{ext}'，支持 .json .csv .tsv .md .txt", file=sys.stderr)
        sys.exit(1)
