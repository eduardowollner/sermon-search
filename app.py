import streamlit as st
from supabase import create_client

# ── Configuração da página ────────────────────────────────────
st.set_page_config(
    page_title="Busca de Sermões",
    page_icon="✝️",
    layout="centered",
)

# ── Conexão com Supabase (lê dos secrets do Streamlit Cloud) ─
@st.cache_resource
def conectar():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = conectar()

# ── Função de busca ───────────────────────────────────────────
def buscar(termo, limite=20):
    resp = supabase.rpc("buscar_segmentos", {
        "termo": termo,
        "lim": limite,
    }).execute()
    return resp.data or []

def formatar_tempo(segundos):
    segundos = int(segundos)
    h = segundos // 3600
    m = (segundos % 3600) // 60
    s = segundos % 60
    return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

def link_youtube(url, inicio_seg):
    return f"{url}&t={int(inicio_seg)}"

# ── Interface ─────────────────────────────────────────────────
st.title("✝️ Busca de Sermões")
st.caption("Pesquise por temas, palavras ou trechos em todos os vídeos transcritos.")

termo = st.text_input(
    "O que você quer encontrar?",
    placeholder="ex: graça, fé e perseverança, perdão...",
)

col1, col2 = st.columns([2, 1])
with col1:
    buscar_btn = st.button("Buscar", type="primary", use_container_width=True)
with col2:
    limite = st.selectbox("Resultados", [10, 20, 50], index=0, label_visibility="collapsed")

# ── Resultados ────────────────────────────────────────────────
if buscar_btn and termo.strip():
    with st.spinner("Buscando..."):
        resultados = buscar(termo.strip(), limite)

    if not resultados:
        st.warning("Nenhum resultado encontrado. Tente outro termo.")
    else:
        st.success(f"{len(resultados)} trecho(s) encontrado(s) para **{termo}**")
        st.divider()

        for r in resultados:
            tempo = formatar_tempo(r["inicio_seg"])
            url_t = link_youtube(r["url"], r["inicio_seg"])

            with st.container():
                st.markdown(f"#### 📺 {r['titulo']}")
                col_a, col_b = st.columns([1, 3])
                with col_a:
                    st.markdown(f"⏱️ `{tempo}`")
                with col_b:
                    st.link_button("Abrir no YouTube ↗", url_t)
                st.markdown(f"> {r['texto']}")
                st.divider()

elif buscar_btn and not termo.strip():
    st.error("Digite um termo para buscar.")

# ── Rodapé ───────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center; color:gray; font-size:12px; margin-top:40px'>"
    "Busca em transcrições geradas com Whisper · Banco Supabase</div>",
    unsafe_allow_html=True,
)
