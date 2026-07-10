import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import plotly.express as px
import json
import time
import os
import random
import base64
import streamlit.components.v1 as components

# --- FUNÇÕES AUXILIARES ---
def safe_get(val, key, default=None):
    if pd.isna(val) or val == "": return default
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
    "Skills / Calistenia": ["Handstand (Parada de Mãos)", "L-Sit", "Planche"]
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

# --- TÓPICOS DO EDITAL POR DISCIPLINA (usado no seletor dinâmico e na Cobertura) ---
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
        "6.3 Reorganização da estrutura de orações e períodos",
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

# Rota estratégica intercalando Exatas, Humanas e TI para evitar fadiga mental
ROTA_ESTRATEGICA = [
    "Matemática e Estatística Aplicada", 
    "Legislação (LAI/Marco Civil/LGPD)", 
    "Banco de Dados (SQL/NoSQL/Big Data)", 
    "Raciocínio Lógico", 
    "Língua Portuguesa", 
    "Ciência de Dados (ML/DL/PLN/Visão)", 
    "Atualidades e IA", 
    "Linguagens (Python/R/Spark/SAS)", 
    "Língua Inglesa" 
]

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
    .neon-card { flex: 1; min-width: 180px; padding: 20px; border-radius: 10px; color: #E0E0E0; background: #0A0A0A; border-left: 4px solid #333; position: relative; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
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
st.sidebar.markdown("## 🔍 Filtros")
st.sidebar.write("---")

filtro_tempo = st.sidebar.selectbox("Período:", ["Todo o Histórico", "Hoje", "Últimos 7 Dias", "Últimos 30 Dias", "Este Ano"])
filtro_ex = st.sidebar.selectbox("Detalhar Treino Físico:", ["Todos"] + TODOS_EXERCICIOS)
filtro_disc = st.sidebar.selectbox("Detalhar Disciplina:", ["Todas"] + DISCIPLINAS_ESTUDO)

if not df_raw.empty:
    df_raw['data'] = pd.to_datetime(df_raw['data'])
    hoje = pd.Timestamp.today().normalize()
    
    if filtro_tempo == "Hoje":
        df_raw = df_raw[df_raw['data'] == hoje]
    elif filtro_tempo == "Últimos 7 Dias":
        df_raw = df_raw[df_raw['data'] >= (hoje - pd.Timedelta(days=7))]
    elif filtro_tempo == "Últimos 30 Dias":
        df_raw = df_raw[df_raw['data'] >= (hoje - pd.Timedelta(days=30))]
    elif filtro_tempo == "Este Ano":
        df_raw = df_raw[df_raw['data'].dt.year == hoje.year]

if not df_raw.empty:
    df_treinos = df_raw[~df_raw['grupo_muscular'].isin(['Nutrição', 'Métricas', 'Estudos'])].copy()
    df_dieta = df_raw[df_raw['grupo_muscular'] == 'Nutrição'].copy()
    df_estudos = df_raw[df_raw['grupo_muscular'] == 'Estudos'].copy()
else:
    df_treinos = pd.DataFrame()
    df_dieta = pd.DataFrame()
    df_estudos = pd.DataFrame()

if filtro_ex != "Todos" and not df_treinos.empty:
    df_treinos = df_treinos[df_treinos['exercicio'] == filtro_ex].copy()

if filtro_disc != "Todas" and not df_estudos.empty:
    df_estudos = df_estudos[df_estudos['exercicio'] == filtro_disc].copy()

# --- INTERFACE MAIN ---
st.markdown("<h1 style='text-align: center; font-weight: 800; letter-spacing: -1px; color: #FFF;'>⚡ OS/System: Analytics</h1>", unsafe_allow_html=True)

texto_filtro = ""
if filtro_ex != "Todos" or filtro_disc != "Todas" or filtro_tempo != "Todo o Histórico":
    texto_filtro = f"<p style='text-align: center; color: #009CA6; margin-top: -15px;'>[ Filtros ativos: {filtro_tempo} ]</p>"

st.markdown(texto_filtro, unsafe_allow_html=True)
st.write("")

# Abas expandidas
tab_registro, tab_dash_treino, tab_dieta, tab_peso, tab_estudo, tab_dash_estudo, tab_cruzamento, tab_gerenciar = st.tabs([
    "📝 Treino", "📊 Dash Físico", "🥗 Dieta", "⚖️ Peso", "📚 Estudar", "📈 Dash Estudos", "🧬 Cruzamentos", "⚙️ Config"
])

# ==========================================
# ABA 1: REGISTRO DE TREINO 
# ==========================================
with tab_registro:
    with st.form("registro_treino", clear_on_submit=True):
        st.markdown("<h3 style='margin-bottom: 20px; color: #009CA6;'>🏋️ Inserir Dados Físicos</h3>", unsafe_allow_html=True)
        
        c_top1, c_top2, c_top3 = st.columns([2, 1, 1])
        with c_top1: data_treino = st.date_input("Data do Treino", value=datetime.today())
            
        agora = datetime.now()
        with c_top2: hora = st.selectbox("Hora", [f"{i:02d}" for i in range(24)], index=agora.hour)
        with c_top3: minuto = st.selectbox("Min.", [f"{i:02d}" for i in range(60)], index=agora.minute)
            
        horario = f"{hora}:{minuto}:00"
        st.markdown("---")
        
        tipo_treino = st.radio("Selecione a Modalidade do Exercício:", ["Hipertrofia / Força Pura", "Skill / Isometria (Ex: Handstand)"], horizontal=True)
        st.write("")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            exercicio_input = st.selectbox("Exercício", TODOS_EXERCICIOS)
            duracao = st.number_input("Duração Cardio (min)", min_value=0)
            
        if "Hipertrofia" in tipo_treino:
            with c2:
                series = st.number_input("Séries", min_value=1, value=1, step=1)
                reps = st.number_input("Repetições (Total)", min_value=0, step=1)
            with c3:
                carga = st.number_input("Carga (kg)", min_value=0.0)
                intervalo = st.number_input("Intervalo (seg)", min_value=0, step=15)
                distancia = st.number_input("Distância Cardio (km)", min_value=0.0)
            isometria_tentativas, isometria_segundos = 0, 0
        else:
            with c2:
                isometria_tentativas = st.number_input("Tentativas / Entradas", min_value=1, value=1, step=1)
                isometria_segundos = st.number_input("Tempo Máx Sustentado (segundos)", min_value=0, step=1)
            with c3:
                intervalo = st.number_input("Intervalo (seg)", min_value=0, step=15)
                distancia = 0.0
            series, reps, carga = 0, 0, 0.0
            
        st.markdown("---")
        humor = st.selectbox("Estado Mental no Treino", ["Normal", "Foco Extremo", "Motivado", "Cansado", "Estressado"])
        
        if st.form_submit_button("🚀 Gravar Treino", use_container_width=True):
            grupo = next((g for g, l in EXERCICIOS_PRESETADOS.items() if exercicio_input in l), "Outro")
            
            mochila_json = {
                "humor": humor,
                "modalidade": "Skill" if "Skill" in tipo_treino else "Hipertrofia",
                "isometria_tentativas": isometria_tentativas,
                "isometria_segundos": isometria_segundos
            }
            
            dados = {
                "data": str(data_treino), "horario": str(horario), "grupo_muscular": grupo,
                "exercicio": exercicio_input, "series": int(series), "repeticoes": int(reps),
                "carga_kg": float(carga), "descanso_seg": int(intervalo), "duracao_min": int(duracao),
                "distancia_km": float(distancia), "alimentacao_saudavel": "", "alimentacao_besteirol": "",
                "peso_corporal": 0.0, 
                "dados_extras": mochila_json 
            }
            supabase.table("treinos").insert(dados).execute()
            st.success("Dados físicos processados e salvos!")
            st.rerun()

# ==========================================
# ABA 2: DASHBOARD FÍSICO
# ==========================================
with tab_dash_treino:
    if not df_treinos.empty:
        df_treinos['reps_totais'] = df_treinos['repeticoes']
        df_treinos['reps_por_serie'] = df_treinos.apply(lambda row: row['repeticoes'] / row['series'] if row['series'] > 0 else 0, axis=1)
        
        total_dias = len(df_treinos['data'].unique())
        total_reps = int(df_treinos['reps_totais'].sum())
        carga_max = df_treinos['carga_kg'].max()
        
        st.markdown(f"""
        <div class="card-container">
            <div class="neon-card card-cyan">
                <div class="card-title">🏆 DIAS TREINADOS</div>
                <div class="card-value">{total_dias}</div>
            </div>
            <div class="neon-card card-emerald">
                <div class="card-title">🔥 REPETIÇÕES (TOTAL)</div>
                <div class="card-value">{total_reps}</div>
            </div>
            <div class="neon-card card-violet">
                <div class="card-title">💪 CARGA MÁXIMA</div>
                <div class="card-value">{carga_max:.1f} kg</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🎛️ Controles Visuais")
        c_ctrl1, c_ctrl2 = st.columns(2)
        with c_ctrl1:
            ex_selecionados = st.multiselect("Quais exercícios visualizar?", options=TODOS_EXERCICIOS, default=[])
        with c_ctrl2:
            st.write("") 
            mostrar_peso_corporal = st.checkbox("Incluir gráfico de Evolução do Peso Corporal", value=True)
            
        st.write("---")
        df_grafico_reps = df_treinos.copy()
        if ex_selecionados: df_grafico_reps = df_grafico_reps[df_grafico_reps['exercicio'].isin(ex_selecionados)]

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
            with st.container(border=True):
                st.markdown(f"#### 📊 Volume (Reps) por Dia")
                if not df_grafico_reps.empty:
                    dias_map = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sáb', 6: 'Dom'}
                    df_grafico_reps['dia_formatado'] = df_grafico_reps['data'].dt.weekday.map(dias_map) + df_grafico_reps['data'].dt.strftime(' (%d/%m)')
                    df_reps_dia = df_grafico_reps.groupby(['data', 'dia_formatado'], as_index=False)['reps_totais'].sum().sort_values('data')

                    fig_reps = px.bar(df_reps_dia, x='dia_formatado', y='reps_totais', text_auto=True)
                    fig_reps.update_traces(marker_color='#009CA6', textfont_color='white')
                    fig_reps.update_layout(xaxis_title="", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E0E0E0"), margin=dict(l=0, r=0, t=20, b=0), xaxis=dict(type='category', showgrid=False), yaxis=dict(showgrid=True, gridcolor="#1F1F1F"))
                    st.plotly_chart(fig_reps, use_container_width=True)
                else: st.info("Nenhum exercício selecionado/encontrado.")

    else: st.warning("Nenhum treino encontrado para o filtro selecionado.")

# ==========================================
# ABA 3: REGISTRO DE ALIMENTAÇÃO
# ==========================================
with tab_dieta:
    with st.form("registro_dieta", clear_on_submit=True):
        st.markdown("<h3 style='margin-bottom: 20px; color: #10B981;'>🍏 Diário Alimentar</h3>", unsafe_allow_html=True)
        data_dieta = st.date_input("Data da Refeição", value=datetime.today(), key="data_dieta")
        
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
            
            dados_dieta = {
                "data": str(data_dieta), "horario": "00:00:00", 
                "grupo_muscular": "Nutrição", "exercicio": "Refeição Diária", 
                "series": 0, "repeticoes": 0, "carga_kg": 0, "descanso_seg": 0, "duracao_min": 0, "distancia_km": 0,
                "alimentacao_saudavel": ", ".join(lista_s), "alimentacao_besteirol": ", ".join(lista_b),
                "peso_corporal": 0.0, "dados_extras": {}
            }
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
        with c_p1: data_peso = st.date_input("Data da Pesagem", value=datetime.today(), key="data_peso")
        with c_p2: peso_corporal_input = st.number_input("Seu Peso (kg)", min_value=0.0, step=0.1)

        if st.form_submit_button("💾 Atualizar Biometria", use_container_width=True):
            dados_peso = {
                "data": str(data_peso), "horario": "00:00:00", 
                "grupo_muscular": "Métricas", "exercicio": "Peso Diário", 
                "series": 0, "repeticoes": 0, "carga_kg": 0, "descanso_seg": 0, "duracao_min": 0, "distancia_km": 0,
                "alimentacao_saudavel": "", "alimentacao_besteirol": "",
                "peso_corporal": float(peso_corporal_input), "dados_extras": {}
            }
            supabase.table("treinos").insert(dados_peso).execute()
            st.success("Métrica salva com sucesso!")
            st.rerun()

# ==========================================
# ABA 5: REGISTRO DE ESTUDOS E POMODORO
# ==========================================
with tab_estudo:
    st.markdown("<h3 style='margin-bottom: 20px; color: #009CA6;'>📚 Central de Foco: Operação FGV</h3>", unsafe_allow_html=True)
    
    # --- MOTOR DE RECOMENDAÇÃO INTELIGENTE ---
    prox_disciplina = ROTA_ESTRATEGICA[0]
    if not df_estudos.empty:
        # Pega a última disciplina estudada validando datas
        ultima_disciplina = df_estudos.sort_values(by=['data', 'horario'], ascending=[False, False]).iloc[0]['exercicio']
        if ultima_disciplina in ROTA_ESTRATEGICA:
            idx_atual = ROTA_ESTRATEGICA.index(ultima_disciplina)
            idx_prox = (idx_atual + 1) % len(ROTA_ESTRATEGICA)
            prox_disciplina = ROTA_ESTRATEGICA[idx_prox]
            
    st.markdown(f"""
    <div style="background-color: #0A0A0A; border-left: 4px solid #8B5CF6; padding: 18px; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
        <span style="color: #009CA6; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px;">🧭 Bússola Estratégica (Recomendação)</span><br>
        <span style="color: #AAA; font-size: 14px;">Para evitar fadiga cognitiva, seu próximo alvo no ciclo de 30 dias deve ser:</span><br>
        <span style="color: #FFF; font-size: 24px; font-weight: 700; display: inline-block; margin-top: 8px;">🎯 {prox_disciplina}</span>
    </div>
    """, unsafe_allow_html=True)
    # -----------------------------------------------

    col_pomodoro, col_registro = st.columns([1, 1.5], gap="large")
    
    with col_pomodoro:
        with st.container(border=True):
            st.markdown("#### ⏱️ Modos de Foco")
            
            # --- MOTOR DE RECOMPENSA (Carrega a Base64 para os dois modos) ---
            pasta_videos = "edits_motivacionais"
            video_base64 = ""
            try:
                videos = [v for v in os.listdir(pasta_videos) if v.endswith(".mp4")]
                if videos:
                    video_escolhido = random.choice(videos)
                    caminho_video = os.path.join(pasta_videos, video_escolhido)
                    with open(caminho_video, 'rb') as v:
                        video_base64 = base64.b64encode(v.read()).decode('utf-8')
            except FileNotFoundError:
                pass

            video_tag = (
                "<video class='cinema-video' id='vid-player' controls autoplay>"
                f"<source src='data:video/mp4;base64,{video_base64}' type='video/mp4'></video>"
            ) if video_base64 else "<p style='color:#E0E0E0;'>Nenhum vídeo encontrado, mas o ciclo terminou!</p>"
            # ------------------------------------------------------------------

            tipo_timer = st.radio("Selecione o Protocolo:", ["🍅 Pomodoro (Estudo Longo)", "⏱️ Cronômetro (Questões)"], horizontal=False)
            st.write("---")

            if "Pomodoro" in tipo_timer:
                c_pom1, c_pom2 = st.columns(2)
                with c_pom1:
                    minutos_pomodoro = st.number_input("Minutos", min_value=0, value=50, step=1)
                with c_pom2:
                    segundos_pomodoro = st.number_input("Segundos", min_value=0, max_value=59, value=0, step=5)
                    
                relogio_placeholder = st.empty()
                
                if st.button("▶️ Iniciar Ciclo", use_container_width=True):
                    total_segundos = int((minutos_pomodoro * 60) + segundos_pomodoro)
                    
                    if total_segundos > 0:
                        for t in range(total_segundos, -1, -1):
                            mins, secs = divmod(t, 60)
                            relogio_placeholder.markdown(
                                f"<h1 style='text-align: center; font-size: 65px; color: #009CA6; margin: 0; text-shadow: 0 0 15px rgba(0,156,166,0.5);'>{mins:02d}:{secs:02d}</h1>", 
                                unsafe_allow_html=True
                            )
                            time.sleep(1)
                        
                        relogio_placeholder.empty()
                        st.success("🎯 Ciclo encerrado! Recompensa ativada.")
                        
                        html_cinema = f"""
                        <script>
                        (function() {{
                            var parentDoc = window.parent.document;
                            var oldOverlay = parentDoc.getElementById('cinema-modal');
                            if (oldOverlay) oldOverlay.remove();
                            var oldStyle = parentDoc.getElementById('cinema-style');
                            if (oldStyle) oldStyle.remove();

                            var style = parentDoc.createElement('style');
                            style.id = 'cinema-style';
                            style.innerHTML = `
                                .cinema-overlay {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background-color: rgba(5, 5, 5, 0.95); z-index: 999999; display: flex; flex-direction: column; justify-content: center; align-items: center; backdrop-filter: blur(10px); }}
                                .cinema-video {{ width: 80vw; max-height: 75vh; border: 2px solid #009CA6; border-radius: 12px; box-shadow: 0 0 50px rgba(0, 156, 166, 0.5); outline: none; }}
                                .btn-fechar {{ margin-top: 25px; padding: 12px 30px; background-color: #0A0A0A; color: #009CA6; border: 2px solid #009CA6; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: all 0.3s ease; font-family: sans-serif; }}
                                .btn-fechar:hover {{ background-color: #009CA6; color: #000; box-shadow: 0 0 20px rgba(0,156,166,0.6); }}
                            `;
                            parentDoc.head.appendChild(style);

                            var overlay = parentDoc.createElement('div');
                            overlay.className = 'cinema-overlay';
                            overlay.id = 'cinema-modal';
                            overlay.innerHTML = `
                                <h2 style="color: #FFF; font-weight: 800; letter-spacing: 2px; margin-bottom: 20px;">⚡ RECOMPENSA DESBLOQUEADA ⚡</h2>
                                {video_tag}
                                <button class="btn-fechar" id="btn-fechar-cinema">FECHAR E VOLTAR AO MODO OPERANTE</button>
                            `;
                            parentDoc.body.appendChild(overlay);

                            var btnFechar = parentDoc.getElementById('btn-fechar-cinema');
                            btnFechar.addEventListener('click', function() {{
                                var vid = parentDoc.getElementById('vid-player');
                                if (vid) {{ vid.pause(); }}
                                overlay.remove();
                                style.remove();
                            }});

                            try {{
                                var AudioCtxClass = window.parent.AudioContext || window.parent.webkitAudioContext;
                                var audioCtx = new AudioCtxClass();
                                if (audioCtx.state === 'suspended') {{ audioCtx.resume(); }}
                                function playBeep(time, freq, duration) {{
                                    var osc = audioCtx.createOscillator();
                                    var gain = audioCtx.createGain();
                                    osc.connect(gain);
                                    gain.connect(audioCtx.destination);
                                    osc.type = "square";
                                    osc.frequency.setValueAtTime(freq, time);
                                    gain.gain.setValueAtTime(0.1, time);
                                    gain.gain.exponentialRampToValueAtTime(0.001, time + duration);
                                    osc.start(time);
                                    osc.stop(time + duration);
                                }}
                                playBeep(audioCtx.currentTime, 880, 0.15);
                                playBeep(audioCtx.currentTime + 0.3, 880, 0.15);
                                playBeep(audioCtx.currentTime + 0.6, 880, 0.15);
                                playBeep(audioCtx.currentTime + 0.9, 1100, 0.6);
                            }} catch(e) {{ console.log("Audio API Error:", e); }}

                            setTimeout(function() {{
                                var vid = parentDoc.getElementById('vid-player');
                                if (vid) {{ vid.play().catch(function(e) {{ console.log("Autoplay block:", e); }}); }}
                            }}, 1500);
                        }})();
                        </script>
                        """
                        components.html(html_cinema, height=0, width=0)
                    else:
                        st.warning("⏱️ Por favor, defina um tempo maior que zero para o ciclo.")

            else:
                # --- WIDGET DO CRONÔMETRO (HTML/JS INJETADO NO STREAMLIT) ---
                html_cronometro = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{
                            background-color: transparent;
                            color: #E0E0E0;
                            font-family: sans-serif;
                            text-align: center;
                            margin: 0;
                            padding: 0;
                        }}
                        .time {{
                            font-size: 65px;
                            color: #009CA6;
                            text-shadow: 0 0 15px rgba(0,156,166,0.5);
                            font-weight: bold;
                            margin: 10px 0 20px 0;
                        }}
                        .btn-group {{
                            display: flex;
                            justify-content: center;
                            gap: 10px;
                            flex-wrap: wrap;
                        }}
                        .btn {{
                            padding: 10px 20px;
                            background-color: #0A0A0A;
                            color: #009CA6;
                            border: 2px solid #009CA6;
                            border-radius: 8px;
                            cursor: pointer;
                            font-size: 14px;
                            font-weight: bold;
                            transition: all 0.3s;
                        }}
                        .btn:hover {{
                            background-color: #009CA6;
                            color: #000;
                            box-shadow: 0 0 10px rgba(0,156,166,0.5);
                        }}
                        .btn-finish {{
                            border-color: #8B5CF6;
                            color: #8B5CF6;
                        }}
                        .btn-finish:hover {{
                            background-color: #8B5CF6;
                            color: #000;
                            box-shadow: 0 0 10px rgba(139,92,246,0.5);
                        }}
                    </style>
                </head>
                <body>
                    <div class="time" id="display">00:00</div>
                    <div class="btn-group">
                        <button class="btn" onclick="start()">▶️ Iniciar</button>
                        <button class="btn" onclick="pause()">⏸️ Pausar</button>
                        <button class="btn btn-finish" onclick="finish()">✅ Finalizar & Edit</button>
                    </div>

                    <script>
                        let timer;
                        let secs = 0;
                        let running = false;
                        const display = document.getElementById('display');

                        function formatTime(s) {{
                            const m = Math.floor(s / 60);
                            const rs = s % 60;
                            return (m < 10 ? '0' : '') + m + ':' + (rs < 10 ? '0' : '') + rs;
                        }}

                        function start() {{
                            if(!running) {{
                                running = true;
                                timer = setInterval(() => {{ secs++; display.innerText = formatTime(secs); }}, 1000);
                            }}
                        }}

                        function pause() {{
                            running = false;
                            clearInterval(timer);
                        }}

                        function finish() {{
                            if(secs === 0) return; // Evita disparar se não cronometrou nada
                            pause();
                            
                            var parentDoc = window.parent.document;
                            var oldOverlay = parentDoc.getElementById('cinema-modal');
                            if (oldOverlay) oldOverlay.remove();
                            var oldStyle = parentDoc.getElementById('cinema-style');
                            if (oldStyle) oldStyle.remove();

                            var style = parentDoc.createElement('style');
                            style.id = 'cinema-style';
                            style.innerHTML = `
                                .cinema-overlay {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background-color: rgba(5, 5, 5, 0.95); z-index: 999999; display: flex; flex-direction: column; justify-content: center; align-items: center; backdrop-filter: blur(10px); }}
                                .cinema-video {{ width: 80vw; max-height: 75vh; border: 2px solid #009CA6; border-radius: 12px; box-shadow: 0 0 50px rgba(0, 156, 166, 0.5); outline: none; }}
                                .btn-fechar {{ margin-top: 25px; padding: 12px 30px; background-color: #0A0A0A; color: #009CA6; border: 2px solid #009CA6; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: all 0.3s ease; font-family: sans-serif; }}
                                .btn-fechar:hover {{ background-color: #009CA6; color: #000; box-shadow: 0 0 20px rgba(0,156,166,0.6); }}
                            `;
                            parentDoc.head.appendChild(style);

                            var overlay = parentDoc.createElement('div');
                            overlay.className = 'cinema-overlay';
                            overlay.id = 'cinema-modal';
                            
                            // Injete a mesma tag de vídeo carregada no Python
                            overlay.innerHTML = `
                                <h2 style="color: #FFF; font-weight: 800; letter-spacing: 2px; margin-bottom: 20px;">⚡ TEMPO DE RESOLUÇÃO: ${{formatTime(secs)}} ⚡</h2>
                                {video_tag}
                                <button class="btn-fechar" id="btn-fechar-cinema">FECHAR E VOLTAR AO MODO OPERANTE</button>
                            `;
                            parentDoc.body.appendChild(overlay);

                            var btnFechar = parentDoc.getElementById('btn-fechar-cinema');
                            btnFechar.addEventListener('click', function() {{
                                var vid = parentDoc.getElementById('vid-player');
                                if (vid) {{ vid.pause(); }}
                                overlay.remove();
                                style.remove();
                                secs = 0; // Zera o cronômetro local após fechar o edit
                                display.innerText = "00:00";
                            }});

                            // Som
                            try {{
                                var AudioCtxClass = window.parent.AudioContext || window.parent.webkitAudioContext;
                                var audioCtx = new AudioCtxClass();
                                if (audioCtx.state === 'suspended') {{ audioCtx.resume(); }}
                                function playBeep(time, freq, duration) {{
                                    var osc = audioCtx.createOscillator();
                                    var gain = audioCtx.createGain();
                                    osc.connect(gain);
                                    gain.connect(audioCtx.destination);
                                    osc.type = "square";
                                    osc.frequency.setValueAtTime(freq, time);
                                    gain.gain.setValueAtTime(0.1, time);
                                    gain.gain.exponentialRampToValueAtTime(0.001, time + duration);
                                    osc.start(time);
                                    osc.stop(time + duration);
                                }}
                                playBeep(audioCtx.currentTime, 880, 0.15);
                                playBeep(audioCtx.currentTime + 0.3, 1100, 0.6);
                            }} catch(e) {{ console.log("Audio API error:", e); }}

                            setTimeout(function() {{
                                var vid = parentDoc.getElementById('vid-player');
                                if (vid) {{ vid.play().catch(e => console.log("Autoplay block:", e)); }}
                            }}, 1500);
                        }}
                    </script>
                </body>
                </html>
                """
                components.html(html_cronometro, height=180)

    with col_registro:
        st.markdown("#### 📝 Input de Produtividade")

        # Disciplina fica FORA do form para que, ao trocar, a lista de Tópicos do Edital
        # (que depende da disciplina escolhida) seja atualizada na hora.
        index_recomendado = DISCIPLINAS_ESTUDO.index(prox_disciplina) if prox_disciplina in DISCIPLINAS_ESTUDO else 0
        disciplina = st.selectbox("Módulo / Disciplina", DISCIPLINAS_ESTUDO, index=index_recomendado, key="disciplina_estudo_select")
        topicos_disponiveis = TOPICOS_EDITAL.get(disciplina, ["Geral"])

        with st.form("registro_estudo", clear_on_submit=True):
            c_est1, c_est2 = st.columns(2)
            with c_est1:
                data_estudo = st.date_input("Data da Sessão", value=datetime.today())
                topico_edital = st.selectbox("📖 Tópico do Edital", topicos_disponiveis)
                tempo_estudo = st.number_input("Tempo Líquido (min)", min_value=0, step=15)
            with c_est2:
                certas = st.number_input("✅ Questões Corretas", min_value=0, step=1)
                erradas = st.number_input("❌ Questões Erradas", min_value=0, step=1)
                
            detalhe_extra = st.text_input("Detalhe / Micro-tópico (opcional)", placeholder="Ex: Pandas groupby, exercício específico...")
            humor_estudo = st.selectbox("Estado de Fluxo", ["Foco Extremo", "Alto", "Médio", "Baixo", "Disperso/Brain Fog"])

            if st.form_submit_button("💾 Computar Sessão", use_container_width=True):
                total_q = certas + erradas
                topico_final = f"{topico_edital} — {detalhe_extra.strip()}" if detalhe_extra.strip() else topico_edital
                mochila_estudo_json = {
                    "humor_foco": humor_estudo,
                    "topico": topico_final,
                    "topico_edital": topico_edital,
                    "q_certas": certas,
                    "q_erradas": erradas
                }
                
                dados_estudo = {
                    "data": str(data_estudo), "horario": datetime.now().strftime("%H:%M:%S"), 
                    "grupo_muscular": "Estudos", "exercicio": disciplina, 
                    "series": 0, "repeticoes": int(total_q), 
                    "carga_kg": 0.0, "descanso_seg": 0, "duracao_min": int(tempo_estudo),
                    "distancia_km": 0.0, "alimentacao_saudavel": "", "alimentacao_besteirol": "",
                    "peso_corporal": 0.0, "dados_extras": mochila_estudo_json 
                }
                supabase.table("treinos").insert(dados_estudo).execute()
                st.success("Arquivado na base de conhecimento!")
                st.rerun()

# ==========================================
# ABA 6: DASHBOARD DE ESTUDOS
# ==========================================
with tab_dash_estudo:
    st.markdown("### 📈 Analytics Acadêmico")
    if not df_estudos.empty:
        df_estudos['q_certas'] = df_estudos['dados_extras'].apply(lambda x: safe_get(x, 'q_certas', 0))
        df_estudos['q_erradas'] = df_estudos['dados_extras'].apply(lambda x: safe_get(x, 'q_erradas', 0))
        df_estudos['topico'] = df_estudos['dados_extras'].apply(lambda x: safe_get(x, 'topico', ''))
        
        total_certas = df_estudos['q_certas'].sum()
        total_erradas = df_estudos['q_erradas'].sum()
        total_questoes = int(df_estudos['repeticoes'].sum()) 
        
        taxa_acerto = (total_certas / (total_certas + total_erradas) * 100) if (total_certas + total_erradas) > 0 else 0
        
        tempo_total_min = int(df_estudos['duracao_min'].sum())
        
        st.markdown(f"""
        <div class="card-container">
            <div class="neon-card card-cyan">
                <div class="card-title">⏳ HORAS LÍQUIDAS</div>
                <div class="card-value">{(tempo_total_min / 60):.1f}h</div>
            </div>
            <div class="neon-card card-violet">
                <div class="card-title">🎯 TAXA DE ACERTO GLOBAL</div>
                <div class="card-value">{taxa_acerto:.1f}%</div>
            </div>
            <div class="neon-card card-emerald">
                <div class="card-title">📝 BATERIA DE QUESTÕES</div>
                <div class="card-value">{total_questoes}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown("#### 🧠 Sistema de Revisão Espaçada Ativa")
        df_valid_topics = df_estudos[(df_estudos['topico'] != '') & (df_estudos['topico'].notna())].copy()
        
        if not df_valid_topics.empty:
            last_studied = df_valid_topics.groupby(['exercicio', 'topico'], as_index=False)['data'].max()
            last_studied['dias_passados'] = (pd.Timestamp.today().normalize() - pd.to_datetime(last_studied['data'])).dt.days
            
            revisoes_hoje = last_studied[last_studied['dias_passados'].isin([1, 7, 30, 31])]
            
            if not revisoes_hoje.empty:
                for _, row in revisoes_hoje.iterrows():
                    st.warning(f"🔔 **{row['exercicio']}**: Revisar '{row['topico']}' (Visto há {row['dias_passados']} dia(s))")
            else:
                st.info("✔️ Nada pendente no algoritmo de revisão para hoje. Foco no avanço do edital!")
        else:
            st.info("Cadastre os 'Micro-tópicos' nas próximas sessões para a IA calcular suas janelas de revisão.")
        
        st.write("")
        c_dash_e1, c_dash_e2 = st.columns(2)
        with c_dash_e1:
            with st.container(border=True):
                st.markdown("#### ⏳ Alocação de Tempo (Horas)")
                df_disc = df_estudos.groupby('exercicio', as_index=False)['duracao_min'].sum()
                df_disc['horas'] = df_disc['duracao_min'] / 60
                fig_d = px.pie(df_disc, values='horas', names='exercicio', hole=0.5, color_discrete_sequence=px.colors.sequential.Teal)
                fig_d.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E0E0E0"), margin=dict(l=0, r=0, t=10, b=10))
                st.plotly_chart(fig_d, use_container_width=True)

        with c_dash_e2:
            with st.container(border=True):
                st.markdown("#### 📊 Taxa de Acerto por Disciplina")
                df_acertos = df_estudos.groupby('exercicio', as_index=False)[['q_certas', 'q_erradas']].sum()
                df_acertos['total'] = df_acertos['q_certas'] + df_acertos['q_erradas']
                df_acertos = df_acertos[df_acertos['total'] > 0] 
                
                if not df_acertos.empty:
                    df_acertos['% Acerto'] = (df_acertos['q_certas'] / df_acertos['total']) * 100
                    fig_a = px.bar(df_acertos, x='exercicio', y='% Acerto', text_auto='.1f', color='% Acerto', color_continuous_scale="Teal")
                    fig_a.update_layout(xaxis_title="", yaxis_title="%", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E0E0E0"), coloraxis_showscale=False)
                    st.plotly_chart(fig_a, use_container_width=True)
                else:
                    st.info("Registre 'Questões Corretas/Erradas' para gerar este gráfico.")
    else:
        st.warning("Sem dados de estudo arquivados.")

# ==========================================
# ABA 7: CRUZAMENTO DE DADOS 
# ==========================================
with tab_cruzamento:
    st.markdown("### 🧬 Data Lab: Cruzamento de Variáveis")
    st.write("Identifique padrões ocultos entre sua rotina física e seu rendimento cognitivo.")
    
    if not df_raw.empty and not df_estudos.empty and not df_treinos.empty:
        df_t_dia = df_treinos.groupby('data', as_index=False).agg(
            total_reps=('repeticoes', 'sum'),
            treinou=('exercicio', 'count')
        )
        
        df_e_dia = df_estudos.groupby('data', as_index=False).agg(
            minutos_estudados=('duracao_min', 'sum'),
            total_certas=('q_certas', 'sum'),
            total_erradas=('q_erradas', 'sum')
        )
        
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
    else:
        st.info("Os algoritmos precisam de dados simultâneos (Dias com registros de Treino E Estudo) para calcular correlações complexas.")

# ==========================================
# ABA 8: GERENCIAR
# ==========================================
with tab_gerenciar:
    if not df_raw.empty:
        st.markdown("### ⚙️ Engine de Banco de Dados")
        df_raw['data_formatada'] = pd.to_datetime(df_raw['data']).dt.strftime('%d/%m/%Y')
        
        def formatar_registro(row):
            if row['grupo_muscular'] == 'Nutrição': return "🍏 DIETA"
            elif row['grupo_muscular'] == 'Métricas': return f"⚖️ PESO ({row['peso_corporal']}kg)"
            elif row['grupo_muscular'] == 'Estudos': return f"📚 ESTUDO: {row['exercicio']} ({row['duracao_min']} min)"
            else: return f"🏋️ {row['exercicio']}"

        opcoes_registros = df_raw.apply(lambda row: f"ID: {row['id']} | {row['data_formatada']} - {formatar_registro(row)}", axis=1).tolist()
        
        registro_selecionado = st.selectbox("Selecione a Entidade de Dados:", opcoes_registros)
        id_real = int(registro_selecionado.split("ID: ")[1].split(" |")[0])
        
        st.write("---")
        col_edit, col_del = st.columns(2)
        
        with col_edit:
            with st.container(border=True):
                st.markdown("#### ✏️ Alterar Nomenclatura")
                registro_df = df_raw[df_raw['id'] == id_real].iloc[0]
                is_estudo = registro_df['grupo_muscular'] == 'Estudos'
                opcoes_renomear = DISCIPLINAS_ESTUDO if is_estudo else TODOS_EXERCICIOS
                
                novo_nome = st.selectbox("Mudar para qual?", opcoes_renomear)
                if st.button("Aplicar Patch", use_container_width=True):
                    novo_grupo = "Estudos" if is_estudo else next((g for g, l in EXERCICIOS_PRESETADOS.items() if novo_nome in l), "Outro")
                    supabase.table("treinos").update({"exercicio": novo_nome, "grupo_muscular": novo_grupo}).eq("id", id_real).execute()
                    st.success(f"Cluster atualizado: {novo_nome}")
                    st.rerun()

        with col_del:
            with st.container(border=True):
                st.markdown("#### 🗑️ Purge de Registro")
                st.warning("⚠️ DROP irreversível da linha no banco Supabase.")
                if st.button("Executar Delete", type="primary", use_container_width=True):
                    supabase.table("treinos").delete().eq("id", id_real).execute()
                    st.success("Linha expurgada com sucesso!")
                    st.rerun()
