"""Note documents, folders and legacy attachment projection."""
import base64
import json
from uuid import UUID
from solem_note_materials import material, PREFIX as MATERIAL_PREFIX
from solem_workspace import validate_item

FOLDER_PREFIX = "solem-note-folder-v1\n"
DOCUMENT_PREFIX = "solem-note-document-v1\n"


def folder_data(item):
    if item.get("kind") == "note" and item.get("body", "").startswith(FOLDER_PREFIX):
        try:
            return json.loads(item["body"][len(FOLDER_PREFIX):])
        except (ValueError, TypeError):
            pass
    return None


def document_data(item, items=()):
    body = (item or {}).get("body", "")
    if body.startswith(DOCUMENT_PREFIX):
        data = json.loads(body[len(DOCUMENT_PREFIX):])
        return dict(folder=data.get("folder", ""), blocks=data.get("blocks", []))
    blocks = [dict(id="legacy-text", type="text", text=body)]
    for row in items:
        data = material(row)
        if not data or data["folder"] != (item or {}).get("id") or row.get("archived") or data.get("pending"):
            continue
        if data["type"] == "image":
            blocks.append(dict(id=row["id"], type="image", ref=row["id"], caption=row["title"]))
        else:
            blocks.append(dict(id=row["id"], type="text", text=data["value"]))
    return dict(folder="", blocks=blocks)


def image_assets(note_id, items):
    return {row["id"]: data["value"] for row in items
            if (data := material(row)) and data["folder"] == note_id
            and data["type"] == "image" and not row.get("archived")}


def prepare_note(note_id, title, folder, blocks, images, items):
    UUID(note_id)
    if folder:
        if not any(row["id"] == folder and folder_data(row) is not None and not row.get("archived") for row in items):
            raise ValueError("Escolha uma pasta disponível.")
    if not isinstance(blocks, list) or len(blocks) > 150:
        raise ValueError("Use até 150 blocos por anotação.")
    assets = image_assets(note_id, items)
    pending, clean = {}, []
    for block in blocks:
        kind = block.get("type")
        if kind == "text":
            clean.append(dict(id=str(block["id"])[:80], type="text", text=str(block.get("text", ""))))
        elif kind == "image":
            ref = str(block["ref"])
            UUID(ref)
            if ref not in assets:
                value = images.get(ref, "")
                try:
                    raw = base64.b64decode(value, validate=True)
                    if len(raw) > 35000 or not raw.startswith(b"\xff\xd8"):
                        raise ValueError()
                except (ValueError, TypeError):
                    raise ValueError("Uma imagem não pôde ser carregada. Selecione-a novamente.")
                pending[ref] = dict(id=ref, kind="note", title=str(block.get("caption") or "Imagem")[:160],
                    body=MATERIAL_PREFIX + json.dumps(dict(folder=note_id, type="image", value=value, pending=True)))
            clean.append(dict(id=str(block["id"])[:80], type="image", ref=ref, caption=str(block.get("caption", ""))[:160]))
        else:
            raise ValueError("Tipo de conteúdo inválido.")
    item = dict(kind="note", title=title.strip(), body=DOCUMENT_PREFIX + json.dumps(dict(folder=folder, blocks=clean), ensure_ascii=False))
    validate_item(item)
    for row in pending.values():
        validate_item(row)
    return item, list(pending.values())


def save_note(repo, note_id, title, folder, blocks, images, items, old=None):
    item, uploads = prepare_note(note_id, title, folder, blocks, images, items)
    if uploads:
        repo.add_folder_images(uploads)
    return repo.save(item, old=old, new_id=note_id)
