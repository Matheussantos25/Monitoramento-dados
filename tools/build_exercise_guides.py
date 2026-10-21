"""Build original, offline vector diagrams shared by Streamlit and Compose.

Coordinates are schematic, not motion capture or a biomechanical assessment.
No downloaded artwork, video, dependencies or personal data.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACE = "https://www.acefitness.org/resources/everyone/exercise-library/"
CHIN = "https://www.acefitness.org/continuing-education/certified/february-2025/8800/the-ace-do-it-better-series-chin-ups/"
MAYO = "https://www.mayoclinic.org/healthy-lifestyle/fitness/in-depth/weight-training/art-20045842"


def guide(motion, view, cues, avoid, labels=("Preparação", "Movimento"), grip="", source=ACE):
    return dict(motion=motion, view=view, cues=cues, avoid=avoid, labels=list(labels), grip=grip, source=source)


guides = {
    "Abdominal Levantada": guide("legraise", "Vista lateral · elevação das pernas deitado", ["Deite de costas e mantenha o abdômen ativo; eleve as pernas com controle.", "Desça apenas até onde consegue manter o tronco estável e a lombar confortável; dobre os joelhos se precisar reduzir a dificuldade."], "Não balance as pernas nem force a lombar para alcançar o chão.", ("Descida dentro da sua amplitude", "Elevação controlada")),
    "Remada em Pé na Polia": guide("standingrow", "Vista lateral · puxada horizontal", ["Ajuste a polia para uma puxada horizontal; pés firmes e joelhos destravados.", "Puxe o acessório em direção ao abdômen e retorne controlando a carga; mantenha o tronco estável."], "O acessório define a pegada. Não incline o corpo para trás para mover a carga.", ("Braços à frente", "Puxada ao abdômen")),
    "Remada em Pé na Polia com barra": guide("standingrow", "Vista lateral · barra, puxada horizontal", ["Pés firmes e polia ajustada para puxar na horizontal; neste exemplo, palmas voltadas para baixo na barra.", "Leve a barra em direção ao abdômen e retorne sem balançar o tronco."], "Não confunda com remada alta: aqui a barra vai ao abdômen, não sobe ao peito.", ("Braços à frente", "Barra junto ao abdômen")),
    "Barra Fixa (Pronada)": guide("pull", "Vista de frente", ["Palmas para longe do seu rosto; segure com o polegar envolvendo a barra.", "Suba sem embalo, aproximando o queixo da altura da barra; desça com controle."], "Não estique o pescoço para alcançar a barra nem balance as pernas.", ("Braços estendidos, com controle", "Queixo próximo/acima da barra"), "pronated", CHIN),
    "Barra Fixa (Supinada)": guide("pull", "Vista de frente", ["Palmas voltadas para seu rosto; mãos aproximadamente na largura dos ombros.", "Puxe sem impulso das pernas; retorne com controle, sem despencar."], "Não confunda supinada com pegada neutra (palmas uma para a outra).", ("Braços estendidos, com controle", "Queixo próximo/acima da barra"), "supinated", CHIN),
    "Agachamento": guide("squat", "Vista lateral", ["Apoie o pé inteiro e acompanhe a direção dos pés com os joelhos.", "Leve o quadril para trás e para baixo, dentro de uma amplitude confortável; volte com controle."], "Evite levantar os calcanhares ou deixar os joelhos cederem para dentro.", ("Em pé", "Descida controlada"), source="https://www.mayoclinic.org/healthy-lifestyle/fitness/multimedia/squat/vid-20084663"),
    "Flexão": guide("pushup", "Vista lateral", ["Mãos apoiadas perto da linha dos ombros; mantenha tronco e quadril alinhados.", "Dobre os cotovelos levando o peito em direção ao chão; empurre sem perder o alinhamento."], "Não deixe a lombar afundar. Uma superfície elevada pode reduzir a dificuldade.", ("Apoio alto", "Descida controlada")),
    "Prancha": guide("plank", "Vista lateral · posição estática", ["Cotovelos sob os ombros e antebraços apoiados.", "Mantenha cabeça, tronco e quadril alinhados; respire durante a sustentação."], "Não levante demais o quadril nem prenda a respiração.", ("Sustentar com controle", "")),
    "Caminhada": guide("walk", "Esquema da passada", ["Olhe à frente, relaxe os ombros e deixe os braços acompanharem os passos.", "Use uma passada confortável, sem forçar o comprimento do passo."], "O desenho não define cadência nem distância; o GPS continua independente."),
    "Corrida": guide("run", "Esquema da passada", ["Mantenha os ombros relaxados e os braços acompanhando a passada.", "Procure uma passada confortável; ajuste o ritmo à recuperação."], "Não copie o desenho para forçar uma aterrissagem ou amplitude específica."),
    "Bike": guide("bike", "Vista lateral · bicicleta ilustrativa", ["Ajuste banco e guidão ao seu corpo antes de pedalar.", "Mantenha mãos apoiadas e joelhos acompanhando o movimento dos pedais."], "A ilustração não é uma medida para ajuste da bicicleta; evite travar os joelhos."),
    "Pular Normal": guide("jump", "Vista de frente · salto baixo", ["Faça saltos baixos e aterrise suavemente.", "Deixe joelhos e quadril amortecerem o contato com o chão."], "Evite aterrissar com as pernas rígidas.", ("Apoio no chão", "Salto baixo")),
    "Pular Corda": guide("rope", "Vista de frente · corda esquemática", ["Gire a corda principalmente com os punhos, mantendo os cotovelos próximos ao corpo.", "Faça saltos baixos com aterrissagem suave."], "A corda desenhada indica o espaço livre, não sua trajetória exata.", ("Apoio", "Passagem da corda")),
    "Subida Escada (Andares)": guide("stairs", "Vista lateral", ["Apoie o pé no degrau e suba sem saltar degraus.", "Use o corrimão quando necessário e mantenha o caminho livre."], "Não use o celular enquanto sobe.", ("Pé no degrau", "Transferência do peso")),
    "Remada Baixa": guide("row", "Vista lateral · puxador neutro", ["Sente com a coluna confortável e pés firmes; neste exemplo, palmas uma para a outra.", "Puxe em direção ao abdômen e retorne sem balançar o tronco."], "Outros puxadores mudam a pegada. Confirme o acessório antes de copiar a posição."),
    "Puxada Alta": guide("lat", "Vista de frente · barra pronada", ["Ajuste o apoio das coxas e segure a barra com palmas para a frente.", "Traga a barra à frente, em direção à parte alta do peito; retorne controlando a carga."], "Não puxe a barra atrás da nuca nem use o peso do corpo para dar trancos.", ("Braços elevados", "Barra à frente do peito"), "pronated"),
    "L-Sit": guide("lsit", "Vista lateral · posição estática avançada", ["Use paralelas estáveis; mãos apoiadas e ombros ativos.", "A figura mostra a sustentação final, não ensina a progressão até ela."], "Peça orientação para a progressão. Não force punhos, ombros ou a extensão das pernas.", ("Posição final ilustrativa", "")),
    "Handstand (Parada de Mãos)": guide("handstand", "Vista de frente · posição avançada", ["Mãos firmes e braços sustentando o corpo com controle.", "A figura mostra apenas a posição final; entrada, saída e quedas exigem orientação presencial."], "Não tente inverter o corpo sozinho só por este desenho. Garanta espaço e supervisão.", ("Posição final ilustrativa", "")),
}
pending = {
    "Massagem Facial": "Não há técnica padronizada definida neste cadastro. O registro continua disponível, sem demonstrar pressão sobre o rosto.",
    "Mewing com borracha": "Não incluímos demonstração de carga na mandíbula. Consulte um dentista antes de usar exercitadores; seus registros foram preservados.",
    "Planche": "Habilidade avançada: confirme a progressão com um profissional. Não demonstramos a entrada sem avaliar o nível de preparo.",
}
for name, reason in pending.items():
    guides[name] = dict(motion="", view="Guia específico pendente", cues=[reason], avoid="Não improvise a execução a partir do nome.", labels=[], grip="", source="https://adanews.ada.org/huddles/experts-expose-legitimacy-of-facial-fitness-gum/" if name == "Mewing com borracha" else MAYO)

for name in ("Caminhada", "Corrida", "Bike"):
    guides[name]["labels"] = ["Postura ilustrativa"]

from exercise_figure_art import build_motions, build_grips
motions, grips = build_motions(), build_grips()
guides["Barra Fixa (Pronada)"]["motion"] = "pull_pronated"
guides["Barra Fixa (Supinada)"]["motion"] = "pull_supinated"
data = dict(version=2, notice="Ilustração de referência, não avaliação da sua execução. A amplitude deve ser confortável. Pare se houver dor e peça orientação para ajustar a técnica.", motions=motions, grips=grips, guides=guides)
for relative in ("assets/exercise_guides.json", "android-app/app/src/main/assets/exercise_guides.json", "android-app/app/src/test/resources/exercise_guides.json"):
    (ROOT / relative).write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf8")
print(f"{len(guides)} guides, {len(motions)} original vector diagrams; {len(json.dumps(data, ensure_ascii=False).encode('utf8'))} bytes")
