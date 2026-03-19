import streamlit as st
import google.generativeai as genai
from supabase import create_client

# ── Configuração ──────────────────────────────────────────────
st.set_page_config(
    page_title="Assistente de Sermões",
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

def buscar_chunks(pergunta, limite=8):
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

def gerar_resposta(pergunta, chunks):
    contexto = ""
    for i, c in enumerate(chunks):
        tempo = formatar_tempo(c["inicio_seg"])
        contexto += (
            f"\n---\n"
            f"[Fonte {i+1}] Vídeo: \"{c['titulo']}\" | Tempo: {tempo}\n"
            f"{c['texto']}\n"
        )

    prompt = f"""Você é um assistente cristão que ajuda pessoas a encontrar ensinamentos em sermões.

Com base APENAS nos trechos de sermões abaixo, responda a pergunta do usuário de forma clara e edificante.

Regras importantes:
- Use apenas o conteúdo dos trechos fornecidos, não invente nada
- Ao citar um ensinamento, indique entre parênteses a fonte, por exemplo: (Fonte 1)
- Se os trechos não forem suficientes para responder, diga isso claramente
- Responda em português, de forma acolhedora e com linguagem cristã
- Ao final, liste os vídeos que foram usados na resposta

Trechos dos sermões:
{contexto}

Pergunta: {pergunta}

Resposta:"""

    model = genai.GenerativeModel("gemini-1.5-flash")
    resposta = model.generate_content(prompt)
    return resposta.text

# ── Interface ─────────────────────────────────────────────────
st.title("✝️ Assistente de Sermões")
st.caption("Faça uma pergunta e receba uma resposta baseada nos sermões transcritos.")

pergunta = st.text_input(
    "Qual é a sua pergunta?",
    placeholder="ex: O que os pregadores ensinam sobre perdoar quem nos machucou?",
)

col1, col2 = st.columns([2, 1])
with col1:
    buscar_btn = st.button("Perguntar", type="primary", use_container_width=True)
with col2:
    n_chunks = st.selectbox(
        "Trechos analisados", [5, 8, 12], index=1, label_visibility="collapsed"
    )

# ── Resultado ─────────────────────────────────────────────────
if buscar_btn and pergunta.strip():
    with st.spinner("Buscando nos sermões e gerando resposta..."):
        chunks = buscar_chunks(pergunta.strip(), n_chunks)

        if not chunks:
            st.warning("Nenhum trecho relevante encontrado. Tente reformular a pergunta.")
        else:
            resposta = gerar_resposta(pergunta.strip(), chunks)

            # Resposta do LLM
            st.markdown("### Resposta")
            st.markdown(resposta)

            # Fontes
            st.divider()
            st.markdown("### Trechos consultados")
            for i, c in enumerate(chunks):
                tempo = formatar_tempo(c["inicio_seg"])
                url_t = f"{c['url']}&t={int(c['inicio_seg'])}"
                similaridade = round(c["similaridade"] * 100, 1)

                with st.expander(
                    f"Fonte {i+1} — {c['titulo']} · {tempo} · {similaridade}% relevância"
                ):
                    st.markdown(f"> {c['texto']}")
                    st.link_button("Abrir no YouTube ↗", url_t)

elif buscar_btn and not pergunta.strip():
    st.error("Digite uma pergunta.")

# ── Rodapé ────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center;color:gray;font-size:12px;margin-top:40px'>"
    "Respostas geradas com Gemini 1.5 Flash · Busca semântica com pgvector · Supabase"
    "</div>",
    unsafe_allow_html=True,
)
