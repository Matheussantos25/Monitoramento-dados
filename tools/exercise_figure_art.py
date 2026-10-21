"""Original anatomical silhouettes, shared as compact vector keyframes.

No downloaded images. Limbs use two-bone IK while authoring; runtime only
interpolates nine lightweight vector keyframes. Coordinates are illustrative,
not motion capture, a physical assessment or a prescribed range of motion.
"""
from math import atan2, cos, sin, sqrt, pi, hypot

SKIN = "#d8a781"
SHADE = "#ad795e"
LIGHT = "#efc5a1"
SHIRT = "#65b6cf"
SHIRT_DARK = "#3a819f"
SHORTS = "#29435e"
SHOE = "#d9e8ee"
INK = "#183044"
STEEL = "#667d93"


def add(a, b): return (a[0]+b[0], a[1]+b[1])
def mix(a, b, t): return tuple(x+(y-x)*t for x,y in zip(a,b))


class Art:
    def __init__(self): self.shapes=[]; self.coords=[]
    def path(self, commands, points, fill="", stroke="", width=0):
        assert sum({"M":1,"L":1,"Q":2,"C":3,"Z":0}[c] for c in commands)==len(points),(commands,len(points))
        self.shapes.append(dict(kind="path",commands=commands,fill=fill,stroke=stroke,width=width))
        self.coords.append([round(v,2) for p in points for v in p])
    def ellipse(self, center, rx, ry, fill, stroke="", width=0):
        self.shapes.append(dict(kind="ellipse",commands="",fill=fill,stroke=stroke,width=width))
        self.coords.append([round(v,2) for v in (*center,rx,ry)])
    def line(self, points, color, width=2): self.path("M"+"L"*(len(points)-1),points,stroke=color,width=width)
    def limb(self,a,b,r1,r2,color):
        dx,dy=b[0]-a[0],b[1]-a[1]; length=max(hypot(dx,dy),.01)
        n=(-dy/length,dx/length)
        self.path("MLLLZ",[add(a,(n[0]*r1,n[1]*r1)),add(b,(n[0]*r2,n[1]*r2)),add(b,(-n[0]*r2,-n[1]*r2)),add(a,(-n[0]*r1,-n[1]*r1))],fill=color)
        self.ellipse(a,r1,r1,color); self.ellipse(b,r2,r2,color)
    def frozen(self): return [dict(shape=s,coords=c) for s,c in zip(self.shapes,self.coords)]


def elbow(a,b,l1=65,l2=62,bend=1):
    dx,dy=b[0]-a[0],b[1]-a[1]; d=max(.01,hypot(dx,dy))
    reach=min(d,l1+l2-.01)
    along=(l1*l1-l2*l2+reach*reach)/(2*reach)
    height=sqrt(max(0,l1*l1-along*along))
    return (a[0]+dx/d*along-dy/d*height*bend,a[1]+dy/d*along+dx/d*height*bend)


def face(art,h,front=True):
    x,y=h
    art.ellipse((x,y+3),16,22,SKIN)
    if front:
        art.ellipse((x-16,y+3),3,6,SHADE); art.ellipse((x+16,y+3),3,6,SHADE)
        art.path("MQQQQZ",[(x-16,y-4),(x-20,y-25),(x,y-24),(x+20,y-25),(x+16,y-2),(x+10,y-12),(x,y-6),(x-10,y-11),(x-16,y-4)],fill=INK)
        art.line([(x-8,y+2),(x-5,y+2)],INK,1.6); art.line([(x+5,y+2),(x+8,y+2)],INK,1.6)
        art.line([(x,y+5),(x-2,y+10),(x+1,y+11)],SHADE,1.3)
        art.path("MQ",[(x-4,y+16),(x,y+18),(x+4,y+16)],stroke=SHADE,width=1.3)
    else:
        # Profile faces right; a nose, ear, jaw and hair distinguish it from a dot.
        art.path("MLLLZ",[(x+12,y-3),(x+23,y+7),(x+15,y+10),(x+12,y+14)],fill=SKIN)
        art.ellipse((x-6,y+4),4,6,SHADE)
        art.path("MQQQQZ",[(x-15,y+7),(x-24,y-21),(x-3,y-24),(x+17,y-24),(x+15,y-8),(x+5,y-10),(x-7,y-4),(x-10,y+7),(x-15,y+7)],fill=INK)
        art.line([(x+10,y),(x+14,y)],INK,1.7)
        art.line([(x+13,y+15),(x+17,y+14)],SHADE,1.3)


def front_person(art, head, shoulder, hip, hands, feet, *, inverted=False, knees=None):
    x,y=shoulder; hx,hy=hip
    shoulders=[(x-31,y),(x+31,y)]
    hips=[(hx-16,hy),(hx+16,hy)]
    for index,(a,b) in enumerate(zip(hips,feet)):
        # In a frontal projection, knee flexion is mostly depth, not sideways.
        # Never solve that depth as inward elbows: it would cross the legs.
        k=knees[index] if knees else add(mix(a,b,.51),(-2 if index==0 else 2,0))
        art.limb(a,k,18,12,SKIN); art.limb(k,b,12,7,SKIN)
        art.line([add(k,(3,3)),add(b,(2,-9))],SHADE,2)
        art.ellipse(add(b,(-3 if index==0 else 3,6)),13,8,SHOE)
    # Neck, tapered torso, shoulder caps, waist and shorts are separate volumes.
    art.limb(add(head,(0,15)),(x,y+6),8,10,SKIN)
    art.path("MQLQLQQZ",[(x-10,y-9),(x-25,y-11),(x-35,y+3),(hx-22,hy-8),(hx,hy+3),(hx+22,hy-8),(x+35,y+3),(x+25,y-11),(x+10,y-9),(x,y+2),(x-10,y-9)],fill=SHIRT)
    art.path("MLLLLLLLLZ",[(hx-30,hy-18),(hx+30,hy-18),(hx+36,hy+8),(hx+30,hy+36),(hx+3,hy+36),(hx,hy+17),(hx-3,hy+36),(hx-30,hy+36),(hx-36,hy+8)],fill=SHORTS)
    art.line([(hx,hy-8),(hx,hy+15)],INK,2)
    art.path("MQ",[(x-26,y+20),(x-11,y+29),(x-2,y+23)],stroke=SHIRT_DARK,width=2)
    art.path("MQ",[(x+26,y+20),(x+11,y+29),(x+2,y+23)],stroke=SHIRT_DARK,width=2)
    art.line([(hx-14,hy-25),(hx+14,hy-25)],SHIRT_DARK,1.5)
    for i,(s,w) in enumerate(zip(shoulders,hands)):
        e=elbow(s,w,bend=-1 if i==0 else 1)
        art.limb(s,e,12,9,SKIN); art.limb(e,w,9,6,SKIN)
        art.line([mix(s,e,.25),mix(s,e,.75)],LIGHT,3)
        art.ellipse(s,14,14,SHIRT)
        art.ellipse(w,8,10,SKIN)
        art.line([add(w,(-3,-4)),add(w,(-3,4))],SHADE,1.4)
    face(art,head)
    if inverted:
        for shape,coords in zip(art.shapes,art.coords):
            if shape["kind"]=="ellipse": coords[1]=440-coords[1]
            else:
                for n in range(1,len(coords),2): coords[n]=440-coords[n]


def side_person(art,head,shoulder,hip,hand,knee,ankle,*,arm=None,other_leg=None,other_arm=None,head_pose="upright"):
    # Rear leg/arm are muted, so overlap still reads as a human body in profile.
    rear_k,rear_a=other_leg or (add(knee,(-9,-3)),add(ankle,(-10,-3)))
    rear_s=add(shoulder,(-5,-3)); rear_w=other_arm or add(hand,(-10,-3))
    rear_e=add(arm,(-6,-3)) if arm and not other_arm else elbow(rear_s,rear_w,60,57,-1)
    art.limb(add(hip,(-7,-3)),rear_k,17,11,SHADE); art.limb(rear_k,rear_a,11,7,SHADE)
    art.ellipse(add(rear_a,(9,3)),18,8,STEEL)
    art.limb(rear_s,rear_e,11,8,SHADE); art.limb(rear_e,rear_w,8,6,SHADE)
    art.ellipse(rear_w,7,8,SHADE)
    art.limb(hip,knee,20,12,SKIN); art.limb(knee,ankle,12,7,SKIN)
    art.line([mix(knee,ankle,.25),mix(knee,ankle,.8)],LIGHT,3)
    art.ellipse(add(ankle,(10,5)),19,8,SHOE)
    # Torso follows shoulder-to-hip direction, rather than a fixed vertical blob.
    dx,dy=hip[0]-shoulder[0],hip[1]-shoulder[1]; length=max(1,hypot(dx,dy))
    n=(-dy/length,dx/length)
    def offset(p,d): return add(p,(n[0]*d,n[1]*d))
    art.limb(add(head,(0,18) if head_pose=="upright" else (18,0)),shoulder,8,11,SKIN)
    art.path("MQQQQZ",[offset(shoulder,19),offset(mix(shoulder,hip,.35),25),offset(hip,18),offset(hip,27),offset(hip,-19),offset(mix(shoulder,hip,.4),-21),offset(shoulder,-23),offset(shoulder,-27),offset(shoulder,19)],fill=SHIRT)
    art.limb(hip,mix(hip,knee,.36),22,19,SHORTS)
    art.path("MQ",[offset(mix(shoulder,hip,.2),-15),offset(mix(shoulder,hip,.6),-13),offset(mix(shoulder,hip,.88),-15)],stroke=SHIRT_DARK,width=3)
    e=arm or elbow(shoulder,hand,60,57,-1)
    art.limb(shoulder,e,12,9,SKIN); art.limb(e,hand,9,6,SKIN)
    art.line([mix(shoulder,e,.2),mix(shoulder,e,.75)],LIGHT,3)
    art.ellipse(shoulder,14,14,SHIRT); art.ellipse(hand,8,8,SKIN)
    head_art=Art(); face(head_art,head,False)
    if head_pose != "upright":
        for shape, coords in zip(head_art.shapes,head_art.coords):
            end=2 if shape["kind"]=="ellipse" else len(coords)
            for i in range(0,end,2):
                dx,dy=coords[i]-head[0],coords[i+1]-head[1]
                if head_pose=="down": dx=-dx
                coords[i],coords[i+1]=round(head[0]+dy,2),round(head[1]-dx,2)
            if shape["kind"]=="ellipse": coords[2],coords[3]=coords[3],coords[2]
    art.shapes.extend(head_art.shapes); art.coords.extend(head_art.coords)


def compile_motion(fn,static=None,moving=True,direction="",landmarks=None):
    drawings=[]
    for i in range(9 if moving else 1):
        a=Art(); fn(a,i/8 if moving else 0); drawings.append(a)
    shapes=drawings[0].shapes
    assert all(a.shapes==shapes for a in drawings),"Animation topology must stay fixed"
    assert all([len(c) for c in a.coords]==[len(c) for c in drawings[0].coords] for a in drawings)
    return dict(shapes=shapes,frames=[a.coords for a in drawings],static=(static or Art()).frozen(),direction=direction,landmarks=landmarks or [])


def equipment(*lines):
    a=Art()
    a.ellipse((220,415),105,7,"#15263a")
    for line in lines: a.line(line,STEEL,7)
    return a


def build_motions():
    motions={}
    for key,spacing in (("pull_pronated",76),("pull_supinated",43)):
        def pull(a,t,spacing=spacing):
            y=105*t
            front_person(a,(220,134-y),(220,168-y),(220,258-y),[(220-spacing,51),(220+spacing,51)],[(202,410-y),(238,410-y)])
        motions[key]=compile_motion(pull,equipment([(90,51),(350,51)],[(94,51),(94,25)],[(346,51),(346,25)]),direction="Suba sem balanço · desça com controle",landmarks=["Mãos fixas na barra", "Cotovelos descem ao subir"])
    def squat(a,t):
        hip=mix((197,239),(160,308),t); s=mix((202,142),(219,219),t)
        knee=mix((209,319),(256,315),t)
        side_person(a,add(s,(0,-33)),s,hip,add(s,(116,5)),knee,(244,399),arm=add(s,(58,3)))
    motions["squat"]=compile_motion(squat,equipment([(100,414),(340,414)]),direction="Quadril para trás e para baixo",landmarks=["Pés apoiados", "Joelhos acompanham os pés"])
    def push(a,t):
        s=mix((122,263),(122,345),t); hip=mix((242,307),(242,356),t)
        side_person(a,add(s,(-34,-4)),s,hip,(120,401),mix(hip,(387,395),.5),(387,395),arm=elbow(s,(120,401),73,68,-1),head_pose="down")
    motions["pushup"]=compile_motion(push,equipment([(53,414),(411,414)]),direction="Peito aproxima do chão · corpo alinhado",landmarks=["Mãos permanecem apoiadas", "Tronco e quadril descem juntos"])
    motions["plank"]=compile_motion(lambda a,t:side_person(a,(78,298),(113,308),(240,336),(65,401),(315,366),(387,395),arm=(113,400),head_pose="down"),equipment([(43,414),(413,414)]),False,direction="Sustente a posição e continue respirando")
    def legraise(a,t):
        angle=(20+65*t)*pi/180; hip=(220,394)
        knee=(hip[0]+82*cos(angle),hip[1]-82*sin(angle)); ankle=(hip[0]+157*cos(angle),hip[1]-157*sin(angle))
        side_person(a,(63,393),(100,394),hip,(168,402),knee,ankle,arm=(115,402),head_pose="up")
    motions["legraise"]=compile_motion(legraise,equipment([(40,414),(406,414)]),direction="Eleve as pernas · desça sem arquear a lombar",landmarks=["Tronco apoiado", "Movimento vem do quadril"])
    def standingrow(a,t):
        hand=mix((292,221),(195,221),t)
        a.line([hand,(393,221)],STEEL,3)
        side_person(a,(157,90),(159,123),(155,228),hand,(146,309),(134,399),other_leg=((192,307),(226,399)))
        a.line([add(hand,(0,-12)),add(hand,(0,12))],SHOE,5)
    motions["standingrow"]=compile_motion(standingrow,equipment([(393,56),(393,414)]),direction="Puxada horizontal ao abdômen",landmarks=["Tronco permanece estável", "Não é uma remada alta"])
    def row(a,t):
        hand=mix((297,221),(199,229),t); a.line([hand,(393,214)],STEEL,3)
        side_person(a,(164,90),(165,124),(171,234),hand,(271,259),(326,347))
        a.line([add(hand,(0,-10)),add(hand,(0,10))],SHOE,5)
    motions["row"]=compile_motion(row,equipment([(132,258),(207,258)],[(146,258),(146,405)],[(313,372),(346,328)],[(393,85),(393,405)]),direction="Puxe ao abdômen · retorne controlando")
    def lat(a,t):
        hand_y=62+129*t
        front_person(a,(220,149),(220,182),(220,270),[(144,hand_y),(296,hand_y)],[(190,408),(250,408)],knees=[(190,320),(250,320)])
        a.line([(124,hand_y),(316,hand_y)],SHOE,7); a.line([(220,30),(220,hand_y)],STEEL,2)
    motions["lat"]=compile_motion(lat,equipment([(75,405),(75,30),(365,30),(365,405)],[(183,291),(257,291)],[(195,291),(195,402)]),direction="Barra desce à frente do peito",landmarks=["Não puxe atrás da nuca"])
    for key in ("jump","rope"):
        def jumping(a,t):
            lift=28*t
            front_person(a,(220,93-lift),(220,126-lift),(220,217-lift),[(145,239-lift),(295,239-lift)],[(199,371-lift),(241,371-lift)])
        base=equipment([(115,414),(325,414)])
        if key=="rope": base.path("MQQ",[(140,237),(72,425),(220,419),(368,425),(300,237)],stroke="#b8cddb",width=3)
        motions[key]=compile_motion(jumping,base,direction="Salto baixo · aterrissagem suave")
    # Static gait/cycling references avoid teaching an artificial two-pose gait.
    motions["walk"]=compile_motion(lambda a,t:side_person(a,(219,65),(217,98),(208,201),(155,178),(172,296),(144,393),other_leg=((258,282),(300,392)),other_arm=(275,172)),equipment(),False,direction="Postura de referência · passada confortável")
    motions["run"]=compile_motion(lambda a,t:side_person(a,(248,75),(235,110),(209,207),(310,140),(289,255),(258,339),arm=(275,180),other_leg=((159,286),(99,256)),other_arm=(151,157)),equipment(),False,direction="Postura de referência · ritmo confortável")
    base=equipment([(110,342),(185,231),(245,342),(110,342)],[(245,342),(340,342),(310,203),(347,192)],[(169,231),(206,231)])
    for center in ((110,342),(340,342)):base.ellipse(center,62,62,"",STEEL,5)
    motions["bike"]=compile_motion(lambda a,t:side_person(a,(283,100),(266,134),(188,221),(331,199),(256,265),(228,355),other_leg=((177,286),(251,314))),base,False,direction="Postura ilustrativa · ajuste a bicicleta ao seu corpo")
    def stairs(a,t):
        shift=(28*t,-43*t); s=add((178,121),shift); hip=add((168,219),shift)
        front_ankle=(253,346); front_knee=elbow(hip,front_ankle,80,78,-1)
        side_person(a,add(s,(0,-34)),s,hip,add((245,160),shift),front_knee,front_ankle,arm=add((200,170),shift),other_leg=(add((151,308),shift),add((133,399),shift)))
    motions["stairs"]=compile_motion(stairs,equipment([(74,414),(214,414),(214,357),(327,357),(327,300),(403,300)]),direction="Transfira o peso para o pé no degrau")
    motions["lsit"]=compile_motion(lambda a,t:side_person(a,(147,85),(148,121),(154,222),(134,239),(249,222),(343,222),arm=(141,179)),equipment([(101,249),(170,249)],[(111,249),(111,409)],[(160,249),(160,409)]),False,direction="Posição final · habilidade avançada")
    motions["handstand"]=compile_motion(lambda a,t:front_person(a,(220,123),(220,157),(220,247),[(189,30),(251,30)],[(204,403),(236,403)],inverted=True),equipment([(342,27),(342,414)]),False,direction="Posição final · entrada e saída exigem orientação")
    return motions


def build_grips():
    grips={}
    for kind in ("pronated","supinated"):
        a=Art()
        a.line([(34,58),(326,58)],STEEL,14)
        # One left hand, reflected for the right: rounded palm, four separate
        # wrapped fingers, thumb enclosing the bar; dorsal nails vs palm creases.
        for origin,mirror in ((101,False),(259,True)):
            hand=Art()
            hand.path("MQLQQQLQZ",[(-16,153),(-16,135),(-20,119),(-30,94),(-35,79),(-28,62),(-19,55),(21,55),(28,64),(29,87),(21,116),(16,135),(16,153)],fill=SKIN,stroke=SHADE,width=1.5)
            for i in range(4):
                x=-23+i*12
                hand.path("MQQQQQZ",[(x,80),(x-5,68),(x-4,56),(x-3,47),(x+3,47),(x+9,48),(x+8,59),(x+7,69),(x+6,79),(x+2,84),(x,80)],fill=LIGHT if kind=="supinated" else SKIN,stroke=SHADE,width=1.2)
                if kind=="pronated":hand.path("MQ",[(x-1,61),(x+3,58),(x+6,61)],stroke=LIGHT,width=1.5)
                else:hand.line([(x,70),(x+5,71)],SHADE,1.1)
            hand.path("MQQQQZ",[(25,78),(38,83),(29,94),(12,110),(2,101),(-2,94),(9,90),(17,82),(25,78)],fill=SKIN,stroke=SHADE,width=1.4)
            if kind=="supinated":
                hand.path("MQQ",[(-23,91),(-8,105),(11,104),(18,115),(7,124)],stroke=SHADE,width=1.6)
                hand.path("MQ",[(-18,126),(-2,119),(8,126)],stroke=SHADE,width=1.4)
            else:
                for x in (-13,0,12):hand.path("MQ",[(x,92),(x-3,112),(x*.7,129)],stroke=LIGHT,width=1.3)
            for shape,coords in zip(hand.shapes,hand.coords):
                transformed=list(coords)
                for i in range(0,len(coords),2):transformed[i]=origin+(-coords[i] if mirror else coords[i])
                a.shapes.append(shape);a.coords.append(transformed)
        grips[kind]=dict(title="Pronada" if kind=="pronated" else "Supinada",caption="Dorso das mãos visível para você" if kind=="pronated" else "Palmas das mãos voltadas para você",instruction="Palmas apontam para longe do rosto" if kind=="pronated" else "Palmas apontam para o seu rosto",shapes=a.frozen())
    return grips
