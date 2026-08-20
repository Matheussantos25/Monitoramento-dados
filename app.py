import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import random
import base64
import streamlit.components.v1 as components

# --- FUNÇÕES AUXILIARES DE SEGURANÇA ---
def safe_get(val, key, default=None):
    if val is None or val == "": return default
    if isinstance(val, float) and pd.isna(val): return default
    if isinstance(val, str):
        try: val = json.loads(val)
        except: return default
    if isinstance(val, dict): return val.get(key, default)
    return default

# --- DICIONÁRIOS PRESETADOS ---
EXERCICIOS_PRESETADOS = {
    "Abdominal": ["Abdominal Levantada", "Prancha"],
    "Bíceps": ["Barra Fixa (Supinada)"],
    "Cardio": ["Bike", "Caminhada", "Corrida", "Pular Corda", "Pular Normal", "Subida Escada (Andares)"],
    "Costas": [
        "Barra Fixa (Pronada)", 
        "Puxada Alta", 
        "Remada Baixa", 
        "Remada em Pé na Polia", 
        "Remada em Pé na Polia com barra"
    ],
    "Peitoral": ["Flexão"],
    "Pernas": ["Agachamento"],
    "Rosto": ["Massagem Facial", "Mewing com borracha"],
    "Skills / Calistenia": ["Handstand (Parada de Mãos)", "L-Sit"]
}

TODOS_EXERCICIOS = [ex for lista in EXERCICIOS_PRESETADOS.values() for ex in lista]
TODOS_EXERCICIOS.sort()

ALIMENTOS_SAUDAVEIS = ["Banana", "Uva", "Maçã", "Laranja", "Melão", "Melancia", "Mirtilo", "Ovo", "Frango", "Aveia", "Whey"]
ALIMENTOS_SAUDAVEIS.sort()

ALIMENTOS_BESTEIROL = ["Refrigerante", "Hambúrguer", "Pizza", "Lasanha", "Churros", "Pastel", "Coxinha", "Sorvete", "Batata Frita", "Sonho de Valsa", "Biscoito Recheado", "Chocotone"]
ALIMENTOS_BESTEIROL.sort()

DISCIPLINAS_ESTUDO = [
    "Atualidades e IA", 
    "Banco de Dados (SQL/NoSQL/Big Data)", 
    "Ciência de Dados (ML/DL/PLN/Visão)", 
    "Legislação (LAI/Marco Civil/LGPD)",
    "Linguagens (Python/R/Spark/SAS)",
    "Língua Inglesa", 
    "Língua Portuguesa", 
    "Matemática e Estatística Aplicada", 
    "Raciocínio Lógico", 
    "TCC", 
    "Outro"
]
DISCIPLINAS_ESTUDO.sort()

DECKS_ANKI = [
    "Atualidades",
    "Conhecimentos Específicos",
    "Erros Simulados com IA",
    "Inglês",
    "Legislação",
    "Língua Portuguesa",
    "Raciocínio Lógico"
]

FONTES_QUESTOES = [
    "FGV",
    "Gerado por IA",
    "IA (Estilo FGV)",
    "CEBRASPE",
    "VUNESP",
    "FCC",
    "QConcursos / TEC",
    "Anki",
    "Outra"
]

TOPICOS_EDITAL = {
    "Matemática e Estatística Aplicada": [
        "I.1 Cálculo: funções, limites, derivadas, derivadas parciais, máximos e mínimos, integrais",
        "I.2 Álgebra linear: vetores, matrizes, produto escalar/vetorial, matriz identidade/inversa/transposta, transformações lineares, normas L1/L2, autovalores e autovetores",
        "II.1 Probabilidade: modelo, probabilidade condicional, independência, variáveis aleatórias, esperança/variância/covariância, distribuições contínuas e discretas, distribuições multidimensionais",
        "II.2 Estatística descritiva: Teorema do Limite Central, teste de hipótese e intervalo de confiança, máxima verossimilhança, inferência bayesiana, correlação de Pearson, boxplot e outliers",
    ],
    "Ciência de Dados (ML/DL/PLN/Visão)": [
        "1 Aprendizado supervisionado: regressão, classificação, métricas, overfitting/underfitting, regularização, validação cruzada, viés-variância, regressão linear/logística, árvores/random forest, SVM, K-NN",
        "2 Aprendizado não supervisionado: PCA, K-Means, mistura de Gaussianas, regras de associação",
        "3 Redes neurais artificiais: arquitetura, funções de ativação, gradiente/SGD/backpropagation, regularização L1/L2, CNN",
        "4 Machine Learning aplicado: visão computacional com CNN, classificação/detecção de imagens, noções de PLN",
        "5 ETL",
        "6 Manipulação, tratamento e visualização de dados",
        "7.1 Análise de dados (Pandas, NumPy, Jupyter, R)",
        "7.2 Aprendizado de máquina: classificação, regressão, agrupamento, redução de dimensionalidade, associação, sistemas de recomendação",
        "8 Processamento de linguagem natural (PLN)",
        "9 Visão computacional",
        "10 Deep learning",
        "11 Mineração de dados",
        "12 Ferramenta SAS",
    ],
    "Linguagens (Python/R/Spark/SAS)": [
        "1 Python e bibliotecas: NumPy, Matplotlib, Seaborn, Streamlit, Pandas, SciPy, TensorFlow, Keras, PyTorch",
        "2 R e suas bibliotecas",
        "3 Apache Hadoop e Apache Spark",
    ],
    "Banco de Dados (SQL/NoSQL/Big Data)": [
        "1 Modelagem de dados (conceitual, lógica e física)",
        "2 Abordagem relacional",
        "3 Normalização das estruturas de dados",
        "4 Integridade referencial",
        "5 Metadados",
        "6 Modelagem dimensional",
        "7 Linguagem de consulta estruturada (SQL)",
        "8 Linguagem de definição de dados (DDL)",
        "9 Linguagem de manipulação de dados (DML)",
        "10 SGBD",
        "11 Propriedades de banco de dados",
        "12 Banco de dados NoSQL",
        "13 Banco de dados em memória",
        "14 Data lakes e soluções para big data",
    ],
    "Língua Portuguesa": [
        "1 Compreensão e interpretação de textos",
        "2 Tipos e gêneros textuais",
        "3 Ortografia oficial",
        "4.1 Coesão: referenciação, substituição, repetição, conectores",
        "4.2 Emprego de tempos e modos verbais",
        "5.1 Classes de palavras",
        "5.2 Coordenação entre orações e termos",
        "5.3 Subordinação entre orações e termos",
        "5.4 Sinais de pontuação",
        "5.5 Concordância verbal e nominal",
        "5.6 Regência verbal e nominal",
        "5.7 Emprego do sinal indicativo de crase",
        "5.8 Colocação dos pronomes átonos",
        "6.1 Significação das palavras",
        "6.2 Substituição de palavras/trechos de texto",
        "6.3 Reorganização da structure de orações e períodos",
        "6.4 Reescrita de textos (gêneros e formalidade)",
    ],
    "Língua Inglesa": [
        "1 Compreensão de textos em língua inglesa e itens gramaticais relevantes",
    ],
    "Raciocínio Lógico": [
        "1 Estruturas lógicas",
        "2 Lógica de argumentação: analogias, inferências, deduções e conclusões",
        "3.1 Proposições simples e compostas",
        "3.2 Tabelas-verdade",
        "3.3 Equivalências",
        "3.4 Diagramas lógicos",
        "4 Lógica de primeira ordem",
        "5 Problemas aritméticos, geométricos e matriciais",
    ],
    "Atualidades e IA": [
        "1 Tópicos atuais: segurança, transportes, política, economia, sociedade, educação, saúde, cultura, tecnologia, energia, relações internacionais, sustentabilidade e ecologia",
        "2 IA: fundamentos, aplicações e aprendizado de máquina; modelos generativos e de linguagem",
        "2.1 Ética, governança e privacidade em IA",
    ],
    "Legislação (LAI/Marco Civil/LGPD)": [
        "1 Lei nº 12.527/2011 (LAI) — Cap. I, II, III, IV e V; Dec. nº 7.724 e nº 7.845",
        "2 Lei nº 12.737/2012 (Delitos Informáticos) — Art. 2º",
        "3 Lei nº 12.965/2014 (Marco Civil da Internet) — Cap. II Seção I e Cap. III Seções I e II",
        "4 Lei nº 13.709/2018 (LGPD) — Cap. I, II, III, IV, VII e VIII",
    ],
    "TCC": [
        "Definição do tema",
        "Revisão bibliográfica",
        "Metodologia",
        "Desenvolvimento",
        "Redação final",
        "Defesa",
    ],
    "Outro": [
        "Geral",
    ],
}

ROTA_ESTRATEGICA = [
    "Banco de Dados (SQL/NoSQL/Big Data)", 
    "Raciocínio Lógico", 
    "Ciência de Dados (ML/DL/PLN/Visão)", 
    "Legislação (LAI/Marco Civil/LGPD)",
    "Atualidades e IA", 
    "Linguagens (Python/R/Spark/SAS)", 
    "Língua Inglesa" 
]

PESOS_DISCIPLINA = {
    "Ciência de Dados (ML/DL/PLN/Visão)": 30,
    "Matemática e Estatística Aplicada": 20,
    "Banco de Dados (SQL/NoSQL/Big Data)": 15,
    "Linguagens (Python/R/Spark/SAS)": 10,
    "Língua Portuguesa": 8,
    "Raciocínio Lógico": 6,
    "Legislação (LAI/Marco Civil/LGPD)": 6,
    "Atualidades e IA": 3,
    "Língua Inglesa": 2,
}


# ==========================================
# FUNÇÃO INTELIGENTE DE RECOMENDAÇÃO (COM PESO POR TEMPO)
# ==========================================
def obter_pior_topico(df_hist, disciplina):
    todos_topicos = [t for t in TOPICOS_EDITAL.get(disciplina, ["Geral"]) if "Simulado" not in t]
    if not todos_topicos: return "Geral"
    if df_hist.empty: return todos_topicos[0]
    df_disc = df_hist[df_hist['exercicio'] == disciplina].copy()
    if df_disc.empty: return todos_topicos[0]
    
    df_disc['q_certas'] = df_disc['dados_extras'].apply(lambda x: safe_get(x, 'q_certas', 0))
    df_disc['q_erradas'] = df_disc['dados_extras'].apply(lambda x: safe_get(x, 'q_erradas', 0))
    df_disc['topicos_str'] = df_disc['dados_extras'].apply(lambda x: safe_get(x, 'topico_edital', ''))
    
    df_disc['data_sessao'] = pd.to_datetime(df_disc['data'])
    hoje = (pd.Timestamp.utcnow() - pd.Timedelta(hours=3)).normalize().tz_localize(None)
    df_disc['dias_atras'] = (hoje - df_disc['data_sessao']).dt.days
    df_disc['dias_atras'] = df_disc['dias_atras'].apply(lambda x: max(0, x))
    df_disc['peso_tempo'] = 0.5 ** (df_disc['dias_atras'] / 7.0)
    df_disc['certas_pond'] = df_disc['q_certas'] * df_disc['peso_tempo']
    df_disc['total_pond'] = (df_disc['q_certas'] + df_disc['q_erradas']) * df_disc['peso_tempo']

    registros_expandidos = []
    for _, row in df_disc.iterrows():
        topicos_lista = [t.strip() for t in row['topicos_str'].split(',')] if row['topicos_str'] else ["Geral"]
        for t in topicos_lista:
            registros_expandidos.append({
                'topico': t, 'certas_pond': row['certas_pond'], 'total_pond': row['total_pond']
            })
            
    if not registros_expandidos: return todos_topicos[0]
    df_exp = pd.DataFrame(registros_expandidos)
    stats = df_exp.groupby('topico')[['certas_pond', 'total_pond']].sum().reset_index()
    topicos_estudados = set(stats['topico'].tolist())
        
    topicos_nao_estudados = [t for t in todos_topicos if t not in topicos_estudados]
    if topicos_nao_estudados: return topicos_nao_estudados[0]
        
    stats = stats[stats['total_pond'] > 0]
    if not stats.empty:
        stats['acc'] = stats['certas_pond'] / stats['total_pond']
        stats = stats.sort_values('acc', ascending=True)
        for pior_topico in stats['topico']:
            if pior_topico in todos_topicos: return pior_topico
                
    return todos_topicos[0]


# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Monitoramento Físico & Mental", page_icon="⚡", layout="wide")

# --- INJEÇÃO DE CSS PREMIUM (DARK CLEAN) ---
st.markdown("""
<style>
    .stApp { background-color: #050505 !important; }
    h1, h2, h3, h4, p, label, span, .stMarkdown { color: #E0E0E0 !important; }
    
    .stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input, .stTimeInput input, [data-baseweb="select"] > div {
        background-color: #121212 !important;
        color: #009CA6 !important;
        border: 1px solid #1F1F1F !important;
        border-radius: 6px !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus { border-color: #009CA6 !important; }

    [data-testid="stForm"], div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: #0D0D0D !important;
        border: 1px solid #1A1A1A !important;
        border-radius: 10px !important;
        padding: 24px !important;
    }

    /* === CARTÕES CUSTOMIZADOS DARK CLEAN === */
    .card-container { display: flex; gap: 15px; justify-content: space-between; margin-bottom: 25px; flex-wrap: wrap; }
    .neon-card { flex: 1; min-width: 150px; padding: 20px; border-radius: 10px; color: #E0E0E0; background: #0A0A0A; border-left: 4px solid #333; position: relative; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
    .neon-card .card-title { font-size: 13px; font-weight: 500; text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.7; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;}
    .neon-card .card-value { font-size: 32px; font-weight: 700; color: #FFF; }
    
    .card-cyan { border-color: #009CA6; }
    .card-cyan .card-value { text-shadow: 0 0 10px rgba(0, 156, 166, 0.4); }
    
    .card-emerald { border-color: #10B981; }
    .card-emerald .card-value { text-shadow: 0 0 10px rgba(16, 185, 129, 0.4); }
    
    .card-violet { border-color: #8B5CF6; }
    .card-violet .card-value { text-shadow: 0 0 10px rgba(139, 92, 246, 0.4); }
    
    .card-crimson { border-color: #F43F5E; }
    .card-crimson .card-value { text-shadow: 0 0 10px rgba(244, 63, 94, 0.4); }

    .card-orange { border-color: #F59E0B; }
    .card-orange .card-value { text-shadow: 0 0 10px rgba(245, 158, 11, 0.4); }
    
    span[data-baseweb="tag"] { background-color: #009CA6 !important; color: #050505 !important; font-weight: bold; }
    
    hr { border-color: #1F1F1F !important; }
</style>
""", unsafe_allow_html=True)

# --- BANCO DE DADOS ---
@st.cache_resource
def init_connection() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

def fetch_data():
    response = supabase.table("treinos").select("*").execute()
    return pd.DataFrame(response.data)

df_raw = fetch_data()

# --- FILTROS NA SIDEBAR ---
st.sidebar.markdown("## 🔍 Filtros Gerais")
st.sidebar.write("---")

filtro_tempo = st.sidebar.selectbox("Período:", ["Todo o Histórico", "Hoje", "Últimos 7 Dias", "Últimos 30 Dias", "Este Ano"])

if not df_raw.empty:
    df_raw['data'] = pd.to_datetime(df_raw['data'])
    # Correção UTC-3
    hoje = (pd.Timestamp.utcnow() - pd.Timedelta(hours=3)).normalize().tz_localize(None)
    
    if filtro_tempo == "Hoje": df_raw = df_raw[df_raw['data'] == hoje]
    elif filtro_tempo == "Últimos 7 Dias": df_raw = df_raw[df_raw['data'] >= (hoje - pd.Timedelta(days=7))]
    elif filtro_tempo == "Últimos 30 Dias": df_raw = df_raw[df_raw['data'] >= (hoje - pd.Timedelta(days=30))]
    elif filtro_tempo == "Este Ano": df_raw = df_raw[df_raw['data'].dt.year == hoje.year]

if not df_raw.empty:
    df_treinos = df_raw[~df_raw['grupo_muscular'].isin(['Nutrição', 'Métricas', 'Estudos'])].copy()
    df_dieta = df_raw[df_raw['grupo_muscular'] == 'Nutrição'].copy()
    df_estudos = df_raw[df_raw['grupo_muscular'] == 'Estudos'].copy()
else:
    df_treinos = pd.DataFrame()
    df_dieta = pd.DataFrame()
    df_estudos = pd.DataFrame()

# --- INTERFACE MAIN ---
st.markdown("<h1 style='text-align: center; font-weight: 800; letter-spacing: -1px; color: #FFF;'>Sistema Solem</h1>", unsafe_allow_html=True)
if filtro_tempo != "Todo o Histórico":
    st.markdown(f"<p style='text-align: center; color: #009CA6; margin-top: -15px;'>[ Período Ativo: {filtro_tempo} ]</p>", unsafe_allow_html=True)
st.write("")

# Abas sem o Modo Flow
tab_registro, tab_dash_treino, tab_dieta, tab_peso, tab_estudo, tab_dash_estudo, tab_cruzamento, tab_gerenciar = st.tabs([
    "📝 Treino", "📊 Dash Físico", "🥗 Dieta", "⚖️ Peso", "📚 Estudar", "📈 Dash Estudos", "🧬 Cruzamentos", "⚙️ Config"
])

# ==========================================
# ABA 1: REGISTRO DE TREINO 
# ==========================================
with tab_registro:
    modo_insercao = st.radio("Selecione o formato do treino:", ["🏋️ Exercício Isolado (Convencional)", "🔥 Circuito AMRAP 20' (5 Barras / 10 Flexões / 15 Agachamentos)"], horizontal=True)
    if modo_insercao == "🏋️ Exercício Isolado (Convencional)":
        with st.form("registro_treino", clear_on_submit=True):
            st.markdown("<h3 style='margin-bottom: 20px; color: #009CA6;'>🏋️ Inserir Dados Físicos</h3>", unsafe_allow_html=True)
            c_top1, c_top2, c_top3 = st.columns([2, 1, 1])
            with c_top1: data_treino = st.date_input("Data do Treino", value=(datetime.utcnow() - timedelta(hours=3)).date())
            agora = datetime.utcnow() - timedelta(hours=3)
            with c_top2: hora = st.selectbox("Hora", [f"{i:02d}" for i in range(24)], index=agora.hour)
            with c_top3: minuto = st.selectbox("Min.", [f"{i:02d}" for i in range(60)], index=agora.minute)
            horario = f"{hora}:{minuto}:00"
            st.markdown("---")
            exercicio_input = st.selectbox("Exercício", TODOS_EXERCICIOS)
            
            if not df_treinos.empty:
                df_hist_ex = df_treinos[df_treinos['exercicio'] == exercicio_input].sort_values(by=['data', 'horario'])
                if not df_hist_ex.empty:
                    ult = df_hist_ex.iloc[-1]
                    reps_u = int(ult['repeticoes'])
                    carga_u = float(ult['carga_kg'])
                    desc_u = int(ult['descanso_seg'])
                    iso_u = int(safe_get(ult['dados_extras'], 'isometria_segundos', 0))

                    sugestao = ""
                    if iso_u > 0: sugestao = f"Tente segurar {iso_u + 2}s a {iso_u + 5}s (Progressão Isométrica)."
                    elif reps_u > 0: sugestao = f"Tente {reps_u + 1} a {reps_u + 2} reps, ou aumente a carga para {carga_u + 1}kg."
                    else: sugestao = "Mantenha o ritmo e otimize o movimento."
                    
                    html_overload = (
                        '<div style="background-color: #121212; border-left: 3px solid #009CA6; padding: 10px; border-radius: 5px; margin-top: 5px; margin-bottom: 20px;">'
                        f'<span style="color: #AAA; font-size: 12px;">ÚLTIMO TREINO: {reps_u} reps | {iso_u}s isometria | {carga_u}kg | {desc_u}s descanso</span><br>'
                        f'<span style="color: #009CA6; font-size: 14px; font-weight: bold;">⚡ Sugestão de Overload: {sugestao} Reduza o descanso para {max(0, desc_u - 15)}s se estiver fácil.</span>'
                        '</div>'
                    )
                    st.markdown(html_overload, unsafe_allow_html=True)
            
            st.markdown("#### 📊 Métricas do Exercício")
            c1, c2, c3 = st.columns(3)
            with c1:
                series = st.number_input("Séries / Tentativas", min_value=0, value=1, step=1)
                reps = st.number_input("Repetições (Total)", min_value=0, step=1)
                carga = st.number_input("Carga (kg)", min_value=0.0)
            with c2:
                isometria_segundos = st.number_input("Isometria: Tempo Sustentado (seg)", min_value=0, step=1)
                intervalo = st.number_input("Intervalo de Descanso (seg)", min_value=0, step=15)
            with c3:
                duracao = st.number_input("Cardio: Duração (min)", min_value=0)
                distancia = st.number_input("Cardio: Distância (km)", min_value=0.0)
                
            isometria_tentativas = series  
            st.markdown("---")
            humor = st.selectbox("Estado Mental no Treino", ["Normal", "Foco Extremo", "Motivado", "Cansado", "Estressado"])
            
            if st.form_submit_button("🚀 Gravar Treino", use_container_width=True):
                grupo = next((g for g, l in EXERCICIOS_PRESETADOS.items() if exercicio_input in l), "Outro")
                mochila_json = {"humor": humor, "isometria_tentativas": isometria_tentativas, "isometria_segundos": isometria_segundos}
                dados = {
                    "data": str(data_treino), "horario": str(horario), "grupo_muscular": grupo,
                    "exercicio": exercicio_input, "series": int(series), "repeticoes": int(reps),
                    "carga_kg": float(carga), "descanso_seg": int(intervalo), "duracao_min": int(duracao),
                    "distancia_km": float(distancia), "alimentacao_saudavel": "", "alimentacao_besteirol": "",
                    "peso_corporal": 0.0, "dados_extras": mochila_json 
                }
                supabase.table("treinos").insert(dados).execute()
                st.success("Dados físicos processados e salvos!")
                st.rerun()

    else:
        st.markdown("<h3 style='margin-bottom: 5px; color: #F43F5E;'>🔥 Circuito AMRAP (20 Minutos)</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color: #AAA; margin-bottom: 20px;'>1 Round = 5 Barras Fixas + 10 Flexões + 15 Agachamentos</p>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("##### ⏱️ Cronômetro do Circuito (20:00)")
            html_timer_amrap = """
            <!DOCTYPE html><html><head><style>
                    body { background-color: transparent; color: #E0E0E0; font-family: sans-serif; text-align: center; margin: 0; padding: 0; }
                    .time { font-size: 68px; color: #F43F5E; text-shadow: 0 0 15px rgba(244,63,94,0.5); font-weight: bold; margin: 10px 0 15px 0; transition: color 0.3s; }
                    .time.done { color: #10B981; text-shadow: 0 0 20px rgba(16,185,129,0.6); animation: pulseAmrap 1s infinite; }
                    @keyframes pulseAmrap { 0% { opacity: 1; } 50% { opacity: 0.35; } 100% { opacity: 1; } }
                    .btn-group { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
                    .btn { padding: 10px 20px; background-color: #0A0A0A; color: #F43F5E; border: 2px solid #F43F5E; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: bold; transition: all 0.3s; }
                    .btn:hover { background-color: #F43F5E; color: #000; box-shadow: 0 0 10px rgba(244,63,94,0.5); }
                    .status { color: #AAA; font-size: 13px; margin-top: 12px; min-height: 18px; }
            </style></head><body>
                <div class="time" id="display_amrap">20:00</div>
                <div class="btn-group">
                    <button class="btn" onclick="startAmrap()">▶️ Iniciar</button>
                    <button class="btn" onclick="pauseAmrap()">⏸️ Pausar</button>
                    <button class="btn" onclick="resetAmrap()">🔄 Reiniciar</button>
                </div>
                <div class="status" id="status_amrap"></div>
                <script>
                    var TOTAL_AMRAP = 20 * 60; var secsLeftAmrap = TOTAL_AMRAP; var runningAmrap = false; var timerAmrapHandle;
                    var displayAmrap = document.getElementById('display_amrap'); var statusAmrap = document.getElementById('status_amrap');
                    function formatTimeAmrap(s) { var m = Math.floor(s / 60); var rs = s % 60; return (m < 10 ? '0' : '') + m + ':' + (rs < 10 ? '0' : '') + rs; }
                    function beepAmrap() { try { var ctx = new (window.AudioContext || window.webkitAudioContext)(); for (var i = 0; i < 3; i++) { (function(i){ var o = ctx.createOscillator(); var g = ctx.createGain(); o.connect(g); g.connect(ctx.destination); o.type = 'sine'; o.frequency.value = 880; g.gain.setValueAtTime(0.3, ctx.currentTime + i * 0.4); o.start(ctx.currentTime + i * 0.4); o.stop(ctx.currentTime + i * 0.4 + 0.3); })(i); } } catch(e) {} }
                    function startAmrap() { if (runningAmrap || secsLeftAmrap <= 0) return; runningAmrap = true; statusAmrap.innerText = "Cronômetro rodando... bora!";
                        timerAmrapHandle = setInterval(function() { secsLeftAmrap--; if (secsLeftAmrap <= 0) { secsLeftAmrap = 0; displayAmrap.innerText = "FIM!"; displayAmrap.classList.add('done'); statusAmrap.innerText = "⏰ 20 minutos encerrados. Anote seus rounds!"; clearInterval(timerAmrapHandle); runningAmrap = false; beepAmrap(); } else { displayAmrap.innerText = formatTimeAmrap(secsLeftAmrap); } }, 1000); }
                    function pauseAmrap() { runningAmrap = false; clearInterval(timerAmrapHandle); if (secsLeftAmrap > 0) { statusAmrap.innerText = "Pausado."; } }
                    function resetAmrap() { pauseAmrap(); secsLeftAmrap = TOTAL_AMRAP; displayAmrap.classList.remove('done'); displayAmrap.innerText = formatTimeAmrap(secsLeftAmrap); statusAmrap.innerText = ""; }
                </script>
            </body></html>
            """
            components.html(html_timer_amrap, height=230)
        st.write("")
        with st.form("registro_amrap", clear_on_submit=True):
            c_top1, c_top2, c_top3 = st.columns([2, 1, 1])
            with c_top1: data_treino = st.date_input("Data do Treino", value=(datetime.utcnow() - timedelta(hours=3)).date(), key="d_amrap")
            agora = datetime.utcnow() - timedelta(hours=3)
            with c_top2: hora = st.selectbox("Hora", [f"{i:02d}" for i in range(24)], index=agora.hour, key="h_amrap")
            with c_top3: minuto = st.selectbox("Min.", [f"{i:02d}" for i in range(60)], index=agora.minute, key="m_amrap")
            horario = f"{hora}:{minuto}:00"
            st.markdown("---")
            c_round1, c_round2 = st.columns(2)
            with c_round1: rounds = st.number_input("Número TOTAL de Rounds Completos", min_value=0, step=1, value=5)
            with c_round2: humor = st.selectbox("Estado Mental no Treino", ["Normal", "Foco Extremo", "Motivado", "Cansado", "Estressado"], key="humor_amrap")
            st.info(f"📊 **Total Projetado:** Serão gravados **{rounds * 5} Barras**, **{rounds * 10} Flexões** e **{rounds * 15} Agachamentos** no histórico.")
            
            if st.form_submit_button("🚀 Gravar AMRAP", use_container_width=True):
                if rounds > 0:
                    mochila_json = {"humor": humor, "isometria_tentativas": 0, "isometria_segundos": 0}
                    dados_barra = { "data": str(data_treino), "horario": str(horario), "grupo_muscular": "Costas", "exercicio": "Barra Fixa (Pronada)", "series": int(rounds), "repeticoes": int(rounds * 5), "carga_kg": 0.0, "descanso_seg": 0, "duracao_min": 20, "distancia_km": 0.0, "alimentacao_saudavel": "", "alimentacao_besteirol": "", "peso_corporal": 0.0, "dados_extras": mochila_json }
                    dados_flexao = dados_barra.copy()
                    dados_flexao.update({"grupo_muscular": "Peitoral", "exercicio": "Flexão", "repeticoes": int(rounds * 10), "duracao_min": 0})
                    dados_agachamento = dados_barra.copy()
                    dados_agachamento.update({"grupo_muscular": "Pernas", "exercicio": "Agachamento", "repeticoes": int(rounds * 15), "duracao_min": 0})
                    supabase.table("treinos").insert([dados_barra, dados_flexao, dados_agachamento]).execute()
                    st.success("🔥 WOD AMRAP destruído! Os 3 exercícios foram registrados no sistema com sucesso.")
                    st.rerun()
                else: st.error("Insira pelo menos 1 round para registrar o treino.")

# ==========================================
# ABA 2: DASHBOARD FÍSICO
# ==========================================
with tab_dash_treino:
    meta_fisica_diaria = 200 
    reps_treino_hoje = 0
    if not df_treinos.empty:
        df_treinos['data_real'] = pd.to_datetime(df_treinos['data'])
        hoje_data = (pd.Timestamp.utcnow() - pd.Timedelta(hours=3)).normalize().tz_localize(None)
        df_hoje_tr = df_treinos[df_treinos['data_real'] == hoje_data]
        if not df_hoje_tr.empty: reps_treino_hoje = int(df_hoje_tr['repeticoes'].sum())
            
    faltam_reps = max(0, meta_fisica_diaria - reps_treino_hoje)
    cor_alerta_f = "#F43F5E" if faltam_reps > 0 else "#10B981"
    msg_alerta_f = f"💪 FALTAM {faltam_reps} REPETIÇÕES HOJE!" if faltam_reps > 0 else "🏆 META FÍSICA BATIDA!"
    bg_color_f = "rgba(244, 63, 94, 0.1)" if faltam_reps > 0 else "rgba(16, 185, 129, 0.1)"
    
    st.markdown(f"""
    <div style="background: {bg_color_f}; border: 2px solid {cor_alerta_f}; padding: 30px; border-radius: 12px; text-align: center; box-shadow: 0 0 20px {cor_alerta_f}40; margin-bottom: 30px;">
        <h2 style="color: {cor_alerta_f}; margin: 0; font-size: 38px; font-weight: 900; letter-spacing: 1px;">{msg_alerta_f}</h2>
        <p style="color: #E0E0E0; font-size: 18px; margin-top: 10px; font-weight: bold;">Meta de Volume: {meta_fisica_diaria} Reps | Realizadas Hoje: {reps_treino_hoje}</p>
    </div>
    """, unsafe_allow_html=True)
    
    fig_gauge_f = go.Figure(go.Indicator(
        mode = "gauge+number", value = reps_treino_hoje, domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Progresso de Repetições", 'font': {'color': '#E0E0E0', 'size': 20}},
        gauge = { 'axis': {'range': [None, meta_fisica_diaria], 'tickwidth': 1, 'tickcolor': "#E0E0E0"}, 'bar': {'color': cor_alerta_f}, 'bgcolor': "rgba(0,0,0,0)", 'borderwidth': 2, 'bordercolor': "#1F1F1F", 'steps': [ {'range': [0, meta_fisica_diaria*0.5], 'color': '#333'}, {'range': [meta_fisica_diaria*0.5, meta_fisica_diaria*0.9], 'color': '#555'} ] }
    ))
    fig_gauge_f.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E0E0E0"), height=320, margin=dict(l=30, r=30, t=70, b=40))
    st.plotly_chart(fig_gauge_f, use_container_width=True)

    if not df_treinos.empty:
        df_treinos['isometria_segundos'] = df_treinos['dados_extras'].apply(lambda x: safe_get(x, 'isometria_segundos', 0))
        total_dias = len(df_treinos['data'].unique())
        total_reps = int(df_treinos['repeticoes'].sum())
        carga_max = df_treinos['carga_kg'].max()
        
        st.markdown(f"""
        <div class="card-container">
            <div class="neon-card card-cyan"><div class="card-title">🏆 DIAS TREINADOS</div><div class="card-value">{total_dias}</div></div>
            <div class="neon-card card-emerald"><div class="card-title">🔥 REPETIÇÕES (TOTAL)</div><div class="card-value">{total_reps}</div></div>
            <div class="neon-card card-violet"><div class="card-title">💪 CARGA MÁXIMA</div><div class="card-value">{carga_max:.1f} kg</div></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🎛️ Controles Visuais")
        c_ctrl1, c_ctrl2 = st.columns(2)
        with c_ctrl1: ex_selecionados = st.multiselect("Quais exercícios visualizar?", options=TODOS_EXERCICIOS, default=[])
        with c_ctrl2: st.write(""); mostrar_peso_corporal = st.checkbox("Incluir gráfico de Evolução do Peso Corporal", value=True)
            
        st.write("---")
        df_filtrado = df_treinos.copy()
        if ex_selecionados: df_filtrado = df_filtrado[df_filtrado['exercicio'].isin(ex_selecionados)]

        col_graf1, col_graf2 = st.columns(2) if mostrar_peso_corporal else (None, st.container())
        
        if mostrar_peso_corporal and col_graf1:
            with col_graf1:
                with st.container(border=True):
                    st.markdown("#### ⚖️ Evolução do Peso Corporal (kg)")
                    if 'peso_corporal' in df_raw.columns:
                        df_peso = df_raw[df_raw['peso_corporal'] > 0].groupby('data', as_index=False)['peso_corporal'].mean()
                        if not df_peso.empty:
                            df_peso['data_format'] = df_peso['data'].dt.strftime('%d/%m')
                            fig_peso = px.line(df_peso, x='data_format', y='peso_corporal', markers=True, text='peso_corporal')
                            fig_peso.update_traces(line_color='#009CA6', marker=dict(size=10, color='#8B5CF6'), textposition="top center", texttemplate='%{text:.1f}')
                            fig_peso.update_layout(xaxis_title="", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E0E0E0"), margin=dict(l=0, r=0, t=20, b=20), xaxis=dict(type='category', showgrid=False), yaxis=dict(showgrid=True, gridcolor="#1F1F1F"))
                            st.plotly_chart(fig_peso, use_container_width=True)
                        else: st.info("Sem registros de peso.")
                    else: st.info("Adicione dados de peso.")

        with col_graf2:
            st.markdown("#### 📊 Volume de Repetições Diárias")
            df_reps = df_filtrado[df_filtrado['repeticoes'] > 0].copy()
            if not df_reps.empty:
                dias_map = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sáb', 6: 'Dom'}
                df_reps['dia_formatado'] = df_reps['data'].dt.weekday.map(dias_map) + df_reps['data'].dt.strftime(' (%d/%m)')
                df_reps_dia = df_reps.groupby(['data', 'dia_formatado'], as_index=False)['repeticoes'].sum().sort_values('data')
                fig_reps = px.bar(df_reps_dia, x='dia_formatado', y='repeticoes', text_auto=True)
                fig_reps.update_traces(marker_color='#009CA6', textfont_color='white')
                fig_reps.update_layout(xaxis_title="", yaxis_title="Total Reps", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E0E0E0"), margin=dict(l=0, r=0, t=20, b=0), xaxis=dict(type='category', showgrid=False), yaxis=dict(showgrid=True, gridcolor="#1F1F1F"))
                st.plotly_chart(fig_reps, use_container_width=True)
            else: st.info("Sem dados de repetições para os exercícios selecionados.")

        st.markdown("#### ⏱️ Tempo Sustentado (Cardio / Isometria)")
        df_dur = df_filtrado[(df_filtrado['isometria_segundos'] > 0) | (df_filtrado['duracao_min'] > 0)].copy()
        if not df_dur.empty:
            df_dur['tempo_total'] = df_dur.apply(lambda row: row['isometria_segundos'] if row['isometria_segundos'] > 0 else row['duracao_min'], axis=1)
            df_dur['tipo_tempo'] = df_dur.apply(lambda row: 'Segundos' if row['isometria_segundos'] > 0 else 'Minutos', axis=1)
            df_dur['dia_formatado'] = df_dur['data'].dt.strftime('%d/%m')
            fig_dur = px.bar(df_dur, x='dia_formatado', y='tempo_total', color='tipo_tempo', text_auto=True, barmode='group')
            fig_dur.update_traces(textfont_color='white')
            fig_dur.update_layout(xaxis_title="", yaxis_title="Tempo (Seg ou Min)", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E0E0E0"), xaxis=dict(showgrid=False))
            st.plotly_chart(fig_dur, use_container_width=True)
        else:
            st.info("Sem dados de tempo/isometria para os exercícios selecionados.")
    else: st.warning("Nenhum treino encontrado para o filtro selecionado.")

# ==========================================
# ABA 3: REGISTRO DE ALIMENTAÇÃO
# ==========================================
with tab_dieta:
    with st.form("registro_dieta", clear_on_submit=True):
        st.markdown("<h3 style='margin-bottom: 20px; color: #10B981;'>🍏 Diário Alimentar</h3>", unsafe_allow_html=True)
        data_dieta = st.date_input("Data da Refeição", value=(datetime.utcnow() - timedelta(hours=3)).date(), key="data_dieta")
        c_alim1, c_alim2 = st.columns(2)
        with c_alim1:
            st.markdown("#### 🥗 Combustível Limpo")
            alim_s_preset = st.multiselect("Selecione os alimentos:", ALIMENTOS_SAUDAVEIS)
            alim_s_extra = st.text_input("Outros (opcional):", placeholder="Ex: Frango, Aveia...")
        with c_alim2:
            st.markdown("#### 🍔 Junk Food")
            alim_b_preset = st.multiselect("Selecione as besteiras:", ALIMENTOS_BESTEIROL)
            alim_b_extra = st.text_input("Outras besteiras (opcional):", placeholder="Ex: Cerveja, Doce de leite...")
        if st.form_submit_button("💾 Salvar Refeição", use_container_width=True):
            lista_s = alim_s_preset + ([alim_s_extra.strip()] if alim_s_extra.strip() else [])
            lista_b = alim_b_preset + ([alim_b_extra.strip()] if alim_b_extra.strip() else [])
            dados_dieta = { "data": str(data_dieta), "horario": "00:00:00", "grupo_muscular": "Nutrição", "exercicio": "Refeição Diária", "series": 0, "repeticoes": 0, "carga_kg": 0, "descanso_seg": 0, "duracao_min": 0, "distancia_km": 0, "alimentacao_saudavel": ", ".join(lista_s), "alimentacao_besteirol": ", ".join(lista_b), "peso_corporal": 0.0, "dados_extras": {} }
            supabase.table("treinos").insert(dados_dieta).execute()
            st.success("Nutrição indexada!")
            st.rerun()

# ==========================================
# ABA 4: REGISTRO DE PESO
# ==========================================
with tab_peso:
    with st.form("registro_peso", clear_on_submit=True):
        st.markdown("<h3 style='margin-bottom: 20px; color: #8B5CF6;'>⚖️ Biometria Diária</h3>", unsafe_allow_html=True)
        c_p1, c_p2 = st.columns(2)
        with c_p1: data_peso = st.date_input("Data da Pesagem", value=(datetime.utcnow() - timedelta(hours=3)).date(), key="data_peso")
        with c_p2: peso_corporal_input = st.number_input("Seu Peso (kg)", min_value=0.0, step=0.1)
        if st.form_submit_button("💾 Atualizar Biometria", use_container_width=True):
            dados_peso = { "data": str(data_peso), "horario": "00:00:00", "grupo_muscular": "Métricas", "exercicio": "Peso Diário", "series": 0, "repeticoes": 0, "carga_kg": 0, "descanso_seg": 0, "duracao_min": 0, "distancia_km": 0, "alimentacao_saudavel": "", "alimentacao_besteirol": "", "peso_corporal": float(peso_corporal_input), "dados_extras": {} }
            supabase.table("treinos").insert(dados_peso).execute()
            st.success("Métrica salva com sucesso!")
            st.rerun()

# ==========================================
# ABA 5: REGISTRO DE ESTUDOS E POMODORO
# ==========================================
with tab_estudo:
    st.markdown("<h3 style='margin-bottom: 20px; color: #009CA6;'>📚 Central de Foco: Operação FGV</h3>", unsafe_allow_html=True)
    prox_disciplina = ROTA_ESTRATEGICA[0]
    if not df_estudos.empty:
        df_ciclo = df_estudos[df_estudos['exercicio'].isin(ROTA_ESTRATEGICA)]
        if not df_ciclo.empty:
            ultima_disciplina = df_ciclo.sort_values(by=['data', 'horario'], ascending=[False, False]).iloc[0]['exercicio']
            idx_atual = ROTA_ESTRATEGICA.index(ultima_disciplina)
            idx_prox = (idx_atual + 1) % len(ROTA_ESTRATEGICA)
            prox_disciplina = ROTA_ESTRATEGICA[idx_prox]
            
    prox_topico_sugerido = obter_pior_topico(df_estudos, prox_disciplina)
    topico_portugues = obter_pior_topico(df_estudos, "Língua Portuguesa")
    topico_matematica = obter_pior_topico(df_estudos, "Matemática e Estatística Aplicada")

    html_bussola = (
        '<div style="background-color: #0A0A0A; border-left: 4px solid #8B5CF6; padding: 18px; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">'
        '<span style="color: #009CA6; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px;">🧭 Bússola Inteligente (Foco nos Pontos Fracos)</span><br>'
        '<div style="margin-top: 12px; padding-bottom: 8px; border-bottom: 1px solid #1F1F1F;">'
        '<span style="color: #AAA; font-size: 13px;">ROTAÇÃO PRINCIPAL:</span><br>'
        f'<span style="color: #FFF; font-size: 18px; font-weight: 700;">🎯 {prox_disciplina}</span><br>'
        f'<span style="color: #10B981; font-size: 13px; font-weight: 600;">📖 Prioridade: {prox_topico_sugerido}</span>'
        '</div>'
        '<div style="margin-top: 8px; display: flex; gap: 20px;">'
        '<div style="flex: 1;">'
        '<span style="color: #F43F5E; font-size: 12px; font-weight: bold;">⚠️ DIÁRIO: PORTUGUÊS</span><br>'
        f'<span style="color: #DDD; font-size: 13px;">📖 {topico_portugues}</span>'
        '</div>'
        '<div style="flex: 1;">'
        '<span style="color: #F43F5E; font-size: 12px; font-weight: bold;">⚠️ DIÁRIO: MATEMÁTICA</span><br>'
        f'<span style="color: #DDD; font-size: 13px;">📖 {topico_matematica}</span>'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(html_bussola, unsafe_allow_html=True)

    col_pomodoro, col_registro = st.columns([1, 1.5], gap="large")
    with col_pomodoro:
        with st.container(border=True):
            st.markdown("#### ⏱️ Modos de Foco")
            pasta_videos = "edits_motivacionais"
            try: videos_disponiveis = sorted([v for v in os.listdir(pasta_videos) if v.endswith(".mp4")])
            except FileNotFoundError: videos_disponiveis = []

            if "video_recompensa_atual" not in st.session_state or st.session_state.video_recompensa_atual not in videos_disponiveis:
                st.session_state.video_recompensa_atual = random.choice(videos_disponiveis) if videos_disponiveis else None

            video_base64 = ""
            if st.session_state.video_recompensa_atual:
                caminho_video = os.path.join(pasta_videos, st.session_state.video_recompensa_atual)
                with open(caminho_video, 'rb') as v: video_base64 = base64.b64encode(v.read()).decode('utf-8')

            video_tag = ""
            if video_base64: video_tag = "<video class='cinema-video' id='vid-player' controls autoplay><source src='data:video/mp4;base64," + video_base64 + "' type='video/mp4'></video>"
            else: video_tag = "<p style='color:#E0E0E0;'>Nenhum vídeo encontrado, mas o ciclo terminou!</p>"

            c_rw1, c_rw2 = st.columns([2, 1])
            with c_rw1:
                if st.session_state.video_recompensa_atual: st.caption(f"🎬 Recompensa deste ciclo: **{st.session_state.video_recompensa_atual}**")
            with c_rw2:
                if videos_disponiveis and st.button("🔀 Sortear outro", use_container_width=True, key="btn_sortear_video"):
                    st.session_state.video_recompensa_atual = random.choice(videos_disponiveis)
                    st.rerun()

            with st.expander("🎬 Ver um Edit agora (sem rodar o cronômetro)"):
                if videos_disponiveis:
                    video_manual = st.selectbox("Escolha o vídeo:", videos_disponiveis, key="select_video_manual")
                    if st.button("▶️ Assistir Agora", use_container_width=True, key="btn_assistir_manual"): st.video(os.path.join(pasta_videos, video_manual))
                else: st.info("Nenhum vídeo .mp4 encontrado.")

            tipo_timer = st.radio("Selecione o Protocolo:", ["🍅 Pomodoro (Estudo Longo)", "⏱️ Cronômetro (Questões)"], horizontal=False)
            st.write("---")

            if "Pomodoro" in tipo_timer:
                c_pom1, c_pom2 = st.columns(2)
                with c_pom1: minutos_pomodoro = st.number_input("Minutos", min_value=0, value=50, step=1)
                with c_pom2: segundos_pomodoro = st.number_input("Segundos", min_value=0, max_value=59, value=0, step=5)
                total_segundos = int((minutos_pomodoro * 60) + segundos_pomodoro)
                
                if total_segundos > 0:
                    html_pomodoro = """
                    <!DOCTYPE html><html><head><style>
                            body { background-color: transparent; color: #E0E0E0; font-family: sans-serif; text-align: center; margin: 0; padding: 0; }
                            .time { font-size: 65px; color: #009CA6; text-shadow: 0 0 15px rgba(0,156,166,0.5); font-weight: bold; margin: 10px 0 20px 0; }
                            .btn { padding: 10px 20px; background-color: #0A0A0A; color: #009CA6; border: 2px solid #009CA6; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: bold; transition: all 0.3s; }
                            .btn:hover { background-color: #009CA6; color: #000; box-shadow: 0 0 10px rgba(0,156,166,0.5); }
                    </style></head><body>
                        <div class="time" id="display">[INITIAL_TIME]</div>
                        <button class="btn" onclick="startPomodoro()">▶️ Iniciar Foco</button>
                        <script>
                            let secs = [TOTAL_SECS]; let running = false; const display = document.getElementById('display');
                            function formatTime(s) { const m = Math.floor(s / 60); const rs = s % 60; return (m < 10 ? '0' : '') + m + ':' + (rs < 10 ? '0' : '') + rs; }
                            function startPomodoro() { if(!running && secs > 0) { running = true; let timer = setInterval(() => { secs--; display.innerText = formatTime(secs); if(secs <= 0) { clearInterval(timer); running = false; triggerCinema(); } }, 1000); } }
                            function triggerCinema() {
                                var parentDoc = window.parent.document; var style = parentDoc.createElement('style'); style.id = 'cinema-style';
                                style.innerHTML = `
                                    .cinema-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background-color: rgba(5, 5, 5, 0.95); z-index: 999999; display: flex; flex-direction: column; justify-content: center; align-items: center; backdrop-filter: blur(10px); }
                                    .cinema-video { width: 80vw; max-height: 75vh; border: 2px solid #009CA6; border-radius: 12px; box-shadow: 0 0 50px rgba(0, 156, 166, 0.5); outline: none; }
                                    .btn-fechar { margin-top: 25px; padding: 12px 30px; background-color: #0A0A0A; color: #009CA6; border: 2px solid #009CA6; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: all 0.3s ease; font-family: sans-serif; }
                                    .btn-fechar:hover { background-color: #009CA6; color: #000; box-shadow: 0 0 20px rgba(0,156,166,0.6); }
                                `;
                                parentDoc.head.appendChild(style);
                                var overlay = parentDoc.createElement('div'); overlay.className = 'cinema-overlay'; overlay.id = 'cinema-modal';
                                overlay.innerHTML = `
                                    <h2 style="color: #FFF; font-weight: 800; letter-spacing: 2px; margin-bottom: 20px;">⚡ CICLO CONCLUÍDO! RECOMPENSA DESBLOQUEADA ⚡</h2>
                                    [VIDEO_TAG]
                                    <button class="btn-fechar" id="btn-fechar-cinema">FECHAR E VOLTAR AO MODO OPERANTE</button>
                                `;
                                parentDoc.body.appendChild(overlay);
                                var btnFechar = parentDoc.getElementById('btn-fechar-cinema');
                                btnFechar.addEventListener('click', function() { var vid = parentDoc.getElementById('vid-player'); if (vid) { vid.pause(); } overlay.remove(); style.remove(); });
                            }
                        </script>
                    </body></html>
                    """
                    html_pomodoro = html_pomodoro.replace("[TOTAL_SECS]", str(total_segundos)).replace("[INITIAL_TIME]", f"{minutos_pomodoro:02d}:{segundos_pomodoro:02d}").replace("[VIDEO_TAG]", video_tag)
                    components.html(html_pomodoro, height=180)
                else: st.warning("⏱️ Por favor, defina um tempo maior que zero para o ciclo.")
            else:
                html_cronometro = """
                <!DOCTYPE html><html><head><style>
                        body { background-color: transparent; color: #E0E0E0; font-family: sans-serif; text-align: center; margin: 0; padding: 0; }
                        .time { font-size: 65px; color: #009CA6; text-shadow: 0 0 15px rgba(0,156,166,0.5); font-weight: bold; margin: 10px 0 20px 0; }
                        .btn-group { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
                        .btn { padding: 10px 20px; background-color: #0A0A0A; color: #009CA6; border: 2px solid #009CA6; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: bold; transition: all 0.3s; }
                        .btn:hover { background-color: #009CA6; color: #000; box-shadow: 0 0 10px rgba(0,156,166,0.5); }
                        .btn-finish { border-color: #8B5CF6; color: #8B5CF6; }
                        .btn-finish:hover { background-color: #8B5CF6; color: #000; box-shadow: 0 0 10px rgba(139,92,246,0.5); }
                </style></head><body>
                    <div class="time" id="display">00:00</div>
                    <div class="btn-group">
                        <button class="btn" onclick="start()">▶️ Iniciar</button>
                        <button class="btn" onclick="pause()">⏸️ Pausar</button>
                        <button class="btn btn-finish" onclick="finish()">✅ Finalizar & Edit</button>
                    </div>
                    <script>
                        let timer; let secs = 0; let running = false; const display = document.getElementById('display');
                        function formatTime(s) { const m = Math.floor(s / 60); const rs = s % 60; return (m < 10 ? '0' : '') + m + ':' + (rs < 10 ? '0' : '') + rs; }
                        function start() { if(!running) { running = true; timer = setInterval(() => { secs++; display.innerText = formatTime(secs); }, 1000); } }
                        function pause() { running = false; clearInterval(timer); }
                        function finish() {
                            if(secs === 0) return; pause();
                            var parentDoc = window.parent.document; var style = parentDoc.createElement('style'); style.id = 'cinema-style';
                            style.innerHTML = `
                                .cinema-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background-color: rgba(5, 5, 5, 0.95); z-index: 999999; display: flex; flex-direction: column; justify-content: center; align-items: center; backdrop-filter: blur(10px); }
                                .cinema-video { width: 80vw; max-height: 75vh; border: 2px solid #009CA6; border-radius: 12px; box-shadow: 0 0 50px rgba(0, 156, 166, 0.5); outline: none; }
                                .btn-fechar { margin-top: 25px; padding: 12px 30px; background-color: #0A0A0A; color: #009CA6; border: 2px solid #009CA6; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: all 0.3s ease; font-family: sans-serif; }
                                .btn-fechar:hover { background-color: #009CA6; color: #000; box-shadow: 0 0 20px rgba(0,156,166,0.6); }
                            `;
                            parentDoc.head.appendChild(style);
                            var overlay = parentDoc.createElement('div'); overlay.className = 'cinema-overlay'; overlay.id = 'cinema-modal';
                            overlay.innerHTML = `
                                <h2 style="color: #FFF; font-weight: 800; letter-spacing: 2px; margin-bottom: 20px;">⚡ TEMPO DE RESOLUÇÃO: ${formatTime(secs)} ⚡</h2>
                                [VIDEO_TAG]
                                <button class="btn-fechar" id="btn-fechar-cinema">FECHAR E VOLTAR</button>
                            `;
                            parentDoc.body.appendChild(overlay);
                            var btnFechar = parentDoc.getElementById('btn-fechar-cinema');
                            btnFechar.addEventListener('click', function() { var vid = parentDoc.getElementById('vid-player'); if (vid) { vid.pause(); } overlay.remove(); style.remove(); secs = 0; display.innerText = "00:00"; });
                        }
                    </script>
                </body></html>
                """
                html_cronometro = html_cronometro.replace("[VIDEO_TAG]", video_tag)
                components.html(html_cronometro, height=180)

    with col_registro:
        st.markdown("#### 📝 Input de Produtividade")
        tipo_sessao = st.radio("Tipo de Sessão", ["🎥 Apenas Vídeo Aula", "📝 Apenas Questões", "🃏 Revisão (Anki)"], horizontal=True)

        if tipo_sessao == "🃏 Revisão (Anki)":
            disciplina = st.selectbox("Deck do Anki", DECKS_ANKI)
            topicos_disponiveis = []
        else:
            index_recomendado = DISCIPLINAS_ESTUDO.index(prox_disciplina) if prox_disciplina in DISCIPLINAS_ESTUDO else 0
            disciplina = st.selectbox("Módulo / Disciplina", DISCIPLINAS_ESTUDO, index=index_recomendado, key="disciplina_estudo_select")
            topicos_disponiveis = ["🎯 Simulado / Visão Geral"] + TOPICOS_EDITAL.get(disciplina, ["Geral"])

        with st.form("registro_estudo", clear_on_submit=True):
            data_estudo = st.date_input("Data da Sessão", value=(datetime.utcnow() - timedelta(hours=3)).date())
            
            if tipo_sessao != "🃏 Revisão (Anki)":
                topicos_selecionados = st.multiselect("📖 Tópico(s) do Edital", topicos_disponiveis)
                topicos_str = ", ".join(topicos_selecionados) if topicos_selecionados else "Geral"
            else: topicos_str = "Revisão Espaçada"
            
            tempo_estudo = 0; tempo_video = 0; certas = 0; erradas = 0; cartoes_anki = 0; fonte_questoes = "Não Aplicável"
            st.markdown("---")
            
            if tipo_sessao == "🎥 Apenas Vídeo Aula":
                st.markdown("##### 🎥 Consumo de Conteúdo")
                tempo_video = st.number_input("Tempo de Vídeo Aula (min)", min_value=0, step=15)
                
            elif tipo_sessao == "📝 Apenas Questões":
                st.markdown("##### 📝 Bateria de Questões")
                c_est1, c_est2 = st.columns(2)
                with c_est1:
                    tempo_estudo = st.number_input("Tempo Líquido Resolução (min)", min_value=0, step=15)
                    fonte_questoes = st.selectbox("Fonte das Questões", FONTES_QUESTOES)
                with c_est2:
                    certas = st.number_input("✅ Questões Corretas", min_value=0, step=1)
                    erradas = st.number_input("❌ Questões Erradas", min_value=0, step=1)
                    
            elif tipo_sessao == "🃏 Revisão (Anki)":
                st.markdown("##### 🃏 Sessão de Flashcards")
                c_est1, c_est2 = st.columns(2)
                with c_est1: tempo_estudo = st.number_input("Tempo Líquido (min)", min_value=0, step=10)
                with c_est2: cartoes_anki = st.number_input("🔄 Cartões Revisados", min_value=0, step=10)
                fonte_questoes = "Anki"

            st.write("")
            if st.form_submit_button("💾 Computar Sessão", use_container_width=True):
                total_q = cartoes_anki if tipo_sessao == "🃏 Revisão (Anki)" else certas + erradas
                mochila_estudo_json = { "topico_edital": topicos_str, "q_certas": certas, "q_erradas": erradas, "tempo_video": tempo_video, "fonte_questoes": fonte_questoes }
                horario_br = (datetime.utcnow() - timedelta(hours=3)).strftime("%H:%M:%S")
                dados_estudo = {
                    "data": str(data_estudo), "horario": str(horario_br), "grupo_muscular": "Estudos", "exercicio": disciplina, 
                    "series": 0, "repeticoes": int(total_q), "carga_kg": 0.0, "descanso_seg": 0, "duracao_min": int(tempo_estudo),
                    "distancia_km": 0.0, "alimentacao_saudavel": "", "alimentacao_besteirol": "", "peso_corporal": 0.0, "dados_extras": mochila_estudo_json 
                }
                supabase.table("treinos").insert(dados_estudo).execute()
                st.success("Sessão arquivada na base de conhecimento!")
                st.rerun()      

# ==========================================
# ABA 6: DASHBOARD DE ESTUDOS
# ==========================================
with tab_dash_estudo:
    html_motivacional = (
        '<div style="text-align: center; margin-bottom: 25px;">'
        '<p style="color: #009CA6; font-style: italic; font-size: 16px;">"Se você não gosta do seu destino, não o aceite. Em vez disso, tenha a coragem para transformá-lo naquilo que você quer que ele seja." <br>'
        '<span style="font-weight: bold; color: #FFF;">— Naruto Uzumaki</span></p></div>'
    )
    st.markdown(html_motivacional, unsafe_allow_html=True)
    
    with st.expander("📖 Clique para visualizar o Edital Completo"):
        st.markdown("""
        **MATEMÁTICA E ESTATÍSTICA APLICADA:** I MATEMÁTICA: 1 Cálculo: Funções. Limites. Derivadas. Derivadas Parciais. Máximos e mínimos. Integrais. 2 Álgebra linear: Notação de vetores e matrizes. Produto escalar e produto vetorial. Matriz identidade, inversa e transposta. Transformações lineares. Normas L1 e L2. Autovalores e autovetores. II ESTATÍSTICA: 1 Conceitos de probabilidade. Modelo de probabilidade. Probabilidade condicional. Independência. Variáveis aleatórias. Esperança, variância e covariância. Distribuições contínuas e discretas. Distribuições multidimensionais: matriz de covariância. 2 Estatísticas descritivas. Teorema do Limite Central. Teste de hipótese e intervalo de confiança. Estimador de máxima verossimilhança. Inferência bayesiana. Coeficiente de correlação de Pearson. Diagrama boxplot e avaliação de outliers.
        
        **CIÊNCIA DE DADOS:** 1 Aprendizado supervisionado: Regressão e Classificação. Métricas de avaliação. Overfitting e underfitting de modelos. Regularização. Seleção de modelos. Validação cruzada. Conjunto de treino, validação e teste. Trade off entre variância e viés. Regressão Linear e Regressão Logística. Árvores de Decisão e random forests. SVM. K-NN. 2 Aprendizado não-supervisionado: Redução de dimensionalidade: PCA. K-Means. Mistura de Gaussianas. Regras de Associação. 3 Redes neurais artificiais: Definições e arquitetura. Funções de ativação. Otimização: método do gradiente, método do gradiente estocástico e backpropagation. Métodos de regularização: penalização com normas L1 e L2. CNN. 4 Machine Learning aplicado. Noções de visão computacional com CNN. Classificação de imagens e detecção de objetos. Noções de processamento de linguagem natural. 5 ETL. 6 Manipulação, tratamento e visualização de dados. 7 Inteligência artificial. 7.1 Análise de dados (Pandas, NumPy, Jupiter, R). 7.2 Aprendizado de máquina. 7.2.1 Técnicas de classificação. 7.2.2 Técnicas de regressão. 7.2.3 Técnicas de agrupamento. 7.2.4 Técnicas de redução de dimensionalidade. 7.2.5 Técnicas de associação. 7.2.6 Sistemas de recomendação. 8 Processamento de linguagem natural (PLN). 9 Visão computacional. 10 Deep learning. 11 Mineração de Dados. 12 Ferramenta SAS.
        
        **LINGUAGENS DE PROGRAMAÇÃO E SOFTWARES EM CIÊNCIAS DE DADOS:** 1 Python e suas bibliotecas: Numpy, Matplotlib, Seaborn, Streamlit, Pandas, Scipy, TensorFlow, Keras e Pytorch. 2 R e suas bibliotecas. 3 Apache Hadoop e Apache Spark.
        
        **BANCO DE DADOS:** 1 Modelagem de dados (conceitual, lógica e física). 2 Abordagem relacional. 3 Normalização das estruturas de dados. 4 Integridade referencial. 5 Metadados. 6 Modelagem dimensional. 7 Linguagem de consulta estruturada (SQL). 8 Linguagem de definição de dados (DDL). 9 Linguagem de manipulação de dados (DML). 10 SGBD. 11 Propriedades de banco de dados. 12 Banco de dados NoSQL. 13 Banco de dados em memória. 14 Data lakes e soluções para big data. 
        
        **MODULO I - CONHECIMENTOS GERAIS (PARA TODOS OS CARGOS/PERFIS)**
        
        **LÍNGUA PORTUGUESA:** 1 Compreensão e interpretação de textos de gêneros variados. 2 Reconhecimento de tipos e gêneros textuais. 3 Domínio da ortografia oficial. 4 Domínio dos mecanismos de coesão textual. 4.1 Emprego de elementos de referenciação, substituição e repetição, de conectores e de outros elementos de sequenciação textual. 4.2 Emprego de tempos e modos verbais. 5 Domínio da estrutura morfossintática do período. 5.1 Emprego das classes de palavras. 5.2 Relações de coordenação entre orações e entre termos da oração. 5.3 Relações de subordinação entre orações e entre termos da oração. 5.4 Emprego dos sinais de pontuação. 5.5 Concordância verbal e nominal. 5.6 Regência verbal e nominal. 5.7 Emprego do sinal indicativo de crase. 5.8 Colocação dos pronomes átonos. 6 Reescrita de frases e parágrafos do texto. 6.1 Significação das palavras. 6.2 Substituição de palavras ou de trechos de texto. 6.3 Reorganização da estrutura de orações e de períodos do texto. 6.4 Reescrita de textos de diferentes gêneros e níveis de formalidade.
        
        **LÍNGUA INGLESA:** 1 Compreensão de textos em língua inglesa e itens gramaticais relevantes para o entendimento dos sentidos dos textos.
        
        **RACIOCÍNIO LÓGICO:** 1 Estruturas lógicas. 2 Lógica de argumentação: analogias, inferências, deduções e conclusões. 3 Lógica sentencial (ou proposicional). 3.1 Proposições simples e compostas. 3.2 Tabelas-verdade. 3.3 Equivalências. 3.4 Diagramas lógicos. 4 Lógica de primeira ordem. 5 Raciocínio lógico envolvendo problemas aritméticos, geométricos e matriciais
        
        **ATUALIDADES E INTELIGÊNCIA ARTIFICIAL:** 1 Tópicos relevantes e atuais de diversas áreas, tais como segurança, transportes, política, economia, sociedade, educação, saúde, cultura, tecnologia, energia, relações internacionais, desenvolvimento sustentável e ecologia. 2 Inteligência Artificial: fundamentos e aplicações: conceitos de inteligência artificial; aprendizado da máquina; introdução aos modelos generativos e modelos de linguagem; ética, governança e privacidade em IA.
        
        **LEGISLAÇÃO ACERCA DE SEGURANÇA DA INFORMAÇÃO E PROTEÇÃO DE DADOS:** 1 Lei nº 12.527/2011 (Lei de Acesso à Informação): capítulos I, II, III, IV e V; Dec. nº 7.724 e nº 7845. 2 Lei nº 12.737/2012 (Lei de Delitos Informáticos): art. 2º. 3 Lei nº 12.965/2014 (Marco Civil da Internet): capítulos II, Seção I, e III, Seções I e II. 4 Lei nº 13.709/2018 (Lei Geral de Proteção de Dados Pessoais – LGPD): capítulos I, II, III, IV, VII, VIII
        """)

    meta_diaria = 150
    questoes_hoje = 0
    if not df_estudos.empty:
        df_estudos['data_real'] = pd.to_datetime(df_estudos['data'])
        df_estudos['fonte_questoes'] = df_estudos['dados_extras'].apply(lambda x: safe_get(x, 'fonte_questoes', 'Não Informada'))
        hoje_data = (pd.Timestamp.utcnow() - pd.Timedelta(hours=3)).normalize().tz_localize(None)
        df_hoje_est = df_estudos[(df_estudos['data_real'] == hoje_data) & (df_estudos['fonte_questoes'] != 'Anki')]
        if not df_hoje_est.empty: questoes_hoje = int(df_hoje_est['repeticoes'].sum())
            
    faltam_questoes = max(0, meta_diaria - questoes_hoje)
    cor_alerta = "#F43F5E" if faltam_questoes > 0 else "#10B981"
    msg_alerta = f"🚨 FALTAM {faltam_questoes} QUESTÕES HOJE!" if faltam_questoes > 0 else "🏆 META DIÁRIA BATIDA!"
    bg_color = "rgba(244, 63, 94, 0.1)" if faltam_questoes > 0 else "rgba(16, 185, 129, 0.1)"
    
    st.markdown(f"""
    <div style="background: {bg_color}; border: 2px solid {cor_alerta}; padding: 30px; border-radius: 12px; text-align: center; box-shadow: 0 0 20px {cor_alerta}40; margin-bottom: 30px;">
        <h2 style="color: {cor_alerta}; margin: 0; font-size: 42px; font-weight: 900; letter-spacing: 1px;">{msg_alerta}</h2>
        <p style="color: #E0E0E0; font-size: 18px; margin-top: 10px; font-weight: bold;">Meta Inegociável: {meta_diaria} Questões | Realizadas Hoje: {questoes_hoje}</p>
    </div>
    """, unsafe_allow_html=True)
    
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number", value = questoes_hoje, domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Progresso Diário", 'font': {'color': '#E0E0E0', 'size': 20}},
        gauge = { 'axis': {'range': [None, meta_diaria], 'tickwidth': 1, 'tickcolor': "#E0E0E0"}, 'bar': {'color': cor_alerta}, 'bgcolor': "rgba(0,0,0,0)", 'borderwidth': 2, 'bordercolor': "#1F1F1F", 'steps': [ {'range': [0, meta_diaria*0.5], 'color': '#333'}, {'range': [meta_diaria*0.5, meta_diaria*0.9], 'color': '#555'} ] }
    ))
    fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E0E0E0"), height=320, margin=dict(l=30, r=30, t=70, b=40))
    st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("### 📈 Analytics Acadêmico")
    if not df_estudos.empty:
        df_estudos['q_certas'] = df_estudos['dados_extras'].apply(lambda x: safe_get(x, 'q_certas', 0))
        df_estudos['q_erradas'] = df_estudos['dados_extras'].apply(lambda x: safe_get(x, 'q_erradas', 0))
        df_estudos['topico_edital'] = df_estudos['dados_extras'].apply(lambda x: safe_get(x, 'topico_edital', safe_get(x, 'topico', 'Geral')))
        df_estudos['tempo_video'] = df_estudos['dados_extras'].apply(lambda x: safe_get(x, 'tempo_video', 0))
        
        fontes_unicas = df_estudos['fonte_questoes'].unique().tolist()
        fonte_filtro = st.selectbox("Filtrar Dashboard pela Fonte das Questões:", ["Todas as Fontes"] + fontes_unicas)
        df_dash_est = df_estudos.copy()
        if fonte_filtro != "Todas as Fontes": df_dash_est = df_dash_est[df_dash_est['fonte_questoes'] == fonte_filtro]
            
        df_questoes_reais = df_dash_est[df_dash_est['fonte_questoes'] != 'Anki']
        df_anki = df_dash_est[df_dash_est['fonte_questoes'] == 'Anki']
        
        total_certas = df_questoes_reais['q_certas'].sum()
        total_erradas = df_questoes_reais['q_erradas'].sum()
        total_questoes = int(df_questoes_reais['repeticoes'].sum()) 
        taxa_acerto = (total_certas / (total_certas + total_erradas) * 100) if (total_certas + total_erradas) > 0 else 0
        
        tempo_total_min = int(df_dash_est['duracao_min'].sum())
        tempo_video_total_min = int(df_dash_est['tempo_video'].sum())
        tempo_anki_total_min = int(df_anki['duracao_min'].sum())
        
        st.markdown(f"""
        <div class="card-container">
            <div class="neon-card card-cyan"><div class="card-title">⏳ HORAS LÍQUIDAS</div><div class="card-value">{(tempo_total_min / 60):.1f}h</div></div>
            <div class="neon-card card-violet"><div class="card-title">🎯 TAXA DE ACERTO GLOBAL</div><div class="card-value">{taxa_acerto:.1f}%</div></div>
            <div class="neon-card card-emerald"><div class="card-title">📝 QUESTÕES (BATERIA)</div><div class="card-value">{total_questoes}</div></div>
            <div class="neon-card card-crimson"><div class="card-title">🎥 HORAS VÍDEO AULA</div><div class="card-value">{(tempo_video_total_min / 60):.1f}h</div></div>
            <div class="neon-card card-orange"><div class="card-title">🃏 HORAS REVISÃO ANKI</div><div class="card-value">{(tempo_anki_total_min / 60):.1f}h</div></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        st.markdown("#### 🚨 Radar de Pontos Críticos (Menor Aproveitamento)")
        st.markdown("<span style='color: #AAA; font-size: 14px;'>Mostrando os tópicos que você mais errou (mínimo de 5 questões resolvidas).</span>", unsafe_allow_html=True)
        
        df_criticos = df_questoes_reais.copy()
        df_criticos_agg = df_criticos.groupby(['exercicio', 'topico_edital'], as_index=False)[['q_certas', 'q_erradas']].sum()
        df_criticos_agg['total_q'] = df_criticos_agg['q_certas'] + df_criticos_agg['q_erradas']
        df_criticos_agg = df_criticos_agg[df_criticos_agg['total_q'] >= 5]
        
        if not df_criticos_agg.empty:
            df_criticos_agg['% Acerto'] = (df_criticos_agg['q_certas'] / df_criticos_agg['total_q']) * 100
            df_criticos_agg = df_criticos_agg.sort_values('% Acerto', ascending=True).head(5) 
            df_criticos_agg['topico_curto'] = df_criticos_agg['topico_edital'].apply(lambda x: str(x)[:50] + '...' if len(str(x)) > 50 else str(x))
            df_criticos_agg['Label'] = df_criticos_agg['exercicio'] + " - " + df_criticos_agg['topico_curto']
            
            fig_crit = px.bar(df_criticos_agg, x='% Acerto', y='Label', orientation='h', color='% Acerto', color_continuous_scale="Reds_r", text_auto='.1f')
            fig_crit.update_traces(texttemplate='%{x:.1f}%', textposition='outside', textfont_color='white')
            fig_crit.update_layout(xaxis_title="Taxa de Acerto (%)", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E0E0E0"), coloraxis_showscale=False, xaxis=dict(showgrid=False, range=[0, 110]), yaxis=dict(showgrid=False, autorange="reversed"))
            st.plotly_chart(fig_crit, use_container_width=True)
        else: st.success("✔️ Não há dados críticos suficientes (resolva mais questões para a IA mapear suas fraquezas).")

        st.write("---")
        st.markdown("#### 📉 Radar de Tópicos Menos Explorados (Fiz menos questões)")
        st.markdown("<span style='color: #AAA; font-size: 14px;'>Mostrando os subtópicos que você praticamente não tocou ainda.</span>", unsafe_allow_html=True)
        
        df_poucas_q = df_questoes_reais.copy()
        df_poucas_q_agg = df_poucas_q.groupby(['exercicio', 'topico_edital'], as_index=False).agg(total_questoes=('repeticoes', 'sum'))
        df_poucas_q_agg = df_poucas_q_agg.sort_values('total_questoes', ascending=True).head(10)

        if not df_poucas_q_agg.empty:
            df_poucas_q_agg['topico_curto'] = df_poucas_q_agg['topico_edital'].apply(lambda x: str(x)[:45] + '...' if len(str(x)) > 45 else str(x))
            df_poucas_q_agg['Label'] = df_poucas_q_agg['exercicio'] + " - " + df_poucas_q_agg['topico_curto']

            fig_menos = px.bar(df_poucas_q_agg, x='total_questoes', y='Label', orientation='h', color='total_questoes', color_continuous_scale="Blues", text_auto=True)
            fig_menos.update_traces(textposition='outside', textfont_color='white')
            fig_menos.update_layout(xaxis_title="Total de Questões Resolvidas", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E0E0E0"), coloraxis_showscale=False, xaxis=dict(showgrid=False), yaxis=dict(showgrid=False, autorange="reversed"))
            st.plotly_chart(fig_menos, use_container_width=True)
        else:
            st.info("✔️ Não há dados suficientes para gerar este gráfico.")

        st.write("---")
        c_v1, c_v2 = st.columns(2)
        with c_v1:
            st.markdown("#### 📅 Bateria de Questões por Dia")
            df_q_dia = df_questoes_reais.groupby('data', as_index=False)['repeticoes'].sum().sort_values('data')
            df_q_dia['data_format'] = pd.to_datetime(df_q_dia['data']).dt.strftime('%d/%m')
            fig_q_dia = px.bar(df_q_dia, x='data_format', y='repeticoes', text_auto=True)
            fig_q_dia.update_traces(marker_color='#8B5CF6', textfont_color='white')
            fig_q_dia.update_layout(xaxis_title="", yaxis_title="Total de Questões", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E0E0E0"), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#1F1F1F"), margin=dict(l=0, r=0, t=30, b=10))
            st.plotly_chart(fig_q_dia, use_container_width=True)

        with c_v2:
            st.markdown("#### 🎥 Tempo de Vídeo por Disciplina (Horas)")
            df_video_disc = df_dash_est.groupby('exercicio', as_index=False)['tempo_video'].sum()
            df_video_disc = df_video_disc[df_video_disc['tempo_video'] > 0]
            df_video_disc['horas_video'] = df_video_disc['tempo_video'] / 60
            if not df_video_disc.empty:
                fig_v = px.bar(df_video_disc, x='horas_video', y='exercicio', orientation='h', text_auto='.1f', color='horas_video', color_continuous_scale="Reds")
                fig_v.update_layout(xaxis_title="Horas em Vídeo", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E0E0E0"), coloraxis_showscale=False, xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
                st.plotly_chart(fig_v, use_container_width=True)
            else: st.info("Nenhuma hora de vídeo aula registrada para os filtros atuais.")

        st.write("---")
        st.markdown("#### 🗓️ Cronograma Estratégico (Próximos 30 Dias)")
        hoje_cron = (datetime.utcnow() - timedelta(hours=3)).replace(hour=0, minute=0, second=0, microsecond=0)
        dias_cron = [hoje_cron + timedelta(days=i) for i in range(30)]
        dias_semana_map = {0:"Seg", 1:"Ter", 2:"Qua", 3:"Qui", 4:"Sex", 5:"Sáb", 6:"Dom"}
        indices_topicos = {disc: 0 for disc in ROTA_ESTRATEGICA}
        cronograma_dados = []
        for i, dia in enumerate(dias_cron):
            disc_atual = ROTA_ESTRATEGICA[i % len(ROTA_ESTRATEGICA)]
            lista_topicos = [t for t in TOPICOS_EDITAL.get(disc_atual, ["Geral"]) if "Simulado" not in t]
            if not lista_topicos: lista_topicos = ["Revisão / Exercícios Gerais"]
            topico_atual = lista_topicos[indices_topicos[disc_atual] % len(lista_topicos)]
            indices_topicos[disc_atual] += 1
            cronograma_dados.append({ "Data": dia.strftime("%d/%m"), "Dia da Semana": dias_semana_map[dia.weekday()], "Disciplina de Rodízio": disc_atual, "Assunto (Subdisciplina)": topico_atual })
        df_cronograma = pd.DataFrame(cronograma_dados)
        st.dataframe(df_cronograma, use_container_width=True, hide_index=True, height=250)
        st.write("*Lembre-se: Matemática e Português devem ser incluídos diariamente, independente da Disciplina de Rodízio do dia.*")

        st.write("---")
        c_dash_e1, c_dash_e2 = st.columns(2)
        with c_dash_e1:
            with st.container(border=True):
                st.markdown("#### ⏳ Alocação de Tempo por Disciplina")
                df_disc = df_dash_est.groupby('exercicio', as_index=False)['duracao_min'].sum()
                df_disc['horas'] = df_disc['duracao_min'] / 60
                fig_d = px.pie(df_disc, values='horas', names='exercicio', hole=0.5, color_discrete_sequence=px.colors.sequential.Teal)
                fig_d.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E0E0E0"), margin=dict(l=0, r=0, t=10, b=10))
                st.plotly_chart(fig_d, use_container_width=True)

        with c_dash_e2:
            with st.container(border=True):
                st.markdown("#### 📊 Taxa de Acerto por Disciplina")
                df_acertos = df_questoes_reais.groupby('exercicio', as_index=False)[['q_certas', 'q_erradas']].sum()
                df_acertos['total'] = df_acertos['q_certas'] + df_acertos['q_erradas']
                df_acertos = df_acertos[df_acertos['total'] > 0] 
                if not df_acertos.empty:
                    df_acertos['% Acerto'] = (df_acertos['q_certas'] / df_acertos['total']) * 100
                    fig_a = px.bar(df_acertos, x='exercicio', y='% Acerto', color='% Acerto', color_continuous_scale="Teal")
                    fig_a.update_traces(texttemplate='%{y:.1f}%', textposition='auto')
                    fig_a.update_layout(xaxis_title="", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E0E0E0"), coloraxis_showscale=False, yaxis=dict(showgrid=False), xaxis=dict(showgrid=False))
                    st.plotly_chart(fig_a, use_container_width=True)
                else: st.info("Registre 'Questões Corretas/Erradas' para gerar este gráfico.")

        st.markdown("---")
        st.markdown("#### 📖 Análise Granular por Tópico do Edital")
        disciplinas_unicas = df_dash_est['exercicio'].unique().tolist()
        disciplina_selecionada = st.selectbox("Filtrar Tópicos por Disciplina:", ["Visão Geral (Todas)"] + disciplinas_unicas)
        df_tops = df_dash_est.copy()
        if disciplina_selecionada != "Visão Geral (Todas)": df_tops = df_tops[df_tops['exercicio'] == disciplina_selecionada]
            
        if not df_tops.empty:
            df_topicos_agg = df_tops.groupby(['exercicio', 'topico_edital'], as_index=False).agg(duracao_min=('duracao_min', 'sum'), certas=('q_certas', 'sum'), erradas=('q_erradas', 'sum'))
            df_topicos_agg['horas'] = df_topicos_agg['duracao_min'] / 60
            df_topicos_agg['total_q'] = df_topicos_agg['certas'] + df_topicos_agg['erradas']
            df_topicos_agg['% Acerto'] = (df_topicos_agg['certas'] / df_topicos_agg['total_q']) * 100
            df_topicos_agg['% Acerto'] = df_topicos_agg['% Acerto'].fillna(0)
            df_topicos_agg['topico_curto'] = df_topicos_agg['topico_edital'].apply(lambda x: str(x)[:45] + '...' if len(str(x)) > 45 else str(x))
            
            c_top1, c_top2 = st.columns(2)
            with c_top1:
                with st.container(border=True):
                    st.markdown("##### ⏳ Tempo Investido (Horas)")
                    df_top_horas = df_topicos_agg.sort_values('horas', ascending=True).tail(10)
                    if df_top_horas['horas'].sum() > 0:
                        fig_t = px.bar(df_top_horas, y='topico_curto', x='horas', orientation='h', color='horas', color_continuous_scale="Teal", hover_data={'topico_edital': True, 'exercicio': True})
                        fig_t.update_traces(texttemplate='%{x:.1f}h', textposition='auto')
                        fig_t.update_layout(xaxis_title="", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E0E0E0"), coloraxis_showscale=False, xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
                        st.plotly_chart(fig_t, use_container_width=True)
                    else: st.info("Sem registro de horas para os tópicos filtrados.")
                    
            with c_top2:
                with st.container(border=True):
                    st.markdown("##### 🎯 Taxa de Acerto (%)")
                    df_top_acertos = df_topicos_agg[df_topicos_agg['total_q'] > 0].sort_values('% Acerto', ascending=True).tail(10)
                    if not df_top_acertos.empty:
                        fig_q = px.bar(df_top_acertos, y='topico_curto', x='% Acerto', orientation='h', color='% Acerto', color_continuous_scale="Teal", hover_data={'topico_edital': True, 'total_q': True, 'exercicio': True})
                        fig_q.update_traces(texttemplate='%{x:.1f}%', textposition='auto')
                        fig_q.update_layout(xaxis_title="", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E0E0E0"), coloraxis_showscale=False, xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
                        st.plotly_chart(fig_q, use_container_width=True)
                    else: st.info("Cadastre Acertos/Erros para mapear seu desempenho por tópico.")
        else: st.info("Nenhuma sessão acadêmica cadastrada para essa disciplina.")
    else: st.info("Não há dados de estudo no período selecionado.")

# ==========================================
# ABA 7: CRUZAMENTO DE DADOS 
# ==========================================
with tab_cruzamento:
    st.markdown("### 🧬 Data Lab: Cruzamento de Variáveis")
    st.write("Identifique padrões ocultos entre sua rotina física e seu rendimento cognitivo.")
    if not df_raw.empty and not df_estudos.empty and not df_treinos.empty:
        df_t_dia = df_treinos.groupby('data', as_index=False).agg(total_reps=('repeticoes', 'sum'), treinou=('exercicio', 'count'))
        df_e_dia = df_estudos.groupby('data', as_index=False).agg(minutos_estudados=('duracao_min', 'sum'), total_certas=('q_certas', 'sum'), total_erradas=('q_erradas', 'sum'))
        df_merged = pd.merge(df_t_dia, df_e_dia, on='data', how='outer').fillna(0)
        df_merged['data_format'] = df_merged['data'].dt.strftime('%d/%m')
        
        c_cross1, c_cross2 = st.columns(2)
        with c_cross1:
            with st.container(border=True):
                st.markdown("#### ⚡ Treino vs. Tempo de Estudo")
                df_merged['Status Físico'] = df_merged['treinou'].apply(lambda x: 'Dias com Treino' if x > 0 else 'Dias de Descanso')
                avg_study = df_merged.groupby('Status Físico', as_index=False)['minutos_estudados'].mean()
                avg_study['horas'] = avg_study['minutos_estudados'] / 60
                fig_c1 = px.bar(avg_study, x='Status Físico', y='horas', text_auto='.1f', color='Status Físico', color_discrete_map={'Dias com Treino': '#009CA6', 'Dias de Descanso': '#333333'})
                fig_c1.update_layout(xaxis_title="", yaxis_title="Média de Horas Estudadas", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E0E0E0"), showlegend=False)
                st.plotly_chart(fig_c1, use_container_width=True)
                
        with c_cross2:
            with st.container(border=True):
                st.markdown("#### 🎯 Fadiga x Precisão Cognitiva")
                st.markdown("<span style='font-size: 0.9em; color: #888;'>Relação entre Volume de Treino (Reps) e Taxa de Acerto no mesmo dia.</span>", unsafe_allow_html=True)
                df_acc = df_merged[df_merged['minutos_estudados'] > 0].copy()
                df_acc['% Acerto'] = (df_acc['total_certas'] / (df_acc['total_certas'] + df_acc['total_erradas'])) * 100
                df_acc = df_acc.fillna(0)
                fig_c2 = px.scatter(df_acc, x='total_reps', y='% Acerto', hover_name='data_format', size='minutos_estudados', color='% Acerto', color_continuous_scale='Teal')
                fig_c2.update_layout(xaxis_title="Volume de Treino (Reps Totais)", yaxis_title="Taxa de Acerto nos Estudos (%)", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E0E0E0"))
                st.plotly_chart(fig_c2, use_container_width=True)
    else: st.info("Os algoritmos precisam de dados simultâneos (Dias com registros de Treino E Estudo) para calcular correlações complexas.")

# ==========================================
# ABA 8: GERENCIAR
# ==========================================
with tab_gerenciar:
    if not df_raw.empty:
        st.markdown("### ⚙️ Engine de Banco de Dados (Edição Completa)")
        df_raw['data_formatada'] = pd.to_datetime(df_raw['data']).dt.strftime('%d/%m/%Y')
        
        def formatar_registro(row):
            if row['grupo_muscular'] == 'Nutrição': return "🍏 DIETA"
            elif row['grupo_muscular'] == 'Métricas': return f"⚖️ PESO ({row['peso_corporal']}kg)"
            elif row['grupo_muscular'] == 'Estudos': return f"📚 ESTUDO: {row['exercicio']} ({row['duracao_min']} min)"
            else: return f"🏋️ {row['exercicio']} ({row['repeticoes']} reps)"

        opcoes_registros = df_raw.apply(lambda row: f"ID: {row['id']} | {row['data_formatada']} - {formatar_registro(row)}", axis=1).tolist()
        registro_selecionado = st.selectbox("Selecione o Registro para Editar/Excluir:", opcoes_registros)
        id_real = int(registro_selecionado.split("ID: ")[1].split(" |")[0])
        st.write("---")
        
        row_data = df_raw[df_raw['id'] == id_real].iloc[0]
        is_estudo = row_data['grupo_muscular'] == 'Estudos'
        is_nutricao = row_data['grupo_muscular'] == 'Nutrição'
        is_peso = row_data['grupo_muscular'] == 'Métricas'
        is_treino = not (is_estudo or is_nutricao or is_peso)
        
        extras = row_data['dados_extras']
        if isinstance(extras, str):
            try: extras = json.loads(extras)
            except: extras = {}
        elif not isinstance(extras, dict): extras = {}
            
        if is_estudo:
            is_anki_default = extras.get('fonte_questoes') == 'Anki' or row_data['exercicio'] in DECKS_ANKI
            has_video = int(extras.get('tempo_video', 0)) > 0
            has_questoes = int(extras.get('q_certas', 0)) > 0 or int(extras.get('q_erradas', 0)) > 0

            if is_anki_default: tipo_padrao = "🃏 Revisão (Anki)"
            elif has_video and not has_questoes: tipo_padrao = "🎥 Apenas Vídeo Aula"
            else: tipo_padrao = "📝 Apenas Questões"

            st.write("---")
            tipo_sessao_edit = st.radio(
                "Mudar Tipo de Sessão (Corrija se registrou errado):",
                ["🎥 Apenas Vídeo Aula", "📝 Apenas Questões", "🃏 Revisão (Anki)"],
                index=["🎥 Apenas Vídeo Aula", "📝 Apenas Questões", "🃏 Revisão (Anki)"].index(tipo_padrao),
                horizontal=True, key=f"radio_tipo_edit_{id_real}"
            )

        with st.form(f"form_edit_{id_real}"):
            st.markdown(f"#### ✏️ Editar Dados do Registro (ID: {id_real})")
            c1, c2 = st.columns(2)
            with c1: new_date = st.date_input("Data", value=pd.to_datetime(row_data['data']).date())
            with c2:
                try: time_obj = pd.to_datetime(row_data['horario']).time()
                except: time_obj = (datetime.utcnow() - timedelta(hours=3)).time()
                new_time = st.time_input("Horário", value=time_obj)
            st.write("")
            
            if is_estudo:
                if tipo_sessao_edit == "🃏 Revisão (Anki)":
                    idx_ex = DECKS_ANKI.index(row_data['exercicio']) if row_data['exercicio'] in DECKS_ANKI else 0
                    new_ex = st.selectbox("Deck do Anki", DECKS_ANKI, index=idx_ex)
                    c3, c4 = st.columns(2)
                    with c3:
                        dur_val = row_data.get('duracao_min', 0)
                        new_dur = st.number_input("Tempo Líquido (min)", min_value=0, value=int(dur_val if pd.notnull(dur_val) else 0))
                    with c4:
                        rep_val = row_data.get('repeticoes', 0)
                        new_cartoes = st.number_input("Cartões Revisados", min_value=0, value=int(rep_val if pd.notnull(rep_val) else 0))
                    new_topicos = []; new_certas = 0; new_erradas = 0; new_vid = 0; new_fonte = "Anki"

                elif tipo_sessao_edit == "🎥 Apenas Vídeo Aula":
                    idx_ex = DISCIPLINAS_ESTUDO.index(row_data['exercicio']) if row_data['exercicio'] in DISCIPLINAS_ESTUDO else 0
                    new_ex = st.selectbox("Disciplina", DISCIPLINAS_ESTUDO, index=idx_ex)
                    topicos_disp = ["🎯 Simulado / Visão Geral"] + TOPICOS_EDITAL.get(new_ex, ["Geral"])
                    old_topicos_str = extras.get('topico_edital', 'Geral')
                    old_topicos_list = [t.strip() for t in old_topicos_str.split(',')] if old_topicos_str else []
                    valid_old_topicos = [t for t in old_topicos_list if t in topicos_disp]
                    new_topicos = st.multiselect("Tópico(s) do Edital", topicos_disp, default=valid_old_topicos)
                    new_vid = st.number_input("Tempo Vídeo (min)", min_value=0, value=int(extras.get('tempo_video', 0)))
                    new_dur = 0; new_certas = 0; new_erradas = 0; new_cartoes = 0; new_fonte = "Não Aplicável"

                elif tipo_sessao_edit == "📝 Apenas Questões":
                    idx_ex = DISCIPLINAS_ESTUDO.index(row_data['exercicio']) if row_data['exercicio'] in DISCIPLINAS_ESTUDO else 0
                    new_ex = st.selectbox("Disciplina", DISCIPLINAS_ESTUDO, index=idx_ex)
                    topicos_disp = ["🎯 Simulado / Visão Geral"] + TOPICOS_EDITAL.get(new_ex, ["Geral"])
                    old_topicos_str = extras.get('topico_edital', 'Geral')
                    old_topicos_list = [t.strip() for t in old_topicos_str.split(',')] if old_topicos_str else []
                    valid_old_topicos = [t for t in old_topicos_list if t in topicos_disp]
                    new_topicos = st.multiselect("Tópico(s) do Edital", topicos_disp, default=valid_old_topicos)
                    c3, c4, c5 = st.columns(3)
                    with c3:
                        dur_val = row_data.get('duracao_min', 0)
                        new_dur = st.number_input("Tempo Líquido (min)", min_value=0, value=int(dur_val if pd.notnull(dur_val) else 0))
                    with c4:
                        new_certas = st.number_input("Acertos", min_value=0, value=int(extras.get('q_certas', 0)))
                        new_erradas = st.number_input("Erros", min_value=0, value=int(extras.get('q_erradas', 0)))
                    with c5:
                        old_fonte = extras.get('fonte_questoes', 'Não Informada')
                        idx_fonte = FONTES_QUESTOES.index(old_fonte) if old_fonte in FONTES_QUESTOES else 0
                        new_fonte = st.selectbox("Fonte das Questões", FONTES_QUESTOES, index=idx_fonte)
                    new_vid = 0; new_cartoes = 0
                
            elif is_treino:
                idx_ex = TODOS_EXERCICIOS.index(row_data['exercicio']) if row_data['exercicio'] in TODOS_EXERCICIOS else 0
                new_ex = st.selectbox("Exercício", TODOS_EXERCICIOS, index=idx_ex)
                c3, c4, c5 = st.columns(3)
                with c3:
                    ser_val = row_data.get('series', 0)
                    new_series = st.number_input("Séries", min_value=0, value=int(ser_val if pd.notnull(ser_val) else 0))
                    rep_val = row_data.get('repeticoes', 0)
                    new_reps = st.number_input("Repetições", min_value=0, value=int(rep_val if pd.notnull(rep_val) else 0))
                    car_val = row_data.get('carga_kg', 0.0)
                    new_carga = st.number_input("Carga (kg)", min_value=0.0, value=float(car_val if pd.notnull(car_val) else 0.0))
                with c4:
                    new_iso = st.number_input("Isometria (seg)", min_value=0, value=int(extras.get('isometria_segundos', 0)))
                    desc_val = row_data.get('descanso_seg', 0)
                    new_desc = st.number_input("Descanso (seg)", min_value=0, value=int(desc_val if pd.notnull(desc_val) else 0))
                with c5:
                    dur_val = row_data.get('duracao_min', 0)
                    new_dur = st.number_input("Duração Cardio (min)", min_value=0, value=int(dur_val if pd.notnull(dur_val) else 0))
                    dist_val = row_data.get('distancia_km', 0.0)
                    new_dist = st.number_input("Distância (km)", min_value=0.0, value=float(dist_val if pd.notnull(dist_val) else 0.0))
                humores = ["Normal", "Foco Extremo", "Motivado", "Cansado", "Estressado"]
                old_humor = extras.get('humor', 'Normal')
                new_humor = st.selectbox("Estado Mental", humores, index=humores.index(old_humor) if old_humor in humores else 0)

            elif is_nutricao:
                st.info("💡 Edite os alimentos listados abaixo (separados por vírgula).")
                new_saudavel = st.text_area("Alimentação Saudável", value=str(row_data['alimentacao_saudavel']))
                new_besteira = st.text_area("Junk Food (Besteirol)", value=str(row_data['alimentacao_besteirol']))
                
            elif is_peso:
                peso_val = row_data.get('peso_corporal', 0.0)
                new_peso = st.number_input("Peso Corporal (kg)", min_value=0.0, value=float(peso_val if pd.notnull(peso_val) else 0.0))

            submit_edit = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)

        if submit_edit:
            update_data = { "data": str(new_date), "horario": str(new_time) }
            if is_estudo:
                update_data["exercicio"] = new_ex
                update_data["duracao_min"] = new_dur
                if tipo_sessao_edit == "🃏 Revisão (Anki)": update_data["repeticoes"] = new_cartoes
                else: update_data["repeticoes"] = new_certas + new_erradas
                extras["topico_edital"] = ", ".join(new_topicos) if new_topicos else ("Revisão Espaçada" if tipo_sessao_edit == "🃏 Revisão (Anki)" else "Geral")
                extras["q_certas"] = new_certas
                extras["q_erradas"] = new_erradas
                extras["tempo_video"] = new_vid
                extras["fonte_questoes"] = new_fonte
                update_data["dados_extras"] = extras
            elif is_treino:
                update_data["exercicio"] = new_ex
                update_data["grupo_muscular"] = next((g for g, l in EXERCICIOS_PRESETADOS.items() if new_ex in l), "Outro")
                update_data["series"] = new_series
                update_data["repeticoes"] = new_reps
                update_data["carga_kg"] = new_carga
                update_data["descanso_seg"] = new_desc
                update_data["duracao_min"] = new_dur
                update_data["distancia_km"] = new_dist
                extras["isometria_segundos"] = new_iso
                extras["humor"] = new_humor
                update_data["dados_extras"] = extras
            elif is_nutricao:
                update_data["alimentacao_saudavel"] = new_saudavel
                update_data["alimentacao_besteirol"] = new_besteira
            elif is_peso:
                update_data["peso_corporal"] = new_peso
            
            supabase.table("treinos").update(update_data).eq("id", id_real).execute()
            st.success("Registro atualizado com sucesso!")
            st.rerun()

        st.write("---")
        with st.container(border=True):
            st.markdown("#### 🗑️ Purge de Registro")
            st.warning("⚠️ DROP irreversível da linha no banco Supabase.")
            if st.button("Executar Delete", type="primary", use_container_width=True):
                supabase.table("treinos").delete().eq("id", id_real).execute()
                st.success("Linha expurgada com sucesso!")
                st.rerun()
    else: st.info("O Banco de Dados está vazio no momento.")
