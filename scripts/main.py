import os
from enum import Enum
import json
import csv
import argparse
import shutil
import tempfile
from pathlib import Path
import pyfastlanes as fls

FILE_FORMAT_DIR = "synth-data"
FLS_DIR = "fls"
PARQUET_DIR = "parquet"
VORTEX_DIR = "vortex"


class ColumnType(Enum):
    INT64 = "FLS_I64"
    BIGINT = "FLS_I64"  # alias for INT64
    INT32 = "FLS_I32"
    INT16 = "FLS_I16"
    INT8 = "FLS_I08"
    UINT8 = "FLS_U08"
    DOUBLE = "FLS_DBL"
    double = "FLS_DBL"  # alias for DOUBLE
    FLS_STR = "FLS_STR"
    string = "FLS_STR"  # alias for FLS_STR
    STR = "STR"
    varchar = "STR"  # alias for STR
    VARCHAR = "STR"  # alias for STR
    LIST = "LIST"
    STRUCT = "STRUCT"
    map = "MAP"
    MAP = "MAP"


def filename_no_ext(path: str) -> str:
    base = os.path.basename(path)
    name, _ext = os.path.splitext(base)

    return name


def write_to_json_schema(types, file_path):
    """
    Generates a JSON schema file with the specified number of columns.
    The schema file contains a "columns" key with a list of column names.

    :param types: Types of the columns in the schema.
    :param file_path: Path to the JSON schema file.
    """
    schema = {
        "columns": [
            {"name": f"COLUMN_{i}", "type": col_type}
            for i, col_type in enumerate(types)
        ]
    }

    with open(file_path, mode="w") as schemafile:
        schemafile.write(json.dumps(schema))


def convert_fls(source_path: str, overwrite=False):
    target_filename = f"{filename_no_ext(source_path)}.fls"
    target_path = f"{FILE_FORMAT_DIR}/{FLS_DIR}/{target_filename}"

    if os.path.exists(target_path) and not overwrite:
        return

    # FIXME: read_csv requires a schema to be present at the directory.
    # We do some simple derivation to autogenerate the schema.
    src = Path(source_path)
    if not src.is_file():
        raise FileNotFoundError(f"No such file: {src}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        dst = tmp_dir / src.name
        # FIXME: FLS does not suport csv files with a header, also limited delimiter support.
        reader = csv.reader(src.open("r"))
        dst_file = dst.open("w", newline="")
        writer = csv.writer(dst_file, delimiter="|", lineterminator="\n")

        try:
            first_row = next(reader)
        except StopIteration:
            # Empty file—nothing to do
            return

        # If the row had a number, write it back; otherwise drop it
        for row in reader:
            writer.writerow(row)

        parts = src.stem.split("-")
        if len(parts) > 1:
            n_columns = int(parts[2])
            write_to_json_schema(
                [ColumnType.DOUBLE.value for _ in range(n_columns)],
                f"{tmp_dir}/schema.json",
            )
        else:
            print(f"Filename {src.name!r} doesn't have a part at index 1.")

        dst_file.flush()
        dst_file.close()
        conn = fls.Connection()

        # FIXME: Should also accept a full path with filename.
        conn.read_csv(tmp_dir.as_posix())
        conn.inline_footer().to_fls(target_path)

        # src_count = sum(1 for _ in csv.reader(src.open("r")))
        # tmp_count = sum(1 for _ in csv.reader(dst.open("r")))

        # if src_count != tmp_count:
        #    print(f"{src_count} - {tmp_count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="File format generator from CSV files."
    )
    parser.add_argument("path", help="Path to the source file.", type=str)
    parser.add_argument(
        "--overwrite", help="Overwrite existing file format.", type=bool
    )
    parser.add_argument(
        "--target_formats",
        help="The target format, supported: FastLanes",
        nargs="+",
        type=str,
    )

    args = parser.parse_args()

    if args.target_formats is None:
        convert_fls(args.path, args.overwrite)
    else:
        for format in args.target_formats:
            if format == "FastLanes":
                convert_fls(args.path, args.overwrite)
