import csv
import sqlite3
import argparse

from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("SQLs", nargs="+")
    parser.add_argument(
        "-d", "--database",
        help="name of the database",
        metavar="Database", default="W:/EDDN/ED_Galaxy.db",
    )
    parser.add_argument(
        "-o", "--output",
        help="name of the output directory",
        default="data"
    )
    return parser.parse_args()

def main():
    args = parse_args()

    db_filepath = Path(args.database)
    if not db_filepath.is_file():
        print(f" DB: {db_filepath} not found")
        return

    out_dir_path = Path(args.output)
    if not out_dir_path.is_dir():
        print(f"OUT: {out_dir_path} not found")
        return

    # open database
    conn = sqlite3.connect(db_filepath)
    conn.row_factory = sqlite3.Row

    for sql_filename_path in map(Path, args.SQLs):
        out_file_path = Path(out_dir_path, f"{sql_filename_path.stem}.csv")
        print(f"generating: {out_file_path}")
        with out_file_path.open("w", encoding="UTF-8", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            sql_stmt = sql_filename_path.read_text()
            write_header = True
            for row in conn.execute(sql_stmt):
                if write_header:
                    csv_writer.writerow(row.keys())
                    write_header = False
                csv_writer.writerow(row)

    conn.close()

if __name__ == "__main__":
    main()
