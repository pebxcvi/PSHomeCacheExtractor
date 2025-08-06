import os
import re
import argparse

def read_object_query(file_path):
    object_query_data = {}
    with open(file_path, "r", encoding="utf-8") as file:
        headers = file.readline().strip().split("\t")

        for line in file:
            row = line.strip().split("\t")
            row_data = dict(zip(headers, row))
            if row_data.get("Ext", "").lower() == "sdat":
                uuid = row_data.get("UUID", "")
                if uuid:
                    object_query_data.setdefault(uuid, []).append({
                        "custom_file_name": row_data.get("Custom File Name", ""),
                        "sdat_version": row_data.get("SDAT Version", ""),
                        "object_version": row_data.get("Object Version", ""),
                    })
    return object_query_data

def process_log_file(log_file_path, object_query_data, output_file_path):
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        output_file.write(
            "Cache Name\tDAT Num\tSDAT Date\tProd(2) Folder\tLive(2) Folder\tUUID\tOrig File Name\tExtension\tSDATA Version\tUnique File Name\tnew_uuid\tnew_sdat\tcorrupt_sdat\thas_corrupt_sdat\thighest_object_version\n"
        )

        with open(log_file_path, "r", encoding="utf-8") as log_file:
            for line in log_file:
                log_row = line.strip().split("\t")
                if len(log_row) < 10:
                    continue

                sdat_version_field = log_row[8].strip().lower()
                if sdat_version_field in {"0", "n/a"}:
                    continue

                log_uuid = log_row[5]
                unique_file_name = log_row[9] + ".sdat"

                if log_uuid not in object_query_data:
                    output_file.write("\t".join(log_row) + "\tnew_uuid\t\t\t\n")
                    continue

                matches = [entry for entry in object_query_data[log_uuid] if entry["custom_file_name"] == unique_file_name]
                if matches:
                    sdat_version = matches[0]["sdat_version"]
                    if sdat_version == "0":
                        output_file.write("\t".join(log_row) + "\t\t\tcorrupt_sdat\t\t\n")
                else:
                    corrupt_entries = [entry for entry in object_query_data[log_uuid] if entry["sdat_version"] == "0"]
                    has_corrupt_sdat = bool(corrupt_entries)

                    if has_corrupt_sdat:
                        highest_object_version = max(
                            (entry["object_version"] for entry in corrupt_entries if entry["object_version"].startswith("T")),
                            default="",
                            key=lambda x: int(x[1:]),
                        )
                        output_file.write("\t".join(log_row) + f"\t\tnew_sdat\thas_corrupt_sdat\t{highest_object_version}\n")
                    else:
                        output_file.write("\t".join(log_row) + "\t\tnew_sdat\t\t\n")

def main():
    parser = argparse.ArgumentParser(description="Process log files and object query data.")
    parser.add_argument("--log_objects_file", required=True, help="Path to the log_OBJECTDEFS_ALL.log file.")
    parser.add_argument("--object_query_file", required=True, help="Path to the OBJECT_QUERY.txt file.")
    parser.add_argument("--output_log_file", required=True, help="Path to the output log file.")

    args = parser.parse_args()

    object_query_data = read_object_query(args.object_query_file)

    process_log_file(args.log_objects_file, object_query_data, args.output_log_file)

if __name__ == "__main__":
    main()
