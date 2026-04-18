import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import plotly.express as px

# --- DICIONÁRIOS PRESETADOS ---
EXERCICIOS_PRESETADOS = {
    "Abdominal": ["Abdominal Levantada", "Prancha"],
    "Bíceps": ["Barra Fixa (Supinada)"],
    "Cardio": ["Bike", "Caminhada", "Corrida", "Pular Corda", "Pular Normal", "Subida Escada (Andares)"],
    "Costas": ["Barra Fixa (Pronada)"],
    "Peitoral": ["Flexão"],
    "Pernas": ["Agachamento"]
}

TODOS_EXERCICIOS = [ex for lista in EXERCICIOS_PRESETADOS.values() for ex in lista]
TODOS_EXERCICIOS.sort()

ALIMENTOS_SAUDAVEIS = ["Banana", "Uva", "Maçã", "Laranja", "Melão", "Melancia", "Mirtilo"]
ALIMENTOS_SAUDAVEIS.sort()

ALIMENTOS_BESTEIROL = ["Refrigerante", "Hambúrguer", "Pizza", "Lasanha", "Churros", "Pastel", "Coxinha", "Sorvete", "Batata Frita", "Sonho de Valsa", "Biscoito Recheado", "Chocotone"]
ALIMENTOS_BESTEIROL.sort()

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Monitoramento Físico", page_icon="⚡", layout="wide")

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
filtro_ex = st.sidebar.selectbox("Detalhar Exercício:", ["Todos"] + TODOS_EXERCICIOS)

if not df_raw.empty:
    df_treinos = df_raw[df_raw['grupo_muscular'] != 'Nutrição'].copy()
    df_dieta = df_raw[df_raw['grupo_muscular'] == 'Nutrição'].copy()
else:
    df_treinos = pd.DataFrame()
    df_dieta = pd.DataFrame()

if filtro_ex != "Todos" and not df_treinos.empty:
    df_treinos = df_treinos[df_treinos['exercicio'] == filtro_ex].copy()

# --- INTERFACE ---
st.markdown("<h1 style='text-align: center; font-weight: 800; letter-spacing: -1px;'>⚡ Monitoramento Físico</h1>", unsafe_allow_html=True)
if filtro_ex != "Todos":
    st.markdown(f"<p style='text-align: center; color: #FF4B4B; margin-top: -15px;'>Filtrando por: {filtro_ex}</p>", unsafe_allow_html=True)
st.write("")

tab_registro, tab_dieta, tab_dashboard, tab_gerenciar = st.tabs(["📝 Novo Treino", "🥗 Alimentação", "📊 Dashboard", "⚙️ Gerenciar"])

# ==========================================
# ABA 1: REGISTRO DE TREINO 
# ==========================================
with tab_registro:
    with st.form("registro_treino", clear_on_submit=True):
        st.markdown("<h3 style='margin-bottom: 20px;'>🏋️ Registrar Treino Físico</h3>", unsafe_allow_html=True)
        
        # Adicionei o peso corporal na linha de cima, junto com data e horário
        c_top1, c_top2, c_top3 = st.columns(3)
        with c_top1:
            data_treino = st.date_input("Data do Treino", value=datetime.today())
        with c_top2:
            horario = st.time_input("Horário", step=60)
        with c_top3:
            peso_corporal = st.number_input("Seu Peso Hoje (kg)", min_value=0.0, step=0.1, help="Preencha apenas 1x no dia. Deixe 0.0 nos demais exercícios.")

        st.markdown("---")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            exercicio_input = st.selectbox("Exercício", TODOS_EXERCICIOS)
            duracao = st.number_input("Duração Cardio (min)", min_value=0)
        with c2:
            series = st.number_input("Séries", min_value=1, value=1, step=1)
            reps = st.number_input("Repetições", min_value=0, step=1)
        with c3:
            carga = st.number_input("Carga (kg)", min_value=0.0)
            descanso = st.number_input("Descanso (seg)", min_value=0, step=15)
            distancia = st.number_input("Distância Cardio (km)", min_value=0.0)
        
        if st.form_submit_button("🚀 Salvar Treino", use_container_width=True):
            grupo = next((g for g, l in EXERCICIOS_PRESETADOS.items() if exercicio_input in l), "Outro")
            dados = {
                "data": str(data_treino), "horario": str(horario), "grupo_muscular": grupo,
                "exercicio": exercicio_input, "series": int(series), "repeticoes": int(reps),
                "carga_kg": float(carga), "descanso_seg": int(descanso), "duracao_min": int(duracao),
                "distancia_km": float(distancia), "alimentacao_saudavel": "", "alimentacao_besteirol": "",
                "peso_corporal": float(peso_corporal) # Enviando o peso para o banco!
            }
            supabase.table("treinos").insert(dados).execute()
            st.success("Treino salvo com sucesso!")
            st.rerun()

# ==========================================
# ABA 2: REGISTRO DE ALIMENTAÇÃO
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
                "peso_corporal": 0.0 # Dieta não registra peso corporal para não duplicar dados
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
# ABA 3: DASHBOARD
# ==========================================
with tab_dashboard:
    if not df_treinos.empty:
        df_treinos['data'] = pd.to_datetime(df_treinos['data'])
        df_treinos['reps_totais'] = df_treinos.apply(lambda row: row['repeticoes'] if row['series'] == 0 else row['series'] * row['repeticoes'], axis=1)
        
        total_dias = len(df_treinos['data'].unique())
        total_reps = int(df_treinos['reps_totais'].sum())
        carga_max = df_treinos['carga_kg'].max()
        media_reps = df_treinos['repeticoes'].mean()
        
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

        # --- NOVA SEÇÃO: EVOLUÇÃO DE PESO CORPORAL ---
        # Filtra apenas os dias onde você preencheu o peso (maior que zero)
        if 'peso_corporal' in df_treinos.columns:
            df_peso = df_treinos[df_treinos['peso_corporal'] > 0].groupby('data', as_index=False)['peso_corporal'].mean()
            
            if not df_peso.empty:
                with st.container(border=True):
                    st.markdown("#### ⚖️ Evolução do Peso Corporal (kg)")
                    fig_peso = px.line(df_peso, x='data', y='peso_corporal', markers=True, text='peso_corporal')
                    fig_peso.update_traces(
                        line_color='#B224EF', marker=dict(size=10, color='#7579FF'),
                        textposition="top center", texttemplate='%{text:.1f}'
                    )
                    fig_peso.update_layout(
                        xaxis_title="", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#EDEDED"), margin=dict(l=0, r=0, t=20, b=20),
                        xaxis=dict(type='category', showgrid=False), yaxis=dict(showgrid=True, gridcolor="#262626")
                    )
                    st.plotly_chart(fig_peso, use_container_width=True)

        # --- GRÁFICOS INFERIORES ---
        col_esq, col_dir = st.columns(2)
        
        with col_esq:
            with st.container(border=True):
                st.markdown(f"#### 📊 Repetições por Dia")
                df_reps_dia = df_treinos.groupby('data', as_index=False)['reps_totais'].sum()
                fig_reps = px.bar(df_reps_dia, x='data', y='reps_totais', text_auto=True)
                fig_reps.update_traces(marker_color='#FF416C')
                fig_reps.update_layout(
                    xaxis_title="", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#EDEDED"), margin=dict(l=0, r=0, t=30, b=0),
                    xaxis=dict(type='category', showgrid=False), yaxis=dict(showgrid=True, gridcolor="#262626")
                )
                st.plotly_chart(fig_reps, use_container_width=True)

        with col_dir:
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
                
                fig_turno = px.pie(df_turno, values='quantidade', names='turno', hole=0.5,
                                   color_discrete_sequence=['#F9D423', '#FF4E50', '#00F2FE'])
                
                fig_turno.update_traces(textposition='inside', textinfo='percent+label', 
                                        marker=dict(line=dict(color='#111111', width=2)))
                fig_turno.update_layout(
                    showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#EDEDED"), margin=dict(l=0, r=0, t=20, b=0)
                )
                st.plotly_chart(fig_turno, use_container_width=True)

        st.markdown("### 🗄️ Detalhes dos Treinos")
        # Ocultamos a coluna alimentação daqui para ficar limpo
        colunas_remover = ['id', 'created_at', 'alimentacao_saudavel', 'alimentacao_besteirol', 'turno']
        df_display = df_treinos.drop(columns=[c for c in colunas_remover if c in df_treinos.columns], errors='ignore')
        df_display['data'] = df_display['data'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_display.sort_values(by='data', ascending=False), use_container_width=True, hide_index=True)
    else:
        st.warning("Nenhum dado de treino encontrado.")

# ==========================================
# ABA 4: GERENCIAR
# ==========================================
with tab_gerenciar:
    if not df_raw.empty:
        st.markdown("### ⚙️ Corrigir ou Apagar Registros")
        df_raw['data_formatada'] = pd.to_datetime(df_raw['data']).dt.strftime('%d/%m/%Y')
        
        opcoes_registros = df_raw.apply(
            lambda row: f"ID: {row['id']} | {row['data_formatada']} - {'🍏 DIETA' if row['grupo_muscular'] == 'Nutrição' else f'🏋️ {row['exercicio']} ({row['carga_kg']}kg)'}", 
            axis=1
        ).tolist()
        
        registro_selecionado = st.selectbox("Selecione o Registro Alvo:", opcoes_registros)
        id_real = int(registro_selecionado.split("ID: ")[1].split(" |")[0])
        
        st.write("---")
        col_edit, col_del = st.columns(2)
        
        with col_edit:
            with st.container(border=True):
                st.markdown("#### ✏️ Renomear Exercício")
                novo_nome = st.selectbox("Mudar para qual exercício?", TODOS_EXERCICIOS)
                
                if st.button("Atualizar Exercício", use_container_width=True):
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
