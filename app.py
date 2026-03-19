import streamlit as st
import google.generativeai as genai
from supabase import create_client

# ── Configuração ──────────────────────────────────────────────
st.set_page_config(
    page_title="Busca de Sermões",
    page_icon="✝️",
    layout="centered",
)

@st.cache_resource
def conectar():
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return supabase

supabase = conectar()

# ── Funções ───────────────────────────────────────────────────
def gerar_embedding_busca(texto):
    resultado = genai.embed_content(
        model="models/gemini-embedding-001",
        content=texto,
        task_type="retrieval_query",
        output_dimensionality=1536,
    )
    return resultado["embedding"]

def buscar(pergunta, limite=10):
    embedding = gerar_embedding_busca(pergunta)
    resp = supabase.rpc("buscar_chunks", {
        "query_embedding": embedding,
        "lim": limite,
    }).execute()
    return resp.data or []

def formatar_tempo(segundos):
    segundos = int(segundos)
    h = segundos // 3600
    m = (segundos % 3600) // 60
    s = segundos % 60
    return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

def resumir_relevancia(texto, pergunta):
    # Encontra a frase do chunk mais próxima do tema buscado
    import re
    frases = re.split(r'(?<=[.!?])\s+', texto)
    pergunta_lower = pergunta.lower()
    palavras_busca = set(pergunta_lower.split())

    melhor_frase = ""
    melhor_score = -1

    for frase in frases:
        score = sum(1 for p in palavras_busca if p in frase.lower())
        if score > melhor_score:
            melhor_score = score
            melhor_frase = frase

    # Destaca palavras da busca que aparecem no texto
    for palavra in palavras_busca:
        if len(palavra) > 3:
            padrao = re.compile(f"({re.escape(palavra)})", re.IGNORECASE)
            texto = padrao.sub(
                r"<mark style='background-color:#fff3b0;color:#000;"
                r"border-radius:3px;padding:0 2px'>\1</mark>",
                texto
            )

    return texto, melhor_frase
    return texto

# ── Interface ─────────────────────────────────────────────────
st.title("✝️ Busca de Sermões")
st.caption("Pesquise por temas ou perguntas — não precisa usar as palavras exatas.")

pergunta = st.text_input(
    "O que você quer encontrar?",
    placeholder="ex: como ter paz em momentos difíceis...",
)

col1, col2 = st.columns([2, 1])
with col1:
    buscar_btn = st.button("Buscar", type="primary", use_container_width=True)
with col2:
    limite = st.selectbox("Resultados", [10, 20, 50], index=0, label_visibility="collapsed")

# ── Resultados ────────────────────────────────────────────────
if buscar_btn and pergunta.strip():
    with st.spinner("Buscando por significado..."):
        resultados = buscar(pergunta.strip(), limite)

    if not resultados:
        st.warning("Nenhum resultado encontrado. Tente reformular a pergunta.")
    else:
        st.success(f"{len(resultados)} trecho(s) encontrado(s)")
        st.divider()

        for r in resultados:
            tempo = formatar_tempo(r["inicio_seg"])
            url_t = f"{r['url']}&t={int(r['inicio_seg'])}"
            similaridade = round(r["similaridade"] * 100, 1)

            with st.container():
                col_titulo, col_sim = st.columns([4, 1])
                with col_titulo:
                    st.markdown(f"#### 📺 {r['titulo']}")
                with col_sim:
                    st.metric("relevância", f"{similaridade}%")

                col_a, col_b = st.columns([1, 3])
                with col_a:
                    st.markdown(f"⏱️ `{tempo}`")
                with col_b:
                    st.link_button("Abrir no YouTube ↗", url_t)

                texto_destacado, frase_relevante = resumir_relevancia(r["texto"], pergunta)

                if frase_relevante:
                    st.markdown(
                        f"<div style='background:#1a3a1a;border-left:3px solid #4caf50;"
                        f"padding:6px 12px;margin:8px 0;font-size:13px;color:#90ee90;"
                        f"border-radius:0 6px 6px 0'>"
                        f"Trecho mais relevante: <em>{frase_relevante}</em></div>",
                        unsafe_allow_html=True,
                    )
                
                st.write(
                    f"<div style='border-left:3px solid #ccc;padding:8px 12px;"
                    f"margin:8px 0;font-size:15px'>{texto_destacado}</div>",
                    unsafe_allow_html=True,
                )
                st.divider()

elif buscar_btn and not pergunta.strip():
    st.error("Digite uma pergunta para buscar.")

# ── Rodapé ────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center;color:gray;font-size:12px;margin-top:40px'>"
    "Busca semântica com Google gemini-embedding-001 · Supabase pgvector</div>",
    unsafe_allow_html=True,
)
