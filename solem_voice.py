"""Conservative, local Portuguese dictation parser. Never writes records."""
import re
import unicodedata


def plain(text):
    return ''.join(c for c in unicodedata.normalize('NFD', str(text).lower()) if unicodedata.category(c) != 'Mn')


NUMBERS = dict(zip(
    'zero um uma dois duas tres quatro cinco seis sete oito nove dez onze doze treze quatorze catorze quinze dezesseis dezassete dezessete dezoito dezenove vinte trinta quarenta cinquenta sessenta setenta oitenta noventa cem cento duzentos trezentos quatrocentos quinhentos seiscentos setecentos oitocentos novecentos'.split(),
    [0,1,1,2,2,3,4,5,6,7,8,9,10,11,12,13,14,14,15,16,17,17,18,19,20,30,40,50,60,70,80,90,100,100,200,300,400,500,600,700,800,900]))
NUMBER_WORDS = '|'.join(NUMBERS)


def normalize(text):
    text = plain(text).strip()
    # Decimal words are normalized before punctuation. Do not interpret a comma
    # between foods as a decimal separator.
    pattern = rf'\b(?:{NUMBER_WORDS})(?:\s+e\s+(?:{NUMBER_WORDS}))*\b'
    text = re.sub(pattern, lambda m: str(sum(NUMBERS[w] for w in m[0].split() if w != 'e')), text)
    text = re.sub(r'(\d+)\s+(?:virgula|ponto)\s+(\d+)', r'\1.\2', text)
    text = re.sub(r'(\d),(\d)', r'\1.\2', text)
    return text


def clean_leftover(text):
    return re.sub(r'[\s,;:.!]+', ' ', text).strip()


def _number(value, lo=0, hi=34000):
    result = float(value)
    if not lo <= result <= hi:
        raise ValueError(f'Valor fora do intervalo permitido: {value}. Confira a transcrição.')
    return result


def parse_meal(text, foods, default_cumulative=True):
    """Food followed by grams. Fail closed on unknown foods/units/extra numbers."""
    text = normalize(text)
    cumulative = bool(re.search(r'\bacumulad[oa]s?\b', text))
    individual = bool(re.search(r'\bindividu(?:al|ais)\b', text))
    if cumulative and individual:
        raise ValueError('Diga apenas um modo: acumulado ou individual.')
    mode = cumulative if cumulative or individual else default_cumulative
    text = re.sub(r'\b(?:peso[s]?\s+)?(?:acumulad[oa]s?|individu(?:al|ais))(?:\s+da\s+balanca)?\b', ' ', text)
    kind = None
    for spoken, label in [('cafe da manha','Café da manhã'),('lanche da tarde','Lanche da tarde'),('almoco','Almoço'),('jantar','Jantar'),('outra refeicao','Outra')]:
        if re.search(rf'\b{spoken}\b', text):
            if kind: raise ValueError('Diga apenas uma refeição por vez.')
            kind = label
            text = re.sub(rf'\b{spoken}\b', ' ', text)
    aliases = {plain(f.get('display_name', f['name'])): f for f in foods}
    for alias, target in [('ovo','Ovo cozido'),('pure','Purê de batata'),('salada de alface','Alface')]:
        match = next((f for f in foods if f.get('display_name') == target), None)
        if match: aliases[alias] = match
    pattern = r'\b(' + '|'.join(re.escape(a) for a in sorted(aliases, key=len, reverse=True)) + r')\s*(?:[:=]|com)?\s*(\d+(?:\.\d+)?)\s*(?:gramas?\b|g\b)?'
    matches = list(re.finditer(pattern, text))
    remainder = re.sub(pattern, ' ', text)
    remainder = re.sub(r'\b(?:e|de|no|na|o|a|coloquei|colocar|refeicao|registrar|registra|balanca|pesos|peso)\b', ' ', remainder)
    if clean_leftover(remainder) or not 1 <= len(matches) <= 12:
        raise ValueError('Não entendi a lista completa. Use alimento seguido da leitura em gramas, por exemplo: arroz 170, feijão 323, acumulado. Confira alimentos e números não reconhecidos.')
    readings = [_number(m[2], 0.1) for m in matches]
    previous = 0.0
    items = []
    for match, reading in zip(matches, readings):
        grams = reading - previous if mode else reading
        if not 0 < grams <= 2000:
            raise ValueError('As leituras acumuladas devem aumentar, com até 2000 g adicionados por alimento. Confira o modo e a ordem.')
        food = aliases[match[1]]
        items.append(dict(name=food['name'], food_id=food['id'], grams=round(grams, 3)))
        previous = reading
    return dict(kind='meal', items=items, readings=readings, cumulative=mode, meal_type=kind)


def parse_weight(text):
    text = normalize(text)
    match = re.fullmatch(r'(?:meu peso(?: e)?|peso|estou com|pesei)?\s*(\d+(?:\.\d+)?)\s*(?:kg|quilos?|quilogramas?)?[.!]?', text)
    if not match: raise ValueError('Diga apenas o peso em kg, por exemplo: peso 67 vírgula 5 quilos.')
    return dict(kind='weight', kg=_number(match[1], 1, 500))


def parse_sleep(text):
    text = plain(text)
    # Preserve the clock separator before normalizing general cardinal numbers:
    # "uma e quinze" is 01:15, never the number sixteen.
    hours = ['vinte e tres','vinte e duas','vinte e dois','vinte e uma','vinte e um'] + [w for w,v in NUMBERS.items() if v < 24]
    hour = '|'.join(hours) + r'|\d{1,2}'
    minute = rf'(?:{NUMBER_WORDS})(?:\s+e\s+(?:{NUMBER_WORDS}))*|\d{{1,2}}|meia'
    text = re.sub(rf'\b(dormi|acordei)(?: as)?\s+({hour})(?: horas?)? e ({minute})\b',
                  lambda m: m[1]+' as '+normalize(m[2])+':'+('30' if m[3]=='meia' else normalize(m[3])), text)
    text = normalize(text)
    mode = 'auto'
    for phrase, value in [('na mesma data','same'),('na noite anterior','previous')]:
        if phrase in text:
            mode = value
            text = text.replace(phrase, '')
    text = text.strip(' ,.!')
    # 24h only; no guessing whether "uma e meia" is 01:30 or 13:30.
    time = r'(\d{1,2})(?:(?::|h| horas? e | e )(\d{1,2}|meia))?(?:\s*horas?)?'
    match = re.fullmatch(rf'\s*dormi(?: as)?\s+{time}\s*(?:e|,)\s*acordei(?: as)?\s+{time}\s*[.!]?\s*', text)
    if not match: raise ValueError('Use 24 horas: dormi às 3 e acordei às 13:30. Pode dizer “na mesma data” ou “na noite anterior”.')
    def clock(hour, minute):
        hour, minute = int(hour), 30 if minute == 'meia' else int(minute or 0)
        if hour > 23 or minute > 59: raise ValueError('Confira os horários: horas de 0 a 23 e minutos de 0 a 59.')
        return f'{hour:02}:{minute:02}'
    return dict(kind='sleep', bed=clock(match[1], match[2]), wake=clock(match[3], match[4]), mode=mode)


def parse_workout(text, exercises, current):
    text = normalize(text)
    aliases = {plain(name): name for name in exercises}
    for alias, name in [('flexoes','Flexão'),('agachamentos','Agachamento'),('barras pronadas','Barra Fixa (Pronada)'),('barras supinadas','Barra Fixa (Supinada)')]:
        if name in exercises: aliases[alias] = name
    exercise = current
    found = []
    for alias in sorted(aliases, key=len, reverse=True):
        pattern = r'(?<!\w)' + re.escape(alias) + r'(?!\w)'
        if re.search(pattern, text):
            found.append(aliases[alias]); text = re.sub(pattern, ' ', text)
    if len(set(found)) > 1: raise ValueError('Registre um exercício por vez.')
    if found: exercise = found[0]
    values = {}
    series = re.search(r'\b(\d+) series de (\d+)(?: repeticoes)?', text)
    if series:
        values.update(series=int(series[1]), repeticoes=int(series[1])*int(series[2]))
        text = text[:series.start()] + ' ' + text[series.end():]
    patterns = [
        ('descanso_seg', r'(?:descanso(?: de)?\s+)(\d+)\s*(segundos?|minutos?)'),
        ('series', r'(\d+)\s*series?'),
        ('repeticoes', r'(\d+)\s*(?:repeticoes|reps?|tentativas?)'),
        ('carga_kg', r'(?:carga(?: de)?\s+)(\d+(?:\.\d+)?)\s*(?:kg|quilos?)'),
        ('distancia_km', r'(\d+(?:\.\d+)?)\s*(?:km|quilometros?)'),
        ('duracao_min', r'(\d+)\s*minutos?'),
        ('isometria_segundos', r'(\d+)\s*segundos?')]
    for field, pattern in patterns:
        matches = list(re.finditer(pattern, text))
        if len(matches) > 1 or (matches and field in values):
            raise ValueError('Há dois valores para o mesmo campo. Confira a transcrição.')
        if matches:
            value = _number(matches[0][1], 0, 86400)
            if field == 'descanso_seg' and matches[0][2].startswith('minuto'): value *= 60
            values[field] = value if field in ('distancia_km','carga_kg') else int(value)
            text = re.sub(pattern, ' ', text)
    # "20 agachamentos" becomes just "20" after resolving the exercise.
    if found and re.fullmatch(r'\s*(?:fiz\s+)?\d+\s*[.!]?\s*', text) and 'repeticoes' not in values:
        values['repeticoes'] = int(re.search(r'\d+', text)[0]); text = ''
    text = re.sub(r'\b(?:fiz|de|e|duracao|total|tempo|sustentado)\b', ' ', text)
    if clean_leftover(text) or not values: raise ValueError('Confira a frase. Exemplo: agachamento, 3 séries de 20, descanso de 60 segundos. Para caminhada: 30 minutos, 2 quilômetros.')
    if any(not 0 <= value <= 86400 for value in values.values()):
        raise ValueError('Valores muito altos. Confira as quantidades e unidades.')
    return dict(kind='workout', exercise=exercise, values=values)
