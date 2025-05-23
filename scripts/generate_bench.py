import re
from pathlib import Path

SOURCE_DIR = "synth-data"
FILE_FORMATS = ["parquet", "vortex", "fastlanes"]
FILE_FORMAT_SOURCE_DIRS = {
    "fastlanes": Path(f"{SOURCE_DIR}/fls"),
    "parquet": Path(f"{SOURCE_DIR}/parquet"),
    "vortex": Path(f"{SOURCE_DIR}/vortex"),
}
FILE_FORMAT_EXT_NAMES = {
    "fastlanes": "fast_lanes",
    "parquet": "parquet",
    "vortex": "vortex",
}
FILE_FORMAT_COLUMN_FORMAT = {"fastlanes": "COLUMN_", "parquet": "col", "vortex": "col"}
BENCH_ROOT = Path("benchmark")
TEMPLATE = """# name: {benchmark_path}
# description: Run query {name}
# group: [{group}]

require {group}

load
CREATE VIEW {group}_table AS SELECT * FROM {read_fn}("{source_path}");

run
{query}
"""

OPERATIONS = [["SUM", "AVG", "MIN", "MAX"]]


def parse_name(name):
    pattern = re.compile(
        r"""^data-
        (?P<n_rows>\d+)-
        (?P<n_cols>\d+)-
        (?P<type>[^-]+)-
        (?P<parameter>[0-9]+(?:\.[0-9]+)?)
        \.(?P<extension>[A-Za-z0-9]+)$
    """,
        re.VERBOSE,
    )
    m = pattern.match(name)
    if not m:
        raise ValueError(f"Filename {name!r} does not match expected pattern")
    gd = m.groupdict()
    return {
        "n_rows": int(gd["n_rows"]),
        "n_cols": int(gd["n_cols"]),
        "type": gd["type"],
        "parameter": float(gd["parameter"]),
        "extension": gd["extension"],
    }


def main():
    for fformat in FILE_FORMATS:
        src_dir = FILE_FORMAT_SOURCE_DIRS[fformat]

        group = FILE_FORMAT_EXT_NAMES[fformat]
        read_fn = f"read_{src_dir.name}"
        dst_dir = BENCH_ROOT / src_dir.name
        dst_dir.mkdir(parents=True, exist_ok=True)

        for src_file in src_dir.iterdir():
            if not src_file.is_file():
                continue
            name = src_file.stem

            stats = parse_name(name)

            cols = []
            if stats["n_cols"] > 1:
                cols = [1, stats["n_cols"]]
            else:
                cols = [1]

            for max_col in cols:
                for oprs in OPERATIONS:
                    benchmark_filename = (
                        f"{name}-{','.join(oprs).lower()}-{max_col}.benchmark"
                    )
                    benchmark_path = dst_dir / benchmark_filename

                    operation = ",".join(
                        [
                            ",".join(
                                [
                                    "{opr}({column_name})".format(
                                        opr=opr,
                                        column_name=f"{FILE_FORMAT_COLUMN_FORMAT[fformat]}{column_id}",
                                    )
                                    for opr in oprs
                                ]
                            )
                            for column_id in range(0, max_col)
                        ]
                    )
                    query = "SELECT {operation} FROM {group}_table;".format(
                        operation=operation, group=group
                    )

                    content = TEMPLATE.format(
                        benchmark_path=benchmark_path.as_posix(),
                        name=name,
                        group=group,
                        read_fn=read_fn,
                        source_path=src_file.as_posix(),
                        query=query,
                    )

                    with open(benchmark_path, "w") as f:
                        f.write(content)
                    print(f"Written {benchmark_path}")


if __name__ == "__main__":
    main()
