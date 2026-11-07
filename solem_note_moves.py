"""Revision-checked folder moves without rewriting note content."""
import json
from solem_notes import DOCUMENT_PREFIX, folder_data, document_data
from solem_note_materials import material


def move_note(repo, items, note_id, destination, revision):
    """Move only the saved document, using the revision seen when dragging."""
    note = next((r for r in items if r["id"] == note_id), None)
    folders = {r["id"]: r for r in items if folder_data(r) is not None}
    if not note or note.get("kind") != "note" or material(note) or folder_data(note) is not None or note.get("archived"):
        raise ValueError("Esta anotação não está disponível. Atualize a biblioteca.")
    doc = document_data(note, items)
    if folders.get(doc["folder"], {}).get("archived"):
        raise ValueError("Restaure a pasta antes de mover esta anotação.")
    if destination and (destination not in folders or folders[destination].get("archived")):
        raise ValueError("A pasta de destino não está disponível.")
    if note["revision"] != revision:
        raise ValueError("Esta anotação mudou em outro dispositivo. Atualize antes de mover.")
    if doc["folder"] == destination:
        return note
    # Preserve all fields in a saved document, including future metadata.
    if note["body"].startswith(DOCUMENT_PREFIX):
        doc = json.loads(note["body"][len(DOCUMENT_PREFIX):])
    doc["folder"] = destination
    return repo.save(dict(kind="note", title=note["title"],
                          body=DOCUMENT_PREFIX+json.dumps(doc, ensure_ascii=False)), old=note)
