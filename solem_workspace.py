"""Private workspace: explicit schema, session-local client, optimistic updates."""
import base64
import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import uuid4

KINDS = {'Anotações':'note', 'Resumos':'summary', 'Mapas mentais':'mindmap', 'PDFs':'pdf', 'Cronograma':'plan', 'Investimentos':'investment'}
MAX_PDF = 10 * 1024 * 1024

def public_key(key):
    if key.startswith('sb_publishable_'):
        return True
    try:
        payload = key.split('.')[1]
        return json.loads(base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4))).get('role') == 'anon'
    except (ValueError, IndexError, TypeError):
        return False

def cents(text):
    if not re.fullmatch(r'\d{1,10}([.,]\d{1,2})?', text.strip()):
        raise ValueError('Use valores positivos, sem separador de milhar e com até duas casas decimais.')
    value = int(Decimal(text.strip().replace(',', '.')) * 100)
    if value > 999999999999:
        raise ValueError('Valor acima do limite suportado.')
    return value

def mind_nodes(body):
    nodes, parents = [], []
    for line in body.replace('\r', '').split('\n'):
        if not line.strip():
            continue
        spaces = len(line) - len(line.lstrip(' '))
        depth = spaces // 2
        if '\t' in line or spaces % 2 or depth > 5 or len(line.strip()) > 160:
            raise ValueError('Use 2 espaços por nível, até 5 níveis e 160 caracteres por tópico.')
        if (not nodes and depth != 0) or (nodes and depth == 0) or depth > len(parents):
            raise ValueError('Use uma única raiz e não pule níveis.')
        parents = parents[:depth]
        nodes.append((line.strip(), parents[-1] if parents else None, depth))
        parents.append(len(nodes) - 1)
    if not 1 <= len(nodes) <= 80:
        raise ValueError('O mapa deve ter entre 1 e 80 tópicos.')
    return nodes

def validate_pdf(data):
    if len(data) > MAX_PDF or not data.startswith(b'%PDF-'):
        raise ValueError('Selecione um PDF válido com até 10 MB.')

def validate_item(item):
    if item['kind'] not in KINDS.values() or not 1 <= len(item['title'].strip()) <= 160 or len(item['body']) > 50000:
        raise ValueError('Informe título de até 160 caracteres e conteúdo de até 50 mil caracteres.')
    if item['kind'] == 'mindmap':
        mind_nodes(item['body'])
    if item['kind'] in ('plan', 'investment'):
        day = date.fromisoformat(item['event_date'])
        if not date(1900,1,1) <= day <= date(2200,12,31):
            raise ValueError('Data fora do intervalo suportado.')
    if item['kind'] == 'plan':
        if not 1 <= item['duration_minutes'] <= 1440 or not re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d', item['event_time']):
            raise ValueError('Informe horário HH:MM e duração entre 1 e 1440 minutos.')
    if item['kind'] == 'investment' and not all(0 <= item[k] <= 999999999999 for k in ('invested_cents','value_cents')):
        raise ValueError('Valor inválido.')

class Workspace:
    def __init__(self, client):
        self.client = client

    def list(self):
        result = []
        while True:
            page = self.client.table('solem_items').select('*').order('created_at').order('id').range(len(result), len(result)+499).execute().data
            result.extend(page)
            if len(page) < 500:
                return result

    def save(self, item, old=None, new_id=None):
        validate_item(item)
        if old:
            result = self.client.table('solem_items').update(item).eq('id', old['id']).eq('revision', old['revision']).execute().data
            if len(result) != 1:
                raise ValueError('Este registro mudou em outro dispositivo. Atualize a lista antes de editar novamente.')
        else:
            result = self.client.table('solem_items').insert(dict(item, id=new_id or str(uuid4()))).execute().data
        if not result:
            raise ValueError('Não foi possível confirmar o salvamento. Atualize antes de tentar novamente.')
        return result[0]

    def archive(self, old, archived):
        result = self.client.table('solem_items').update({'archived':archived}).eq('id',old['id']).eq('revision',old['revision']).execute().data
        if len(result) != 1:
            raise ValueError('Registro alterado em outro dispositivo. Atualize a lista.')

    def upload(self, item, data):
        validate_pdf(data)
        self.client.storage.from_('solem-documents').upload(item['file_path'], data, {'content-type':'application/pdf','upsert':'false'})

    def download(self, item):
        data = self.client.storage.from_('solem-documents').download(item['file_path'])
        validate_pdf(data)
        return data
