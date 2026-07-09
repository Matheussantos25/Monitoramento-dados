import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import plotly.express as px
import json
import time

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
    "Rosto": ["Massagem Facial", "Mewing com borracha"]
}

TODOS_EXERCICIOS = [ex for lista in EXERCICIOS_PRESETADOS.values() for ex in lista]
TODOS_EXERCICIOS.sort()

ALIMENTOS_SAUDAVEIS = ["Banana", "Uva", "Maçã", "Laranja", "Melão", "Melancia", "Mirtilo", "Ovo", "Frango", "Aveia", "Whey"]
ALIMENTOS_SAUDAVEIS.sort()

ALIMENTOS_BESTEIROL = ["Refrigerante", "Hambúrguer", "Pizza", "Lasanha", "Churros", "Pastel", "Coxinha", "Sorvete", "Batata Frita", "Sonho de Valsa", "Biscoito Recheado", "Chocotone"]
ALIMENTOS_BESTEIROL.sort()

# --- DISCIPLINAS DO EDITAL FGV ---
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

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Monitoramento Físico & Mental", page_icon="⚡", layout="wide")

# --- INJEÇÃO DE CSS PREMIUM ---
st.markdown("""
<style>
    .stApp { background-color: #0A0A0A !important; }
    h1, h2, h3, h4, p, label, span, .stMarkdown { color: #EDEDED !important; }
    
    .stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input, .stTimeInput input, [data-baseweb="select"] > div {
        background-color: #171717 !important;
        color: #EDEDED !important;
        border: 1px solid #262626 !important;
        border-radius: 8px !important;
    }

    [data-testid="stForm"], div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: #111111 !important;
        border: 1px solid #262626 !important;
        border-radius: 12px !important;
        padding: 24px !important;
    }

    /* === CARTÕES CUSTOMIZADOS NEON === */
    .card-container { display: flex; gap: 15px; justify-content: space-between; margin-bottom: 25px; flex-wrap: wrap; }
    .neon-card { flex: 1; min-width: 200px; padding: 20px; border-radius: 12px; color: white; font-family: sans-serif; position: relative; overflow: hidden; }
    .neon-card .card-title { font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; opacity: 0.9; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;}
    .neon-card .card-value { font-size: 32px; font-weight: 800; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
    
    .card-yellow { background: linear-gradient(135deg, #F9D423 0%, #FF4E50 100%); box-shadow: 0 4px 20px rgba(255, 78, 80, 0.4); }
    .card-red { background: linear-gradient(135deg, #FF416C 0%, #FF4B2B 100%); box-shadow: 0 4px 20px rgba(255, 65, 108, 0.4); }
    .card-purple { background: linear-gradient(135deg, #B224EF 0%, #7579FF 100%); box-shadow: 0 4px 20px rgba(117, 121, 255, 0.4); }
    .card-blue { background: linear-gradient(135deg, #4FACFE 0%, #00F2FE 100%); box-shadow: 0 4px 20px rgba(0, 242, 254, 0.4); }
    .card-green { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); box-shadow: 0 4px 20px rgba(56, 239, 125, 0.4); }
    
    span[data-baseweb="tag"] { background-color: #FF4B4B !important; color: white !important; }
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

# --- INTERFACE ---
st.markdown("<h1 style='text-align: center; font-weight: 800; letter-spacing: -1px;'>⚡ Monitoramento Físico & Mental</h1>", unsafe_allow_html=True)
if filtro_ex != "Todos" or filtro_disc != "Todas" or filtro_tempo != "Todo o Histórico":
    st.markdown(f"<p style='text-align: center; color: #FF4B4B; margin-top: -15px;'>Filtros ativos: {filtro_tempo}</p>", unsafe_allow_html=True)
st.write("")

# Abas reorganizadas
tab_registro, tab_dash_treino, tab_dieta, tab_peso, tab_estudo, tab_dash_estudo, tab_gerenciar = st.tabs([
    "📝 Treino", "📊 Dash Físico", "🥗 Dieta", "⚖️ Peso", "📚 Estudar", "📈 Dash Estudos", "⚙️ Config"
])

# ==========================================
# ABA 1: REGISTRO DE TREINO 
# ==========================================
with tab_registro:
    with st.form("registro_treino", clear_on_submit=True):
        st.markdown("<h3 style='margin-bottom: 20px;'>🏋️ Registrar Treino Físico</h3>", unsafe_allow_html=True)
        
        c_top1, c_top2, c_top3 = st.columns([2, 1, 1])
        with c_top1:
            data_treino = st.date_input("Data do Treino", value=datetime.today())
            
        agora = datetime.now()
        with c_top2:
            hora = st.selectbox("Hora", [f"{i:02d}" for i in range(24)], index=agora.hour)
        with c_top3:
            minuto = st.selectbox("Min.", [f"{i:02d}" for i in range(60)], index=agora.minute)
            
        horario = f"{hora}:{minuto}:00"
            
        st.markdown("---")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            exercicio_input = st.selectbox("Exercício", TODOS_EXERCICIOS)
            duracao = st.number_input("Duração Cardio (min)", min_value=0)
        with c2:
            series = st.number_input("Séries", min_value=1, value=1, step=1)
            reps = st.number_input("Repetições (Total)", min_value=0, step=1)
        with c3:
            carga = st.number_input("Carga (kg)", min_value=0.0)
            intervalo = st.number_input("Intervalo (seg)", min_value=0, step=15)
            distancia = st.number_input("Distância Cardio (km)", min_value=0.0)
            
        st.markdown("---")
        st.markdown("#### 🎒 Como você está se sentindo?")
        
        humor = st.selectbox("Humor no Treino", ["Normal", "Motivado", "Cansado", "Estressado"])
        
        if st.form_submit_button("🚀 Salvar Treino", use_container_width=True):
            grupo = next((g for g, l in EXERCICIOS_PRESETADOS.items() if exercicio_input in l), "Outro")
            
            mochila_json = {
                "humor": humor
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
            st.success("Treino salvo com sucesso!")
            st.rerun()

# ==========================================
# ABA 2: DASHBOARD FÍSICO
# ==========================================
with tab_dash_treino:
    if not df_treinos.empty:
        df_treinos['reps_totais'] = df_treinos['repeticoes']
        df_treinos['reps_por_serie'] = df_treinos.apply(lambda row: row['repeticoes'] / row['series'] if row['series'] > 0 else row['repeticoes'], axis=1)
        
        total_dias = len(df_treinos['data'].unique())
        total_reps = int(df_treinos['reps_totais'].sum())
        carga_max = df_treinos['carga_kg'].max()
        media_reps = df_treinos['reps_por_serie'].mean()
        
        st.markdown(f"""
        <div class="card-container">
            <div class="neon-card card-yellow">
                <div class="card-title">🏆 DIAS TREINADOS</div>
                <div class="card-value">{total_dias}</div>
            </div>
            <div class="neon-card card-red">
                <div class="card-title">🔥 REPETIÇÕES (TOTAL)</div>
                <div class="card-value">{total_reps}</div>
            </div>
            <div class="neon-card card-purple">
                <div class="card-title">💪 CARGA MÁXIMA</div>
                <div class="card-value">{carga_max:.1f} kg</div>
            </div>
            <div class="neon-card card-blue">
                <div class="card-title">📈 MÉDIA REPS/SÉRIE</div>
                <div class="card-value">{media_reps:.0f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🎛️ Controles Visuais")
        c_ctrl1, c_ctrl2 = st.columns(2)
        with c_ctrl1:
            ex_selecionados = st.multiselect(
                "Quais exercícios deseja visualizar nas Repetições?", 
                options=TODOS_EXERCICIOS, 
                default=[],
                help="Deixe vazio para considerar todos os exercícios"
            )
        with c_ctrl2:
            st.write("") 
            mostrar_peso_corporal = st.checkbox("Incluir gráfico de Evolução do Peso Corporal", value=True)
            
        st.write("---")

        df_grafico_reps = df_treinos.copy()
        if ex_selecionados:
            df_grafico_reps = df_grafico_reps[df_grafico_reps['exercicio'].isin(ex_selecionados)]

        if mostrar_peso_corporal:
            col_graf1, col_graf2 = st.columns(2)
        else:
            col_graf2 = st.container()
            col_graf1 = None
        
        if mostrar_peso_corporal and col_graf1 is not None:
            with col_graf1:
                with st.container(border=True):
                    st.markdown("#### ⚖️ Evolução do Peso Corporal (kg)")
                    if 'peso_corporal' in df_raw.columns:
                        df_peso = df_raw[df_raw['peso_corporal'] > 0].groupby('data', as_index=False)['peso_corporal'].mean()
                        if not df_peso.empty:
                            df_peso['data_format'] = df_peso['data'].dt.strftime('%d/%m')
                            fig_peso = px.line(df_peso, x='data_format', y='peso_corporal', markers=True, text='peso_corporal')
                            fig_peso.update_traces(line_color='#B224EF', marker=dict(size=10, color='#7579FF'), textposition="top center", texttemplate='%{text:.1f}')
                            fig_peso.update_layout(xaxis_title="", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#EDEDED"), margin=dict(l=0, r=0, t=20, b=20), xaxis=dict(type='category', showgrid=False), yaxis=dict(showgrid=True, gridcolor="#262626"))
                            st.plotly_chart(fig_peso, use_container_width=True)
                        else:
                            st.info("Nenhum registro de peso neste período.")
                    else:
                        st.info("Adicione dados de peso para ver o gráfico.")

        with col_graf2:
            with st.container(border=True):
                st.markdown(f"#### 📊 Repetições por Dia")
                if not df_grafico_reps.empty:
                    dias_map = {0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta', 4: 'Sexta', 5: 'Sábado', 6: 'Domingo'}
                    df_grafico_reps['dia_formatado'] = df_grafico_reps['data'].dt.weekday.map(dias_map) + df_grafico_reps['data'].dt.strftime(' (%d/%m)')
                    df_reps_dia = df_grafico_reps.groupby(['data', 'dia_formatado'], as_index=False)['reps_totais'].sum()
                    df_reps_dia = df_reps_dia.sort_values('data')

                    fig_reps = px.bar(df_reps_dia, x='dia_formatado', y='reps_totais', text_auto=True)
                    fig_reps.update_traces(marker_color='#FF416C')
                    fig_reps.update_layout(xaxis_title="", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#EDEDED"), margin=dict(l=0, r=0, t=20, b=0), xaxis=dict(type='category', showgrid=False), yaxis=dict(showgrid=True, gridcolor="#262626"))
                    st.plotly_chart(fig_reps, use_container_width=True)
                else:
                    st.info("Nenhum exercício selecionado encontrado neste período.")

        col_graf3, col_graf4 = st.columns(2)
        
        with col_graf3:
            with st.container(border=True):
                st.markdown("#### ⏰ Frequência de Treino por Turno")
                def classificar_turno(hora_str):
                    if pd.isna(hora_str) or hora_str == "": return "Outro"
                    try:
                        h = int(str(hora_str).split(":")[0])
                        if 5 <= h < 12: return "Manhã ☀️"
                        elif 12 <= h < 18: return "Tarde 🌇"
                        else: return "Noite 🌙"
                    except:
                        return "Outro"

                df_treinos['turno'] = df_treinos['horario'].apply(classificar_turno)
                df_turno = df_treinos.groupby('turno', as_index=False).size().rename(columns={'size': 'quantidade'})
                
                fig_turno = px.pie(df_turno, values='quantidade', names='turno', hole=0.5, color_discrete_sequence=['#F9D423', '#FF4E50', '#00F2FE'])
                fig_turno.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#111111', width=2)))
                fig_turno.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#EDEDED"), margin=dict(l=0, r=0, t=20, b=0))
                st.plotly_chart(fig_turno, use_container_width=True)

        with col_graf4:
            with st.container(border=True):
                st.markdown("#### 🧠 Humor Durante o Treino")
                if 'dados_extras' in df_treinos.columns:
                    def extrair_humor(x):
                        if isinstance(x, str):
                            try: x = json.loads(x)
                            except: return None
                        if isinstance(x, dict):
                            return x.get('humor', None)
                        return None

                    df_treinos['humor'] = df_treinos['dados_extras'].apply(extrair_humor)
                    df_humor = df_treinos[df_treinos['humor'].notna()].groupby('humor', as_index=False).size().rename(columns={'size': 'quantidade'})
                    
                    if not df_humor.empty:
                        cores_humor = {'Motivado': '#00F2FE', 'Normal': '#F9D423', 'Cansado': '#FF4E50', 'Estressado': '#B224EF'}
                        fig_humor = px.pie(df_humor, values='quantidade', names='humor', hole=0.5, color='humor', color_discrete_map=cores_humor)
                        fig_humor.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#111111', width=2)))
                        fig_humor.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#EDEDED"), margin=dict(l=0, r=0, t=20, b=0))
                        st.plotly_chart(fig_humor, use_container_width=True)
                    else:
                        st.info("Nenhum humor registrado neste período.")
                else:
                    st.info("A mochila de dados não foi encontrada.")

        st.markdown("### 🗄️ Detalhes dos Treinos")
        colunas_remover = ['id', 'created_at', 'alimentacao_saudavel', 'alimentacao_besteirol', 'turno', 'humor', 'dados_extras', 'peso_corporal', 'reps_por_serie', 'dia_formatado']
        df_display = df_treinos.drop(columns=[c for c in colunas_remover if c in df_treinos.columns], errors='ignore')
        df_display['data'] = df_display['data'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_display.sort_values(by='data', ascending=False), use_container_width=True, hide_index=True)
    else:
        st.warning("Nenhum treino encontrado para o filtro selecionado.")

# ==========================================
# ABA 3: REGISTRO DE ALIMENTAÇÃO
# ==========================================
with tab_dieta:
    with st.form("registro_dieta", clear_on_submit=True):
        st.markdown("<h3 style='margin-bottom: 20px;'>🍏 Diário Alimentar</h3>", unsafe_allow_html=True)
        data_dieta = st.date_input("Data da Refeição", value=datetime.today(), key="data_dieta")
        
        c_alim1, c_alim2 = st.columns(2)
        with c_alim1:
            st.markdown("#### 🥗 Saudável")
            alim_s_preset = st.multiselect("Selecione os alimentos:", ALIMENTOS_SAUDAVEIS)
            alim_s_extra = st.text_input("Outros saudáveis (opcional):", placeholder="Ex: Frango, Aveia...")
            
        with c_alim2:
            st.markdown("#### 🍔 Besteirol")
            alim_b_preset = st.multiselect("Selecione as besteiras:", ALIMENTOS_BESTEIROL)
            alim_b_extra = st.text_input("Outras besteiras (opcional):", placeholder="Ex: Cerveja, Doce de leite...")

        if st.form_submit_button("💾 Salvar Refeição", use_container_width=True):
            lista_s = alim_s_preset + ([alim_s_extra.strip()] if alim_s_extra.strip() else [])
            lista_b = alim_b_preset + ([alim_b_extra.strip()] if alim_b_extra.strip() else [])
            final_s = ", ".join(lista_s)
            final_b = ", ".join(lista_b)
            
            dados_dieta = {
                "data": str(data_dieta), "horario": "00:00:00", 
                "grupo_muscular": "Nutrição", "exercicio": "Refeição Diária", 
                "series": 0, "repeticoes": 0, "carga_kg": 0, "descanso_seg": 0, "duracao_min": 0, "distancia_km": 0,
                "alimentacao_saudavel": final_s, "alimentacao_besteirol": final_b,
                "peso_corporal": 0.0,
                "dados_extras": {}
            }
            supabase.table("treinos").insert(dados_dieta).execute()
            st.success("Refeição registrada!")
            st.rerun()
            
    if not df_dieta.empty:
        st.markdown("#### 📜 Histórico de Alimentação")
        df_dieta_view = df_dieta[['data', 'alimentacao_saudavel', 'alimentacao_besteirol']].copy()
        df_dieta_view['data'] = pd.to_datetime(df_dieta_view['data']).dt.strftime('%d/%m/%Y')
        st.dataframe(df_dieta_view.sort_values(by='data', ascending=False), use_container_width=True, hide_index=True)

# ==========================================
# ABA 4: REGISTRO DE PESO
# ==========================================
with tab_peso:
    with st.form("registro_peso", clear_on_submit=True):
        st.markdown("<h3 style='margin-bottom: 20px;'>⚖️ Registrar Peso Diário</h3>", unsafe_allow_html=True)
        st.info("Basta preencher isso uma vez ao dia para acompanhar sua evolução.")
        
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            data_peso = st.date_input("Data da Pesagem", value=datetime.today(), key="data_peso")
        with c_p2:
            peso_corporal_input = st.number_input("Seu Peso (kg)", min_value=0.0, step=0.1)

        if st.form_submit_button("💾 Salvar Peso", use_container_width=True):
            dados_peso = {
                "data": str(data_peso), "horario": "00:00:00", 
                "grupo_muscular": "Métricas", "exercicio": "Peso Diário", 
                "series": 0, "repeticoes": 0, "carga_kg": 0, "descanso_seg": 0, "duracao_min": 0, "distancia_km": 0,
                "alimentacao_saudavel": "", "alimentacao_besteirol": "",
                "peso_corporal": float(peso_corporal_input),
                "dados_extras": {}
            }
            supabase.table("treinos").insert(dados_peso).execute()
            st.success("Peso registrado com sucesso!")
            st.rerun()

# ==========================================
# ABA 5: REGISTRO DE ESTUDOS E POMODORO
# ==========================================
with tab_estudo:
    st.markdown("<h3 style='margin-bottom: 20px;'>📚 Central de Foco e Estudos</h3>", unsafe_allow_html=True)
    
    col_pomodoro, col_registro = st.columns([1, 1.5], gap="large")
    
    # --- ÁREA DO POMODORO ---
    with col_pomodoro:
        with st.container(border=True):
            st.markdown("#### 🍅 Timer Pomodoro")
            minutos_pomodoro = st.number_input("Tempo de Foco (minutos)", min_value=1, value=25, step=5)
            
            relogio_placeholder = st.empty()
            
            if st.button("▶️ Iniciar Pomodoro", use_container_width=True):
                tempo_total_segundos = int(minutos_pomodoro * 60)
                
                for t in range(tempo_total_segundos, -1, -1):
                    mins, secs = divmod(t, 60)
                    relogio_placeholder.markdown(
                        f"<h1 style='text-align: center; font-size: 60px; color: #009CA6; margin: 0;'>{mins:02d}:{secs:02d}</h1>", 
                        unsafe_allow_html=True
                    )
                    time.sleep(1)
                
                st.success("🎯 Pomodoro concluído! Hora de registrar seu progresso ao lado.")

    # --- ÁREA DE REGISTRO ---
    with col_registro:
        with st.form("registro_estudo", clear_on_submit=True):
            st.markdown("#### 📝 Registrar Sessão")
            
            c_estudo1, c_estudo2 = st.columns(2)
            with c_estudo1:
                data_estudo = st.date_input("Data do Estudo", value=datetime.today())
                disciplina = st.selectbox("Disciplina", DISCIPLINAS_ESTUDO)
            
            with c_estudo2:
                tempo_estudo = st.number_input("Tempo Líquido Estudado (min)", min_value=0, step=15)
                questoes_feitas = st.number_input("Questões Resolvidas", min_value=0, step=1)
                
            topico_estudado = st.text_input("Tópico Específico (Opcional)", placeholder="Ex: Limpeza de dados com Pandas, Modelagem DAX...")
            humor_estudo = st.selectbox("Nível de Foco", ["Alto", "Médio", "Baixo", "Disperso"])

            if st.form_submit_button("💾 Salvar Sessão de Estudo", use_container_width=True):
                mochila_estudo_json = {
                    "humor_foco": humor_estudo,
                    "topico": topico_estudado
                }
                
                # CORREÇÃO APLICADA AQUI: strftime("%H:%M:%S") no lugar de strftime("%H:%M:%00")
                dados_estudo = {
                    "data": str(data_estudo), "horario": datetime.now().strftime("%H:%M:%S"), 
                    "grupo_muscular": "Estudos", "exercicio": disciplina, 
                    "series": 0, "repeticoes": int(questoes_feitas), 
                    "carga_kg": 0.0, "descanso_seg": 0, "duracao_min": int(tempo_estudo),
                    "distancia_km": 0.0, "alimentacao_saudavel": "", "alimentacao_besteirol": "",
                    "peso_corporal": 0.0, 
                    "dados_extras": mochila_estudo_json 
                }
                
                supabase.table("treinos").insert(dados_estudo).execute()
                st.success("Sessão de estudo registrada com sucesso!")
                st.rerun()

# ==========================================
# ABA 6: DASHBOARD DE ESTUDOS
# ==========================================
with tab_dash_estudo:
    st.markdown("### 📈 Estatísticas de Estudo")
    if not df_estudos.empty:
        # Cálculos de métricas
        total_dias_estudo = len(df_estudos['data'].unique())
        tempo_total_min = int(df_estudos['duracao_min'].sum())
        tempo_total_horas = tempo_total_min / 60
        total_questoes = int(df_estudos['repeticoes'].sum())
        
        st.markdown(f"""
        <div class="card-container">
            <div class="neon-card card-blue">
                <div class="card-title">⏳ TEMPO TOTAL</div>
                <div class="card-value">{tempo_total_horas:.1f}h</div>
            </div>
            <div class="neon-card card-purple">
                <div class="card-title">🎯 QUESTÕES RESOLVIDAS</div>
                <div class="card-value">{total_questoes}</div>
            </div>
            <div class="neon-card card-green">
                <div class="card-title">📅 DIAS DE ESTUDO</div>
                <div class="card-value">{total_dias_estudo}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Insights
        st.markdown("#### 🧠 Insights Rápidos")
        if tempo_total_min > 0:
            disciplina_fav = df_estudos.groupby('exercicio')['duracao_min'].sum().idxmax()
            st.info(f"💡 **Disciplina mais estudada:** Você dedicou a maior parte do seu tempo a **{disciplina_fav}**.")
        
        if total_questoes > 0 and total_dias_estudo > 0:
            media_questoes = total_questoes / total_dias_estudo
            st.success(f"📈 **Ritmo de Questões:** Em média, você resolve **{media_questoes:.0f} questões** por dia de estudo.")

        st.markdown("---")

        c_dash_e1, c_dash_e2 = st.columns(2)
        
        with c_dash_e1:
            with st.container(border=True):
                st.markdown("#### 📊 Questões Feitas por Dia")
                df_q_dia = df_estudos.groupby('data', as_index=False)['repeticoes'].sum()
                df_q_dia = df_q_dia.sort_values('data')
                df_q_dia['data_formatada'] = df_q_dia['data'].dt.strftime('%d/%m')
                
                fig_q = px.bar(df_q_dia, x='data_formatada', y='repeticoes', text_auto=True)
                fig_q.update_traces(marker_color='#B224EF')
                fig_q.update_layout(xaxis_title="", yaxis_title="Qtd Questões", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#EDEDED"), margin=dict(l=0, r=0, t=20, b=0))
                st.plotly_chart(fig_q, use_container_width=True)

        with c_dash_e2:
            with st.container(border=True):
                st.markdown("#### ⏳ Tempo por Disciplina (Horas)")
                df_disc = df_estudos.groupby('exercicio', as_index=False)['duracao_min'].sum()
                df_disc['horas'] = df_disc['duracao_min'] / 60
                
                fig_d = px.pie(df_disc, values='horas', names='exercicio', hole=0.4, color_discrete_sequence=px.colors.sequential.Teal)
                fig_d.update_layout(showlegend=True, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#EDEDED"), margin=dict(l=0, r=0, t=20, b=0))
                st.plotly_chart(fig_d, use_container_width=True)

        with st.container(border=True):
            st.markdown("#### 🗓️ Tempo de Estudo por Dia (Minutos)")
            df_t_dia = df_estudos.groupby('data', as_index=False)['duracao_min'].sum()
            df_t_dia = df_t_dia.sort_values('data')
            df_t_dia['data_formatada'] = df_t_dia['data'].dt.strftime('%d/%m')
            
            fig_t = px.line(df_t_dia, x='data_formatada', y='duracao_min', markers=True, text='duracao_min')
            fig_t.update_traces(line_color='#00F2FE', marker=dict(size=8, color='#4FACFE'), textposition="top center")
            fig_t.update_layout(xaxis_title="", yaxis_title="Minutos", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#EDEDED"), margin=dict(l=0, r=0, t=20, b=0), xaxis=dict(type='category', showgrid=False), yaxis=dict(showgrid=True, gridcolor="#262626"))
            st.plotly_chart(fig_t, use_container_width=True)

    else:
        st.warning("Nenhum dado de estudo encontrado para o período selecionado.")

# ==========================================
# ABA 7: GERENCIAR
# ==========================================
with tab_gerenciar:
    if not df_raw.empty:
        st.markdown("### ⚙️ Corrigir ou Apagar Registros")
        df_raw['data_formatada'] = pd.to_datetime(df_raw['data']).dt.strftime('%d/%m/%Y')
        
        def formatar_registro(row):
            if row['grupo_muscular'] == 'Nutrição':
                return "🍏 DIETA"
            elif row['grupo_muscular'] == 'Métricas':
                return f"⚖️ PESO ({row['peso_corporal']}kg)"
            elif row['grupo_muscular'] == 'Estudos':
                return f"📚 ESTUDO: {row['exercicio']} ({row['duracao_min']} min)"
            else:
                return f"🏋️ {row['exercicio']} ({row['carga_kg']}kg)"

        opcoes_registros = df_raw.apply(
            lambda row: f"ID: {row['id']} | {row['data_formatada']} - {formatar_registro(row)}", 
            axis=1
        ).tolist()
        
        registro_selecionado = st.selectbox("Selecione o Registro Alvo:", opcoes_registros)
        id_real = int(registro_selecionado.split("ID: ")[1].split(" |")[0])
        
        st.write("---")
        col_edit, col_del = st.columns(2)
        
        with col_edit:
            with st.container(border=True):
                st.markdown("#### ✏️ Renomear Exercício/Disciplina")
                
                # Identifica se é estudo ou treino físico para mostrar a lista correta
                registro_df = df_raw[df_raw['id'] == id_real].iloc[0]
                is_estudo = registro_df['grupo_muscular'] == 'Estudos'
                
                opcoes_renomear = DISCIPLINAS_ESTUDO if is_estudo else TODOS_EXERCICIOS
                
                novo_nome = st.selectbox("Mudar para qual?", opcoes_renomear)
                
                if st.button("Atualizar Registro", use_container_width=True):
                    if is_estudo:
                        novo_grupo = "Estudos"
                    else:
                        novo_grupo = next((g for g, l in EXERCICIOS_PRESETADOS.items() if novo_nome in l), "Outro")
                        
                    supabase.table("treinos").update({"exercicio": novo_nome, "grupo_muscular": novo_grupo}).eq("id", id_real).execute()
                    st.success(f"Registro atualizado para {novo_nome}!")
                    st.rerun()

        with col_del:
            with st.container(border=True):
                st.markdown("#### 🗑️ Deletar Registro")
                st.warning("Atenção: Esta ação apagará permanentemente o registro.")
                if st.button("Apagar Registro Definitivamente", type="primary", use_container_width=True):
                    supabase.table("treinos").delete().eq("id", id_real).execute()
                    st.success("Registro apagado com sucesso!")
                    st.rerun()
