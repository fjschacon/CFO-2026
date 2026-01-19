import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime, date
import plotly.express as px
import json
import pypdf
import time
import requests
import warnings
import re

# Ignora avisos de segurança SSL (Necessário para furar bloqueio corporativo)
warnings.filterwarnings("ignore")

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(
    page_title="CFO Elite System", 
    layout="wide", 
    page_icon="👮‍♂️",
    initial_sidebar_state="expanded"
)

# --- 2. SEGURANÇA DA CHAVE (VIA SECRETS) ---
try:
    # O código busca a chave no cofre do Streamlit. NÃO ESCREVA ELA AQUI.
    MY_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    # Caso você rode localmente sem secrets, avisa o erro
    st.error("🚨 ERRO DE SEGURANÇA: Chave API não configurada nos Secrets!")
    st.info("Vá em Settings > Secrets no Streamlit Cloud e cole sua chave lá.")
    st.stop()

# Configurações de Segurança da IA (Desbloqueado para temas policiais)
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Tenta configurar a biblioteca oficial (se a rede deixar)
try:
    genai.configure(api_key=MY_API_KEY)
except: pass

# --- 3. CSS VISUAL (ELITE) ---
st.markdown("""
<style>
    .stApp {background-color: #f4f6f9;}
    [data-testid="stSidebar"] {background-color: #0d1b2a; color: white;}
    
    .task-card {
        background-color: white; padding: 20px; border-radius: 12px;
        border-left: 6px solid #003366; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px; transition: 0.3s;
    }
    .task-card:hover { transform: translateY(-2px); }
    
    .quiz-container {
        background: #e3f2fd; padding: 20px; border-radius: 12px;
        border: 1px solid #90caf9; margin-top: 15px;
    }
    
    .result-box {
        background: #ffffff; padding: 20px; border-radius: 12px;
        border-left: 5px solid #28a745; margin-top: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .reforco-container {
        background: #fff3e0; padding: 20px; border-radius: 12px;
        border: 1px solid #ffcc80; margin-top: 15px;
    }
    
    .stButton>button {width: 100%; border-radius: 8px; font-weight: bold; height: 45px;}
    h1, h2, h3 {color: #00274c;}
</style>
""", unsafe_allow_html=True)

# --- 4. FUNÇÕES DE CONEXÃO BLINDADA ---

def conexao_http_forca_bruta(prompt):
    """
    PLANO B: Conecta via HTTP puro ignorando SSL.
    Usa o modelo 'gemini-1.5-flash' que é rápido e compatível.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={MY_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": SAFETY_SETTINGS
    }
    
    try:
        # verify=False é o segredo para furar firewall
        response = requests.post(url, headers=headers, json=data, timeout=25, verify=False)
        
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            # Se der 404 no Flash, tenta o Pro (Fallback)
            if response.status_code == 404:
                return conexao_http_fallback_pro(prompt)
            st.error(f"Erro Google ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        st.error(f"Erro de Rede: {e}")
        return None

def conexao_http_fallback_pro(prompt):
    """Fallback para Gemini Pro antigo"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={MY_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}], "safetySettings": SAFETY_SETTINGS}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=25, verify=False)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
    except: return None
    return None

def gerar_ia_blindada(prompt):
    """
    Tenta Lib Python (Bonito) -> Se falhar -> Tenta HTTP (Força Bruta)
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        resp = model.generate_content(prompt, safety_settings=SAFETY_SETTINGS)
        return resp.text
    except:
        return conexao_http_forca_bruta(prompt)

def limpar_json_inteligente(texto):
    if not texto: return None
    try:
        padrao = r'\[.*\]|\{.*\}'
        match = re.search(padrao, texto.replace('\n', ' '), re.DOTALL)
        if match: return json.loads(match.group())
        else:
            clean = texto.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
    except: return None

def gerar_simulado(materia, topico, qtd=6, ctx=""):
    prompt = f"""
    Aja como banca VUNESP (Barro Branco).
    Crie um JSON com {qtd} questões de múltipla escolha sobre {materia} ({topico}).
    Nível: Difícil. Contexto: {ctx[:3000]}
    
    IMPORTANTE: Retorne APENAS o JSON puro.
    [
        {{
            "pergunta": "...",
            "opcoes": ["A) ...", "B) ...", "C) ...", "D) ...", "E) ..."],
            "correta": 0,
            "comentario": "..."
        }}
    ]
    """
    res = gerar_ia_blindada(prompt)
    return limpar_json_inteligente(res) or []

def gerar_reforco(erros):
    txt = " ".join(erros)
    prompt = f"Gere 2 questões REFORÇO (JSON puro) sobre: {txt}."
    res = gerar_ia_blindada(prompt)
    return limpar_json_inteligente(res) or []

def extract_text_from_pdf(files):
    text = ""
    if files:
        for f in files:
            try:
                reader = pypdf.PdfReader(f)
                for p in reader.pages: text += p.extract_text()
            except: pass
    return text

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

# --- 6. SIDEBAR ---
with st.sidebar:
    st.title("👮‍♂️ Central CFO")
    st.write("**Flavio Chacon**")
    st.success("Sistema Seguro Ativo")
    
    # Botão de Teste Seguro
    if st.button("🛠️ Testar Conexão"):
        res = gerar_ia_blindada("Teste")
        if res: st.success("Conexão OK!")
        else: st.error("Falha. Verifique Secrets.")
    
    st.divider()
    if st.session_state.data_prova:
        d = (st.session_state.data_prova - date.today()).days
        st.metric("Dias p/ Prova", d)

# --- 7. HEADER ---
st.title("Painel de Comando")
c1, c2, c3, c4 = st.columns(4)
q_hj = len(st.session_state.db_quiz[st.session_state.db_quiz['Data'] == date.today()])
c1.metric("Questões Hoje", q_hj)
c2.metric("Redações", "0")
c3.metric("Treinos TAF", len(st.session_state.db_taf))
c4.metric("Modo", "Secure Secrets")
st.markdown("---")

# --- 8. ABAS ---
abas = st.tabs(["📅 Cronograma", "📚 Questões", "📝 Redação", "💪 TAF", "📊 Dashboard", "⚙️ Config"])

# ABA 1: CRONOGRAMA
with abas[0]:
    hj = datetime.now().weekday()
    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    st.subheader(f"Missão de {dias[hj]}")
    
    tarefas = get_cronograma().get(hj, [])
    if tarefas: st.progress(0, text="Progresso Diário")
    else: st.info("Dia Livre!")
    
    for t in tarefas:
        if "TREINO" in t['m']:
            st.warning(f"🏋️‍♂️ **{t['h']}**: {t['m']} ({t['t']})")
            continue
            
        with st.container():
            st.markdown(f"""<div class="task-card"><h3>📚 {t['m']}</h3><p>{t['h']} | {t['t']}</p></div>""", unsafe_allow_html=True)
            k_st = f"s_{t['id']}"; k_qz = f"q_{t['id']}"; k_rf = f"r_{t['id']}"; k_rs = f"res_{t['id']}"
            
            if k_st not in st.session_state: st.session_state[k_st] = "init"
            
            # FASE 1: INÍCIO
            if st.session_state[k_st] == "init":
                if st.button(f"▶️ Iniciar Aula", key=f"b_{t['id']}"):
                    with st.spinner("Gerando Simulado..."):
                        q = gerar_simulado(t['m'], t['t'], 6, st.session_state.ctx_provas)
                        if q:
                            st.session_state[k_qz] = q
                            st.session_state[k_st] = "quiz"
                            st.rerun()
                        else: st.error("Erro na conexão. Verifique Secrets.")

            # FASE 2: QUIZ
            if st.session_state[k_st] == "quiz":
                st.markdown(f"<div class='quiz-container'><h4>📝 Simulado</h4>", unsafe_allow_html=True)
                qs = st.session_state[k_qz]
                resps = {}
                with st.form(key=f"f_{t['id']}"):
                    for i, q in enumerate(qs):
                        st.markdown(f"**{i+1}) {q['pergunta']}**")
                        op = q.get('opcoes', ["Erro"])
                        resps[i] = st.radio("R:", op, key=f"r_{t['id']}_{i}", index=None)
                        st.divider()
                    enviou = st.form_submit_button("✅ Finalizar")
                
                if enviou:
                    if any(resps[i] is None for i in range(len(qs))):
                        st.error("Responda todas as questões!")
                    else:
                        acc = 0
                        erros = []
                        for i, q in enumerate(qs):
                            try:
                                if q['opcoes'].index(resps[i]) == q['correta']: acc += 1
                                else: erros.append(q['comentario'])
                            except: pass
                        
                        st.session_state[k_rs] = {"acertos": acc, "erros": erros}
                        st.session_state.db_quiz = pd.concat([st.session_state.db_quiz, pd.DataFrame([{"Data": date.today(), "Matéria": t['m'], "Acertos": acc, "Total": 6}])], ignore_index=True)
                        st.session_state[k_st] = "result"
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            # FASE 3: RESULTADO
            if st.session_state[k_st] == "result":
                res_data = st.session_state.get(k_rs, {})
                acertos = res_data.get("acertos", 0)
                erros = res_data.get("erros", [])
                
                st.markdown(f"<div class='result-box'><h3>📊 Resultado: {acertos}/6</h3>", unsafe_allow_html=True)
                
                if acertos >= 4:
                    st.balloons()
                    st.success("✅ Aprovado!")
                else:
                    st.warning("⚠️ Reforço Recomendado.")
                
                c1, c2 = st.columns(2)
                if acertos < 4:
                    if c1.button("Gerar Reforço", key=f"brf_{t['id']}"):
                        with st.spinner("Criando Reforço..."):
                            ref = gerar_reforco(erros)
                            if ref:
                                st.session_state[k_rf] = ref
                                st.session_state[k_st] = "ref"
                                st.rerun()
                
                if c2.button("Fechar Aula", key=f"bcl_{t['id']}"):
                    st.session_state[k_st] = "init"
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            # FASE 4: REFORÇO
            if st.session_state[k_st] == "ref":
                st.markdown(f"<div class='reforco-container'><h4>🔥 Reforço Obrigatório</h4>", unsafe_allow_html=True)
                refs = st.session_state[k_rf]
                for i, r in enumerate(refs):
                    with st.expander(f"Questão Extra {i+1}", expanded=True):
                        st.write(r['pergunta'])
                        rr = st.radio("Opção:", r['opcoes'], key=f"rx_{t['id']}_{i}", index=None)
                        if st.button("Verificar", key=f"bx_{t['id']}_{i}"):
                            if rr:
                                try:
                                    if r['opcoes'].index(rr) == r['correta']: st.success("Boa!")
                                    else: st.error("Errou.")
                                except: pass
                                st.write(f"**Gabarito:** {r['comentario']}")
                            else: st.warning("Escolha uma opção")
                
                if st.button("Encerrar Sessão", key=f"end_{t['id']}"):
                    st.session_state[k_st] = "init"
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

# ABA 2: LIVRE
with abas[1]:
    st.header("Modo Livre")
    c1, c2 = st.columns(2)
    m = c1.selectbox("Matéria", ["Matemática", "Português", "História", "Geografia", "Física", "Química", "Biologia", "Inglês"])
    tp = c2.text_input("Tópico")
    if st.button("Gerar"):
        res = gerar_simulado(m, tp, 1, st.session_state.ctx_provas)
        if res: st.session_state.qlivre = res[0]
    
    if 'qlivre' in st.session_state:
        q = st.session_state.qlivre
        st.write(q['pergunta'])
        ro = st.radio("Opção", q['opcoes'], index=None)
        if st.button("Verificar"):
            if ro:
                try:
                    if q['opcoes'].index(ro) == q['correta']: st.success("Certa!")
                    else: st.error("Errada.")
                    st.caption(q['comentario'])
                except: pass
            else: st.warning("Escolha uma opção.")

# ABA 3: REDAÇÃO
with abas[2]:
    st.header("Redação")
    tm = st.text_input("Tema")
    tx = st.text_area("Texto")
    if st.button("Corrigir"):
        st.write(gerar_ia_blindada(f"Corrija VUNESP 0-20: {tm} \n {tx}"))

# ABA 4: TAF
with abas[3]:
    st.header("TAF")
    e = st.selectbox("Exercício", ["Barra", "Abs", "Corrida"])
    v = st.number_input("Valor")
    if st.button("Salvar"):
        st.session_state.db_taf = pd.concat([st.session_state.db_taf, pd.DataFrame([{"Data": date.today(), "Exercício": e, "Marca": v}])], ignore_index=True)
        st.success("Ok!")
    if not st.session_state.db_taf.empty:
        st.plotly_chart(px.line(st.session_state.db_taf, x="Data", y="Marca", color="Exercício"))

# ABA 5: DASHBOARD
with abas[4]:
    if not st.session_state.db_quiz.empty:
        c1, c2 = st.columns(2)
        df_g = st.session_state.db_quiz.groupby("Matéria")[["Acertos", "Total"]].sum().reset_index()
        c1.plotly_chart(px.bar(df_g, x="Matéria", y="Acertos", title="Acertos por Matéria"))
        
        tot_ac = st.session_state.db_quiz['Acertos'].sum()
        tot_er = st.session_state.db_quiz['Total'].sum() - tot_ac
        c2.plotly_chart(go.Figure(data=[go.Pie(labels=['Acertos', 'Erros'], values=[tot_ac, tot_er])]))
    else: st.info("Sem dados.")

# ABA 6: CONFIG
with abas[5]:
    u1 = st.file_uploader("Edital", type="pdf")
    if u1 and st.button("Ler"):
        res = gerar_ia_blindada(f"Data prova JSON {{'data':'YYYY-MM-DD'}}: {extract_text_from_pdf([u1])[:3000]}")
        d = limpar_json(res)
        if d:
            st.session_state.data_prova = datetime.strptime(d['data'], "%Y-%m-%d").date()
            st.rerun()
    u2 = st.file_uploader("Provas", type="pdf", accept_multiple_files=True)
    if u2 and st.button("Treinar"):
        st.session_state.ctx_provas = extract_text_from_pdf(u2)
        st.success("IA Treinada!")