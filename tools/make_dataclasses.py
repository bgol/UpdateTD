#!/usr/bin/env python

import time
import sqlite3
import keyword
import argparse

from pathlib import Path

DB_STANDARD_BASENAME = "TradeDangerous"
DB_STANDARD_SUFFIX = ".db"
STANDARD_OUTPUTFILE = "tables.py"

DEFAULT_FACTORIES = {"CURRENT_TIME", "CURRENT_DATE", "CURRENT_TIMESTAMP"}

def print_dataclass(conn, db_basename, table_name, out_file):
    curs = conn.cursor()

    need_default = False
    out_file.write("\n")
    out_file.write("@dataclass(frozen=True)\n")
    out_file.write(f"class {table_name}:\n")
    out_file.write(f'    """{db_basename} "{table_name}" table"""\n')
    for col_row in curs.execute(f"PRAGMA table_xinfo('{table_name}')"):
        out_file.write(f"    {col_row['name']}")
        if keyword.iskeyword(col_row["name"]):
             out_file.write("_")
        if not col_row["type"]:
            out_type = "bytes"
        elif "INT" in col_row["type"].upper():
            out_type = "int"
        elif any(x in col_row["type"].upper() for x in ("CHAR", "CLOB", "TEXT")):
            out_type = "str"
        elif "BLOB" in col_row["type"].upper():
            out_type = "bytes"
        elif any(x in col_row["type"].upper() for x in ("REAL", "FLOA", "DOUB")):
            out_type = "float"
        else:
            out_type = "str"
        out_file.write(f": {out_type}")
        if col_row["dflt_value"] is not None:
            if col_row["dflt_value"] in DEFAULT_FACTORIES:
                out_file.write(f" = field(default_factory = {col_row['dflt_value']})")
            else:
                out_file.write(f" = {col_row['dflt_value']}")
            need_default = True
        elif need_default or not (col_row["notnull"] or col_row["pk"]):
            out_file.write(" = None")
            need_default = True
        out_file.write("\n")

    curs.close()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--database",
        help="name of the database",
        metavar="Database", default=DB_STANDARD_BASENAME,
    )
    parser.add_argument(
        "-o", "--output",
        help="name of the output file",
        default=STANDARD_OUTPUTFILE
    )
    return parser.parse_args()

def main():
    args = parse_args()

    db_filepath = Path(args.database)
    if db_filepath.is_dir():
        db_filepath /= f"{DB_STANDARD_BASENAME}{DB_STANDARD_SUFFIX}"
    if not db_filepath.suffix:
        db_filepath = db_filepath.with_suffix(DB_STANDARD_SUFFIX)
    if not db_filepath.is_file():
        print(f" DB: {db_filepath} not found")
        return
    db_basename = db_filepath.stem
    out_path = Path(args.output)
    if out_path.is_dir():
        out_path /= STANDARD_OUTPUTFILE

    # open database
    conn = sqlite3.connect(db_filepath)
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()

    print(f"generating: {out_path}")
    with out_path.open("w") as out_file:
        stmt = (
            "SELECT m.name"
             " FROM sqlite_master AS m"
            " WHERE m.type = 'table'"
              " AND m.name NOT LIKE 'sqlite_%'"
            " ORDER BY 1"
        )
        gen_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        out_file.write('"""\n')
        out_file.write(f"   auto generated on {gen_time}\n")
        out_file.write(f"   database file: {db_filepath}\n")
        out_file.write('"""\n')

        out_file.write("""
from dataclasses import dataclass, field
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).replace(microsecond = 0)

def CURRENT_TIME():
    return now().time().isoformat()

def CURRENT_DATE():
    return now().date().isoformat()

def CURRENT_TIMESTAMP():
    return now().isoformat(sep = " ")

""")

        for row in curs.execute(stmt):
            print(f"generating: {db_basename}.{row['name']}")
            print_dataclass(conn, db_basename, row["name"], out_file)

    curs.close()
    conn.close()

if __name__ == "__main__":
    main()
