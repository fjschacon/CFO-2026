import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
import json
import pypdf
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="CFO Elite System", 
    layout="wide", 
    page_icon="👮‍♂️",
    initial_sidebar_state="expanded"
)

# --- 2. API & SEGURANÇA ---
MY_API_KEY = "AIzaSyAetO0Ax1LjcR4Q9_-q50jO6w-5Na49WoU"
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

try:
    genai.configure(api_key=MY_API_KEY)
except:
    pass # Silencia erro inicial para não assustar

# --- 3. DESIGN SYSTEM (CSS AVANÇADO) ---
st.markdown("""
<style>
    /* Fundo Geral */
    .stApp {background-color: #f8f9fa;}
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #00274c;
        color: white;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    
    /* Cards de Tarefas */
    .task-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border-left: 8px solid #00274c; /* Azul PM */
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .task-card:hover {
        transform: scale(1.01);
    }
    
    /* Área de Quiz */
    .quiz-container {
        background: linear-gradient(135deg, #ffffff 0%, #e3f2fd 100%);
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #bbdefb;
        margin-top: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    
    /* Área de Reforço (Alerta) */
    .reforco-container {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #ffcc80;
        margin-top: 20px;
        color: #e65100;
    }
    
    /* Botões */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: 600;
        height: 50px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Métricas */
    div[data-testid="metric-container"] {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    
    /* Títulos */
    h1, h2, h3 {
        font-family: 'Helvetica Neue', sans-serif;
        color: #00274c;
        font-weight: 800;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. FUNÇÕES DE INTELIGÊNCIA ---

def extract_text_from_pdf(files):
    text = ""
    if files:
        for file in files:
            try:
                reader = pypdf.PdfReader(file)
                for page in reader.pages: text += page.extract_text() or ""
            except: pass
    return text

def gerar_ia_blindada(prompt):
    """Tenta conectar usando múltiplos modelos para furar bloqueio"""
    modelos = ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.0-pro']
    for m in modelos:
        try:
            model = genai.GenerativeModel(m)
            resp = model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
            if resp.text: return resp.text
        except: continue
    return None

def limpar_json(texto):
    if not texto: return None
    try:
        clean = texto.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except: return None

def gerar_simulado(materia, topico, qtd=6, ctx=""):
    prompt = f"""
    Aja como banca VUNESP (Barro Branco).
    Crie JSON com {qtd} questões múltipla escolha: {materia} ({topico}).
    Nível: Difícil. Contexto: {ctx[:5000]}
    JSON: [{{ "pergunta": "...", "opcoes": ["A)...", "B)..."], "correta": 0, "comentario": "..." }}]
    """
    res = gerar_ia_blindada(prompt)
    return limpar_json(res) or []

def gerar_reforco(erros):
    txt = " ".join(erros)
    prompt = f"Gere 2 questões REFORÇO (JSON) sobre erros: {txt}. Formato VUNESP."
    res = gerar_ia_blindada(prompt)
    return limpar_json(res) or []

def get_cronograma():
    return {
        0: [{"id": "s1", "h": "12h-14h", "m": "História", "t": "Era Vargas"}, {"id": "s2", "h": "12h-14h", "m": "Matemática", "t": "Básica"}],
        1: [{"id": "t1", "h": "06h-08h", "m": "Matemática", "t": "Exercícios"}, {"id": "t2", "h": "12h-14h", "m": "Geografia", "t": "Brasil"}, {"id": "t3", "h": "18h-20h", "m": "TREINO TAF", "t": "Corrida"}],
        2: [{"id": "q1", "h": "06h-08h", "m": "Português", "t": "Gramática"}, {"id": "q2", "h": "12h-14h", "m": "Química", "t": "Geral"}, {"id": "q3", "h": "18h-20h", "m": "TREINO TAF", "t": "Barra"}],
        3: [{"id": "qi1", "h": "06h-08h", "m": "Matemática", "t": "Revisão"}, {"id": "qi2", "h": "12h-14h", "m": "Biologia", "t": "Citologia"}, {"id": "qi3", "h": "18h-20h", "m": "TREINO TAF", "t": "Simulado"}],
        4: [{"id": "sx1", "h": "16h-18h", "m": "Redação", "t": "Prática"}],
        5: [{"id": "sb1", "h": "Livre", "m": "Simulado", "t": "Geral"}],
        6: [{"id": "dm1", "h": "Descanso", "m": "Revisão", "t": "Geral"}]
    }

# --- 5. ESTADO ---
if 'db_quiz' not in st.session_state: st.session_state.db_quiz = pd.DataFrame(columns=["Data", "Matéria", "Acertos", "Total"])
if 'db_taf' not in st.session_state: st.session_state.db_taf = pd.DataFrame(columns=["Data", "Exercício", "Marca"])
if 'ctx_provas' not in st.session_state: st.session_state.ctx_provas = ""
if 'data_prova' not in st.session_state: st.session_state.data_prova = None

# --- 6. SIDEBAR (PERFIL) ---
with st.sidebar:
    st.markdown("### 🛡️ Central do Aluno")
    st.info("**Flavio Chacon** | CFO 2026")
    
    # Status Conexão
    if st.button("🔄 Testar Rede"):
        res = gerar_ia_blindada("Oi")
        if res: st.success("Rede OK!")
        else: st.error("Rede Bloqueada! Use 4G.")
    
    st.divider()
    
    # Resumo Rápido
    if not st.session_state.db_quiz.empty:
        acc = st.session_state.db_quiz['Acertos'].sum()
        tot = st.session_state.db_quiz['Total'].sum()
        st.metric("Precisão Global", f"{(acc/tot)*100:.0f}%")
    
    if st.session_state.data_prova:
        dias = (st.session_state.data_prova - date.today()).days
        st.metric("⏳ Dias p/ Prova", dias)
    else:
        st.warning("Sem data definida")

# --- 7. ÁREA PRINCIPAL (HEADER) ---
st.title("Painel de Comando")

# Métricas Topo
col_a, col_b, col_c, col_d = st.columns(4)
questoes_hoje = len(st.session_state.db_quiz[st.session_state.db_quiz['Data'] == date.today()])
col_a.metric("Questões Hoje", questoes_hoje)
col_b.metric("Redações", "0") # Placeholder para futuro
col_c.metric("Treinos TAF", len(st.session_state.db_taf))
col_d.metric("Foco", "Alta Performance")

st.markdown("---")

# --- 8. ABAS REORGANIZADAS ---
abas = st.tabs(["📅 Cronograma Tático", "📚 Banco de Questões", "📝 Redação Pro", "💪 TAF Monitor", "📊 Dashboard", "⚙️ Config/Edital"])

# === ABA 1: CRONOGRAMA ===
with abas[0]:
    hj = datetime.now().weekday()
    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    
    # Barra de Progresso do Dia
    tarefas = get_cronograma().get(hj, [])
    feitas = 0 # Lógica futura de persistência
    if tarefas:
        prog = 0.0 # Placeholder
        st.progress(prog, text=f"Progresso Diário: {int(prog*100)}%")
    
    st.subheader(f"Missão de {dias[hj]}")
    
    if not tarefas: st.info("🎉 Dia de Descanso ou Simulado Livre!")
    
    for t in tarefas:
        # Card TAF
        if "TREINO" in t['m']:
            st.warning(f"🏋️‍♂️ **{t['h']} - {t['m']}**: {t['t']}")
            continue
            
        # Card Estudos
        with st.container():
            st.markdown(f"""
            <div class="task-card">
                <h3 style='margin:0'>{t['m']}</h3>
                <p style='color:#666; margin:0'>⏰ {t['h']} | 🎯 Foco: <b>{t['t']}</b></p>
            </div>
            """, unsafe_allow_html=True)
            
            k_st = f"s_{t['id']}"
            k_qz = f"q_{t['id']}"
            k_rf = f"r_{t['id']}"
            
            if k_st not in st.session_state: st.session_state[k_st] = "init"
            
            # Botão de Ação
            if st.session_state[k_st] == "init":
                col_btn, _ = st.columns([1,2])
                if col_btn.button(f"▶️ Iniciar Aula", key=f"btn_{t['id']}"):
                    with st.spinner("Conectando ao QG da VUNESP..."):
                        q = gerar_simulado(t['m'], t['t'], 6, st.session_state.ctx_provas)
                        if q:
                            st.session_state[k_qz] = q
                            st.session_state[k_st] = "quiz"
                            st.rerun()
                        else:
                            st.error("Falha de conexão. Tente novamente.")

            # Quiz
            if st.session_state[k_st] == "quiz":
                st.markdown(f"<div class='quiz-container'><h4>📝 Simulado: {t['t']}</h4>", unsafe_allow_html=True)
                qs = st.session_state[k_qz]
                resps = {}
                with st.form(key=f"frm_{t['id']}"):
                    for i, q in enumerate(qs):
                        st.markdown(f"**{i+1}) {q['pergunta']}**")
                        resps[i] = st.radio("Sua resposta:", q['opcoes'], key=f"op_{t['id']}_{i}", label_visibility="collapsed")
                        st.divider()
                    
                    if st.form_submit_button("✅ Finalizar e Corrigir"):
                        acertos, erros_list = 0, []
                        st.markdown("### 📊 Relatório de Desempenho")
                        for i, q in enumerate(qs):
                            try:
                                # Lógica simples para achar a correta baseada no indice
                                if q['opcoes'].index(resps[i]) == q['correta']:
                                    st.success(f"Questão {i+1}: Correta! 👏")
                                    acertos += 1
                                else:
                                    st.error(f"Questão {i+1}: Errou.")
                                    st.info(f"💡 Explicação: {q['comentario']}")
                                    erros_list.append(q['comentario'])
                            except: pass
                        
                        # Salva dados
                        new_row = pd.DataFrame([{"Data": date.today(), "Matéria": t['m'], "Acertos": acertos, "Total": 6}])
                        st.session_state.db_quiz = pd.concat([st.session_state.db_quiz, new_row], ignore_index=True)
                        
                        if acertos < 4:
                            st.warning(f"Nota: {acertos}/6. Atenção! Gerando Reforço...")
                            ref = gerar_reforco(erros_list)
                            if ref:
                                st.session_state[k_rf] = ref
                                st.session_state[k_st] = "ref"
                                st.rerun()
                        else:
                            st.balloons()
                            st.success(f"Nota: {acertos}/6. Missão Cumprida! 🏆")
                            if st.button("Fechar Aula"):
                                st.session_state[k_st] = "init"
                                st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            # Reforço
            if st.session_state[k_st] == "ref":
                st.markdown(f"<div class='reforco-container'><h4>🔥 Reforço Obrigatório</h4>", unsafe_allow_html=True)
                refs = st.session_state[k_rf]
                for i, r in enumerate(refs):
                    with st.expander(f"Questão Extra {i+1}", expanded=True):
                        st.write(r['pergunta'])
                        rr = st.radio("Opção:", r['opcoes'], key=f"rex_{t['id']}_{i}")
                        if st.button("Verificar", key=f"bex_{t['id']}_{i}"):
                            try:
                                if r['opcoes'].index(rr) == r['correta']: st.success("Boa!")
                                else: st.error("Errou.")
                            except: pass
                            st.write(f"**Gabarito:** {r['comentario']}")
                
                if st.button("Encerrar Sessão", key=f"end_{t['id']}"):
                    st.session_state[k_st] = "init"
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

# === ABA 2: BANCO DE QUESTÕES ===
with abas[1]:
    st.header("Gerador Avulso")
    c1, c2, c3 = st.columns([2, 2, 1])
    m = c1.selectbox("Matéria", ["Matemática", "Português", "História", "Geografia", "Física", "Química", "Biologia", "Inglês", "Adm. Pública", "Sociologia", "Filosofia"])
    tp = c2.text_input("Tópico (Ex: Crase, Leis)", placeholder="Deixe vazio para Geral")
    
    if c3.button("Gerar 1 Questão"):
        with st.spinner("Gerando..."):
            res = gerar_simulado(m, tp, 1, st.session_state.ctx_provas)
            if res: st.session_state.qlivre = res[0]
            else: st.error("Erro na rede.")
    
    if 'qlivre' in st.session_state:
        st.markdown("---")
        q = st.session_state.qlivre
        st.subheader(q['pergunta'])
        ro = st.radio("Escolha:", q['opcoes'])
        
        c_check, c_next = st.columns(2)
        if c_check.button("Conferir Resposta"):
            try:
                if q['opcoes'].index(ro) == q['correta']: 
                    st.success("ACERTOU! 🎯")
                    st.balloons()
                else: 
                    st.error("ERROU. ❌")
                st.info(f"**Comentário:** {q['comentario']}")
            except: st.warning("Selecione uma opção.")

# === ABA 3: REDAÇÃO ===
with abas[2]:
    st.header("Laboratório de Redação VUNESP")
    col_tema, col_texto = st.columns([1, 2])
    
    with col_tema:
        tema = st.text_input("Tema da Redação", value="A tecnologia na segurança pública")
        st.info("💡 **Dica:** Foque na estrutura Dissertativa-Argumentativa.")
        
    with col_texto:
        texto = st.text_area("Digite seu texto aqui...", height=400)
        if st.button("Corrigir Agora"):
            if not texto:
                st.warning("Escreva algo primeiro.")
            else:
                with st.spinner("A IA está lendo seu texto..."):
                    res = gerar_ia_blindada(f"Corrija esta redação como a VUNESP (Nota 0-20). Seja rigoroso na gramática e coerência. Tema: {tema}. Texto: {texto}")
                    if res: st.markdown(res)
                    else: st.error("Erro de conexão.")

# === ABA 4: TAF ===
with abas[3]:
    st.header("Monitoramento Físico")
    c1, c2 = st.columns(2)
    with c1:
        with st.form("form_taf"):
            ex = st.selectbox("Exercício", ["Barra Fixa", "Abdominal Remador", "Corrida 50m", "Corrida 12min"])
            val = st.number_input("Marca Alcançada", step=1.0)
            data_taf = st.date_input("Data do Treino", date.today())
            if st.form_submit_button("Salvar Treino"):
                n = pd.DataFrame([{"Data": data_taf, "Exercício": ex, "Marca": val}])
                st.session_state.db_taf = pd.concat([st.session_state.db_taf, n], ignore_index=True)
                st.success("Registrado!")
    
    with c2:
        if not st.session_state.db_taf.empty:
            df_taf = st.session_state.db_taf
            fig = px.line(df_taf, x="Data", y="Marca", color="Exercício", title="Sua Evolução Física", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum dado de treino ainda.")

# === ABA 5: DASHBOARD ===
with abas[4]:
    st.header("Análise de Inteligência")
    df = st.session_state.db_quiz
    
    if not df.empty:
        c1, c2 = st.columns(2)
        
        # Gráfico de Barras
        df_group = df.groupby("Matéria")[["Acertos", "Total"]].sum().reset_index()
        fig_bar = px.bar(df_group, x="Matéria", y="Acertos", title="Acertos por Matéria", color="Matéria")
        c1.plotly_chart(fig_bar, use_container_width=True)
        
        # Gráfico de Pizza (Aproveitamento)
        total_acertos = df['Acertos'].sum()
        total_erros = df['Total'].sum() - total_acertos
        fig_pie = go.Figure(data=[go.Pie(labels=['Acertos', 'Erros'], values=[total_acertos, total_erros], hole=.3)])
        fig_pie.update_layout(title_text="Precisão Geral")
        c2.plotly_chart(fig_pie, use_container_width=True)
        
        # Histórico em Tabela
        st.subheader("Histórico Recente")
        st.dataframe(df.sort_values(by="Data", ascending=False), use_container_width=True)
    else:
        st.warning("Sem dados suficientes. Vá estudar na aba Cronograma!")

# === ABA 6: CONFIG/EDITAL ===
with abas[5]:
    st.header("Gestão de Documentos")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Edital")
        u1 = st.file_uploader("Carregar Edital (PDF)", type="pdf")
        if u1 and st.button("Extrair Data da Prova"):
            txt = extract_text_from_pdf([u1])
            res = gerar_ia_blindada(f"Extraia a data da prova deste texto e retorne APENAS um JSON {{'data': 'YYYY-MM-DD'}}: {txt[:5000]}")
            d = limpar_json(res)
            if d:
                st.session_state.data_prova = datetime.strptime(d['data'], "%Y-%m-%d").date()
                st.success("Data Atualizada com Sucesso!")
                st.rerun()
            else:
                st.error("Falha ao ler data.")
                
    with c2:
        st.subheader("Cérebro da IA")
        u2 = st.file_uploader("Provas Antigas (Treinamento)", type="pdf", accept_multiple_files=True)
        if u2 and st.button("Processar Provas"):
            with st.spinner("Lendo arquivos..."):
                st.session_state.ctx_provas = extract_text_from_pdf(u2)
                st.success(f"IA Treinada com {len(st.session_state.ctx_provas)} caracteres de contexto real!")