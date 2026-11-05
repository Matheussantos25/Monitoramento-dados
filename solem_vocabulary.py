"""Private, reviewable vocabulary and free public lookup. Never writes activity rows."""
import csv
import html
import io
import json
import re
import zipfile
from html.parser import HTMLParser
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
from solem_vocabulary_review import review_state

PREFIX = "SOLEM_VOCAB_V1\n"
LIMITS = dict(word=100, sentence=2000, definition=3000, context=300, source=1500, forms=2000,
              image=2000, image_page=2000, image_credit=2000)
AGENT = "Solem/0.21 (https://github.com/Matheussantos25/Monitoramento-dados)"


def vocabulary_data(item):
    if not item or item.get("kind") != "note" or not str(item.get("body", "")).startswith(PREFIX):
        return None
    try:
        data = json.loads(item["body"][len(PREFIX):])
        if isinstance(data, dict) and all(isinstance(data.get(k, ""), str) for k in LIMITS):
            clean = {k: data.get(k, "") for k in LIMITS}
            if 'review' in data: clean['review'] = review_state(data['review'])
            return clean
    except (ValueError, TypeError):
        pass
    return None


def vocabulary_body(data):
    clean = {k: str(data.get(k, "")).strip() for k in LIMITS}
    if not clean["word"] or any(len(clean[k]) > n for k, n in LIMITS.items()):
        raise ValueError("Informe uma palavra de até 100 caracteres; reduza os campos muito longos.")
    if clean["image"] and not media_url(clean["image"]):
        raise ValueError("Escolha uma imagem da busca do Wikimedia Commons.")
    if 'review' in data: clean['review'] = review_state(data['review'])
    return PREFIX + json.dumps(clean, ensure_ascii=False)


def media_url(url):
    p = urlparse(url)
    return p.scheme == "https" and p.hostname in {"upload.wikimedia.org", "thumb.wikimedia.org"} and not p.username and p.port in (None, 443)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def fetch(url, limit=1_500_000):
    # All callers construct known provider URLs. Images additionally validate the exact host.
    with build_opener(NoRedirect).open(Request(url, headers={"User-Agent": AGENT}), timeout=12) as response:
        result = response.read(limit + 1)
        if len(result) > limit:
            raise ValueError("Resposta muito grande. Tente outra imagem ou palavra.")
        return result, response.headers.get_content_type()


def dictionary(word):
    word = word.strip()
    if not 1 <= len(word) <= 100:
        raise ValueError("Digite uma palavra ou expressão curta em inglês.")
    raw, _ = fetch("https://freedictionaryapi.com/api/v1/entries/en/" + quote(word, safe=""))
    data = json.loads(raw)
    source = "FreeDictionaryAPI.com · Wiktionary · CC BY-SA 4.0 · " + "https://en.wiktionary.org/wiki/" + quote(word, safe="")
    options = []
    for entry in data.get("entries", []):
        if entry.get("language", {}).get("code") != "en":
            continue
        for sense in entry.get("senses", []):
            definition = sense.get("definition", "")
            if not definition:
                continue
            examples = [x for x in sense.get("examples", []) if isinstance(x, str)]
            forms = "\n".join(str(f.get("word", ""))[:100] for f in entry.get("forms", [])[:20])
            options.append(dict(forms=forms, definition=definition[:3000], sentence=(examples[0] if examples else "")[:2000],
                                part=entry.get("partOfSpeech", ""), source=source))
    return options[:30]


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []
    def handle_data(self, data):
        self.parts.append(data)


def plain(value):
    parser = PlainText(); parser.feed(str(value)); return " ".join(parser.parts).strip()


def image_search(term):
    query = urlencode(dict(action="query", format="json", generator="search", gsrsearch=term[:100]+" filetype:bitmap",
                           gsrnamespace=6, gsrlimit=6, prop="imageinfo", iiprop="url|extmetadata|mime", iiurlwidth=480))
    raw, _ = fetch("https://commons.wikimedia.org/w/api.php?" + query)
    pages = json.loads(raw).get("query", {}).get("pages", {}).values()
    results = []
    for page in sorted(pages, key=lambda p: p.get("index", 999)):
        info = next(iter(page.get("imageinfo", [])), {})
        url = info.get("thumburl", "")
        meta = info.get("extmetadata", {})
        license_name = plain(meta.get("LicenseShortName", {}).get("value", ""))
        if not media_url(url) or info.get("mime") not in ("image/jpeg", "image/png") or not license_name:
            continue
        credit = plain(meta.get("Artist", {}).get("value", "")) + " · " + license_name + " · Wikimedia Commons"
        results.append(dict(image=url, image_page=info.get("descriptionurl", ""), image_credit=credit[:2000], title=page.get("title", "")))
    return results


def bold_sentence(sentence, word, forms=""):
    words = [word.strip()] + [f.strip() for f in forms.splitlines() if f.strip()]
    pattern = re.compile(r"(?<!\w)" + "(?:" + "|".join(re.escape(w) for w in sorted(set(words), key=len, reverse=True)) + r")(?!\w)", re.I)
    chunks, end = [], 0
    if not word.strip():
        return html.escape(sentence)
    for match in pattern.finditer(sentence):
        chunks += [html.escape(sentence[end:match.start()]), "<b>" + html.escape(match[0]) + "</b>"]
        end = match.end()
    chunks.append(html.escape(sentence[end:]))
    return "".join(chunks).replace("\n", "<br>")


def card_html(data, image_override=None):
    if not data.get("sentence", "").strip() or not data.get("definition", "").strip():
        raise ValueError("Complete a frase e o significado em inglês antes de exportar.")
    front = bold_sentence(data["sentence"], data["word"], data.get("forms", ""))
    if "<b>" not in front:
        raise ValueError("A palavra precisa aparecer na frase. Ajuste a palavra para a forma usada na série.")
    escape = lambda s: html.escape(s).replace("\n", "<br>")
    back = "<p>" + escape(data["definition"]) + "</p>"
    url = image_override if image_override is not None else data.get("image", "")
    if url and (image_override is not None or media_url(url)):
        back += '<p><img src="' + html.escape(url, quote=True) + '" alt="' + html.escape(data["word"], quote=True) + '" style="max-width:100%;max-height:320px"></p>'
        back += "<small>" + escape(data.get("image_credit", "")) + "<br>" + escape(data.get("image_page", "")) + "</small>"
    if data.get("source"):
        back += "<p><small>" + escape(data["source"]) + "</small></p>"
    return front, back


def anki_text(data, image_override=None):
    out = io.StringIO()
    out.write("#separator:Tab\n#html:true\n#columns:Front\tBack\n")
    csv.writer(out, delimiter="\t", lineterminator="\n").writerow(card_html(data, image_override))
    return out.getvalue()


def anki_package(data):
    media = None; name = ""
    if data.get("image"):
        if not media_url(data["image"]):
            raise ValueError("Imagem inválida.")
        media, mime = fetch(data["image"], 3_000_000)
        if mime not in ("image/jpeg", "image/png"):
            raise ValueError("Imagem indisponível. Remova-a ou escolha outra antes de exportar.")
        import hashlib
        name = "solem_" + hashlib.sha256(media).hexdigest()[:20] + (".png" if mime == "image/png" else ".jpg")
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("card.txt", anki_text(data, name if media else None))
        if media:
            archive.writestr("media/" + name, media)
        archive.writestr("LEIA-ME.txt", "No Anki para computador: extraia o ZIP. Copie o arquivo de media/ para collection.media do seu perfil. Importe card.txt como Básico (Front/Back), separado por tabulação, com HTML habilitado. Depois sincronize com o celular. Este ZIP não é um .apkg. Confira duplicatas na prévia de importação. Fontes e créditos constam no verso. Exportar não registra cards adicionados nem tempo estudado no Solem.")
    return result.getvalue()
