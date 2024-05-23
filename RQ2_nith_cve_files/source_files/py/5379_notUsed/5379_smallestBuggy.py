from .paths import file_uri_to_path
def process_uri(uri: str, changes: list) -> Path:
    path = file_uri_to_path(uri)
    editable_file = EditableFile(path)

    await editable_file.read()
    for change in changes[:1]:
        change_range = change.get("range", editable_file.full_range)
        editable_file.apply_change(change["text"], **change_range)
    await editable_file.write()
    return path