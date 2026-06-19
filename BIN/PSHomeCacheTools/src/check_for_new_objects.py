import re
import argparse

def read_object_query(file_path, debug=False):
    object_query_data = {}

    with open(file_path, "r", encoding="utf-8") as file:
        headers = file.readline().strip().split("\t")

        for line in file:
            row = line.strip().split("\t")
            row_data = dict(zip(headers, row))

            ext = row_data.get("Ext", "").lower()

            if ext in {"sdat", "bar"}:
                uuid = row_data.get("UUID", "").strip()

                if debug:
                    print(f"[OBJ] UUID={uuid} EXT={ext} FILE={row_data.get('Custom File Name')}")

                if uuid:
                    object_query_data.setdefault(uuid, []).append({
                        "custom_file_name": row_data.get("Custom File Name", "").strip(),
                        "sdat_version": row_data.get("SDAT Version", "").strip(),
                        "object_version": row_data.get("Object Version", "").strip(),
                        "ext": ext
                    })

    if debug:
        print(f"[OBJ] Loaded UUIDs: {len(object_query_data)}")

    return object_query_data


def process_log_file(log_file_path, object_query_data, output_file_path, debug=False):

    with open(output_file_path, "w", encoding="utf-8") as output_file:
        output_file.write(
            "Cache Name\tDAT Num\tSDAT Date\tProd(2) Folder\tLive(2) Folder\tUUID\tOrig File Name\tExtension\tSDATA Version\tUnique File Name\tnew_uuid\tnew_sdat\tcorrupt_sdat\thas_corrupt_sdat\thighest_object_version\n"
        )

        with open(log_file_path, "r", encoding="utf-8") as log_file:

            for line in log_file:
                log_row = line.strip().split("\t")

                if len(log_row) < 10:
                    if debug:
                        print("[SKIP] short row:", log_row)
                    continue

                log_uuid = log_row[5].strip()
                ext = log_row[7].strip().lower()
                base_id = log_row[9].strip()

                is_bar = (ext == "bar")

                unique_file_name = base_id + "." + ext

                if debug:
                    print("\n---")
                    print(f"[LOG] UUID={log_uuid}")
                    print(f"[LOG] EXT={ext}")
                    print(f"[LOG] BASE={base_id}")
                    print(f"[LOG] KEY={unique_file_name}")
                    
                if log_uuid not in object_query_data:
                    if debug:
                        print("[NEW_UUID] not found in OBJECT_QUERY")

                    output_file.write("\t".join(log_row) + "\tnew_uuid\t\t\t\n")
                    continue

                entries = object_query_data[log_uuid]

                if debug:
                    print(f"[OBJ] matches in UUID bucket: {len(entries)}")

                matches = [
                    entry for entry in entries
                    if entry["custom_file_name"] == unique_file_name
                ]

                if debug:
                    print(f"[MATCH] found={len(matches)}")

                if matches:
                    sdat_version = matches[0]["sdat_version"]

                    if debug:
                        print(f"[MATCH] sdat_version={sdat_version}")

                    if sdat_version == "0":
                        if is_bar:
                            output_file.write(
                                "\t".join(log_row) +
                                "\t\tnew_bar\t\t\n"
                            )
                        else:
                            output_file.write(
                                "\t".join(log_row) +
                                "\t\t\tcorrupt_sdat\t\t\n"
                            )
                else:
                    corrupt_entries = [
                        entry for entry in entries
                        if entry["sdat_version"] == "0"
                    ]

                    has_corrupt_sdat = bool(corrupt_entries)

                    if debug:
                        print(f"[NO MATCH] corrupt_entries={len(corrupt_entries)}")

                    if has_corrupt_sdat:
                        highest_object_version = max(
                            (
                                entry["object_version"]
                                for entry in corrupt_entries
                                if entry["object_version"].startswith("T")
                            ),
                            default="",
                            key=lambda x: int(x[1:]) if x[1:].isdigit() else 0,
                        )

                        flag = "new_bar" if is_bar else "new_sdat"

                        output_file.write(
                            "\t".join(log_row) +
                            f"\t\t{flag}\thas_corrupt_sdat\t{highest_object_version}\n"
                        )
                    else:
                        flag = "new_bar" if is_bar else "new_sdat"

                        output_file.write(
                            "\t".join(log_row) +
                            f"\t\t{flag}\t\t\n"
                        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log_objects_file", required=True)
    parser.add_argument("--object_query_file", required=True)
    parser.add_argument("--output_log_file", required=True)
    parser.add_argument("--debug", action="store_true")

    args = parser.parse_args()

    obj = read_object_query(args.object_query_file, args.debug)
    process_log_file(args.log_objects_file, obj, args.output_log_file, args.debug)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("FATAL ERROR:", e)
        import traceback
        traceback.print_exc()