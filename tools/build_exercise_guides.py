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


def pose(head, *lines):
    return dict(head=list(head), lines=list(lines))


stand = pose((150, 38, 14), [[150, 55], [150, 125]],
             [[150, 65], [122, 95], [115, 125]], [[150, 65], [178, 95], [185, 125]],
             [[150, 125], [130, 170], [120, 210]], [[150, 125], [170, 170], [180, 210]])
pull = [pose((150, 108, 14), [[150, 125], [150, 165]],
             [[150, 129], [125, 90], [100, 50]], [[150, 129], [175, 90], [200, 50]],
             [[150, 165], [139, 187], [137, 210]], [[150, 165], [161, 187], [163, 210]]),
        pose((150, 24, 14), [[150, 41], [150, 100]],
             [[150, 50], [108, 82], [100, 50]], [[150, 50], [192, 82], [200, 50]],
             [[150, 100], [139, 145], [137, 190]], [[150, 100], [161, 145], [163, 190]])]
squat = [pose((150, 38, 14), [[150, 55], [145, 125]], [[150, 65], [185, 80], [220, 80]],
               [[145, 125], [160, 165], [160, 205], [185, 205]]),
         pose((178, 90, 14), [[170, 106], [120, 155]], [[166, 111], [205, 113], [240, 113]],
               [[120, 155], [180, 157], [160, 205], [185, 205]])]
pushup = [pose((72, 87, 13), [[84, 101], [160, 140], [240, 190]], [[91, 105], [91, 148], [91, 193], [65, 193]], [[240, 190], [256, 193]]),
          pose((65, 148, 13), [[80, 158], [160, 173], [240, 190]], [[91, 160], [123, 177], [91, 193], [65, 193]], [[240, 190], [256, 193]])]
plank = [pose((65, 120, 13), [[80, 133], [160, 160], [240, 190]], [[91, 138], [100, 193], [58, 193]], [[240, 190], [256, 193]])]
walk = [pose((150, 38, 14), [[150, 55], [150, 125]], [[150, 65], [120, 90], [110, 113]], [[150, 65], [182, 88], [196, 64]], [[150, 125], [122, 165], [95, 207]], [[150, 125], [178, 165], [197, 207]]),
        pose((150, 38, 14), [[150, 55], [150, 125]], [[150, 65], [182, 88], [196, 64]], [[150, 65], [120, 90], [110, 113]], [[150, 125], [178, 165], [197, 207]], [[150, 125], [122, 165], [95, 207]])]
run = [pose((162, 34, 14), [[158, 51], [140, 115]], [[154, 65], [119, 90], [108, 65]], [[154, 65], [185, 90], [206, 70]], [[140, 115], [185, 146], [165, 186]], [[140, 115], [108, 159], [75, 130]]),
       pose((162, 34, 14), [[158, 51], [140, 115]], [[154, 65], [185, 90], [206, 70]], [[154, 65], [119, 90], [108, 65]], [[140, 115], [108, 159], [75, 130]], [[140, 115], [185, 146], [165, 186]])]
jump = [stand, pose((150, 18, 14), [[150, 35], [150, 100]], [[150, 45], [120, 70], [105, 100]], [[150, 45], [180, 70], [195, 100]], [[150, 100], [133, 142], [130, 185]], [[150, 100], [167, 142], [170, 185]])]
row = [pose((118, 55, 14), [[120, 72], [130, 138]], [[120, 85], [168, 94], [212, 99]], [[130, 138], [180, 152], [227, 192]]),
       pose((118, 55, 14), [[120, 72], [130, 138]], [[120, 85], [88, 113], [145, 111]], [[130, 138], [180, 152], [227, 192]])]
lat = [pose((150, 86, 14), [[150, 103], [150, 150]], [[150, 110], [108, 75], [95, 26]], [[150, 110], [192, 75], [205, 26]], [[150, 150], [190, 150], [190, 207]]),
       pose((150, 86, 14), [[150, 103], [150, 150]], [[150, 110], [110, 137], [95, 110]], [[150, 110], [190, 137], [205, 110]], [[150, 150], [190, 150], [190, 207]])]
stairs = [pose((140, 36, 14), [[140, 53], [130, 116]], [[138, 70], [165, 90], [188, 77]], [[130, 116], [175, 132], [175, 167]], [[130, 116], [110, 164], [110, 205]]),
          pose((167, 15, 13), [[162, 31], [158, 94]], [[160, 48], [192, 67], [209, 49]], [[158, 94], [174, 126], [175, 167]], [[158, 94], [125, 137], [122, 178]])]
bike = [pose((185, 49, 14), [[173, 63], [123, 105]], [[170, 70], [198, 95], [226, 87]], [[123, 105], [170, 132], [146, 175]], [[123, 105], [113, 143], [153, 139]]),
        pose((185, 49, 14), [[173, 63], [123, 105]], [[170, 70], [198, 95], [226, 87]], [[123, 105], [113, 143], [153, 139]], [[123, 105], [170, 132], [146, 175]])]
lsit = [pose((112, 35, 14), [[112, 53], [112, 120]], [[113, 65], [92, 99], [92, 143]], [[112, 120], [170, 120], [235, 120]])]
handstand = [pose((150, 174, 13), [[150, 156], [150, 94]], [[150, 150], [131, 178.5], [112, 207]], [[150, 150], [169, 178.5], [188, 207]], [[150, 94], [139, 54], [139, 12]], [[150, 94], [161, 54], [161, 12]])]
legraise = [pose((50, 176, 13), [[65, 190], [145, 190]], [[75, 190], [83, 199], [120, 199]], [[145, 190], [190, 170], [237, 150]]),
            pose((50, 176, 13), [[65, 190], [145, 190]], [[75, 190], [83, 199], [120, 199]], [[145, 190], [151, 136], [159, 80]])]
standingrow = [pose((118, 38, 14), [[118, 55], [118, 125]], [[118, 70], [165, 94], [210, 112]], [[118, 125], [108, 168], [98, 210]], [[118, 125], [135, 168], [155, 210]], [[210, 112], [267, 112]]),
               pose((118, 38, 14), [[118, 55], [118, 125]], [[118, 70], [84, 104], [145, 112]], [[118, 125], [108, 168], [98, 210]], [[118, 125], [135, 168], [155, 210]], [[145, 112], [267, 112]])]

motions = {
    "pull": dict(frames=pull, equipment=[[[65, 50], [235, 50]]]),
    "squat": dict(frames=squat), "pushup": dict(frames=pushup), "plank": dict(frames=plank),
    "walk": dict(frames=walk), "run": dict(frames=run), "jump": dict(frames=jump),
    "rope": dict(frames=jump, equipment=[[[105, 110], [65, 130], [72, 205], [150, 219], [228, 205], [235, 130], [195, 110]]]),
    "row": dict(frames=row, equipment=[[[100, 145], [150, 145]], [[267, 95], [267, 205]], [[227, 192], [242, 170]]]),
    "lat": dict(frames=lat, equipment=[[[100, 155], [175, 155]], [[40, 205], [40, 10], [150, 10]]]),
    "stairs": dict(frames=stairs, equipment=[[[70, 210], [145, 210], [145, 170], [215, 170], [215, 130], [280, 130]]]),
    "bike": dict(frames=bike, equipment=[[[80, 175], [125, 105], [155, 175], [80, 175]], [[155, 175], [220, 175], [210, 90], [236, 85]], [[115, 104], [140, 104]]], circles=[[80, 175, 34], [220, 175, 34]]),
    "lsit": dict(frames=lsit, equipment=[[[70, 148], [125, 148]], [[78, 148], [78, 205]], [[119, 148], [119, 205]]]),
    "handstand": dict(frames=handstand, equipment=[[[245, 10], [245, 215]]]),
    "legraise": dict(frames=legraise, equipment=[[[30, 205], [265, 205]]]),
    "standingrow": dict(frames=standingrow, equipment=[[[267, 30], [267, 210]]]),
}
# Moving implement belongs to the pose, not the fixed machine.
for i, frame in enumerate(lat):
    frame["lines"].append([[80, 26 if i == 0 else 110], [220, 26 if i == 0 else 110]])
for i, frame in enumerate(row):
    frame["lines"].append([[212 if i == 0 else 145, 99 if i == 0 else 111], [267, 95]])
# Gait and cycling need more than two poses to convey a useful cycle. Keep
# these as honest posture references instead of a misleading flip animation.
for name in ("walk", "run", "bike"):
    motions[name]["frames"] = motions[name]["frames"][:1]


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

# Close-up of two hands around a bar, viewed by the person exercising.
# Both diagrams share the outline; knuckles vs palm creases identify the side.
grips = {}
for kind in ("pronated", "supinated"):
    outlines, marks = [], []
    for x in (88, 184):
        outlines.append([[x, 92], [x, 70], [x-8, 58], [x-8, 29], [x+30, 29], [x+30, 60], [x+23, 72], [x+23, 92]])
        for offset in (0, 9, 18):
            outlines.append([[x+offset, 30], [x+offset, 43]])
        outlines.append([[x+30, 46], [x+17, 56], [x+11, 51]])
        if kind == "pronated":
            for offset in (0, 9, 18):
                marks.append([[x+offset, 49], [x+offset+4, 49]])
        else:
            marks.extend([[[x-1, 57], [x+5, 62], [x+15, 63]], [[x+2, 69], [x+13, 68], [x+20, 63]]])
    # Opposite hands: mirror the right-hand close-up, including its thumb.
    outlines = [[[390-x if x > 150 else x, y] for x,y in line] for line in outlines]
    marks = [[[390-x if x > 150 else x, y] for x,y in line] for line in marks]
    grips[kind] = dict(lines=outlines, marks=marks,
        title="PRONADA · palmas para longe de você" if kind == "pronated" else "SUPINADA · palmas voltadas para você",
        caption="Você vê o dorso das mãos" if kind == "pronated" else "Você vê as palmas das mãos")
data = dict(version=1, notice="Desenho simplificado, não avaliação da sua execução. Pare se houver dor e peça orientação para ajustar a técnica.", motions=motions, grips=grips, guides=guides)
for relative in ("assets/exercise_guides.json", "android-app/app/src/main/assets/exercise_guides.json", "android-app/app/src/test/resources/exercise_guides.json"):
    (ROOT / relative).write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf8")
print(f"{len(guides)} guides, {len(motions)} original vector diagrams; {len(json.dumps(data, ensure_ascii=False).encode('utf8'))} bytes")
