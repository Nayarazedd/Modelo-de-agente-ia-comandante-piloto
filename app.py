import streamlit as st
import os
from dotenv import load_dotenv
from groq import Groq

# Carrega as variáveis do arquivo .env
load_dotenv()

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Cockpit - Comandante Virtual",
    page_icon="✈️",
    layout="centered"
)

api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    st.error("ERRO CRÍTICO: A variável de ambiente `GROQ_API_KEY` não foi encontrada. Verifique seu arquivo .env ou as configurações do Render.")
    st.stop()

client = Groq(api_key=api_key)

# System Prompt base do Comandante
SYSTEM_PROMPT_BASE = """
# CONTEXTO E MISSÃO
Você é um comandante e piloto de aviação comercial sênior com mais de 15 anos de experiência em voos internacionais. 
Sua missão é responder às dúvidas do usuário com precisão técnica, clareza didática e total coerência contextual.

# ESTILO E TOM
- Estilo: Profissional, focado, articulado e didático. Use termos técnicos autênticos da aviação explicados de maneira acessível.
- Tom: Calmo, confiante, acolhedor e focado na segurança da comunicação e do voo.
- Formato: Respostas diretas e organizadas em parágrafos curtos. Nunca invente fatos.
"""

# Função para gerar o resumo condensado exigido pela especificação (OUTCOME)
def gerar_resumo_estado(mensagens_antigas):
    try:
        texto_para_resumir = "\n".join([f"{m['role']}: {m['content']}" for m in mensagens_antigas])
        
        prompt_resumo = f"""
        Analise o histórico abaixo e gere uma atualização condensada da memória de longo prazo seguindo estritamente estas regras:
        1. Extraia apenas fatos, decisões tomadas, dados técnicos citados e intenções do usuário.
        2. Elimine saudações, conversas fiadas e redundâncias.
        3. Formato de saída: Um texto em tópicos curtos (máximo 3 a 4 linhas no total) representando o estado consolidado da conversa.

        Histórico:
        {texto_para_resumir}
        """
        
        resposta = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt_resumo}],
            temperature=0.3,
        )
        return resposta.choices[0].message.content
    except Exception:
        return "Nenhum estado anterior relevante registrado."

# Inicializa o estado da sessão no Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Painel ativado. Aqui é o Comandante. Estamos com todos os sistemas operacionais e prontos para o briefing. Qual é a nossa rota ou dúvida para o voo de hoje?"}
    ]

if "resumo_memoria" not in st.session_state:
    st.session_state.resumo_memoria = "Nenhum histórico anterior."

# Título da aplicação na interface
st.title("✈️ Cockpit - Comandante de Bordo")
st.markdown("### Sistema de Comunicação com Gestão de Memória Consolidada")

# Exibe o histórico de mensagens na tela
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada de texto do usuário
if prompt_usuario := st.chat_input("Digite sua dúvida ou comando para o Comandante..."):
    st.session_state.messages.append({"role": "user", "content": prompt_usuario})
    
    with st.chat_message("user"):
        st.markdown(prompt_usuario)

    try:
        # Se o histórico crescer, compacta as mensagens mais antigas no "resumo_memoria" (OUTCOME)
        if len(st.session_state.messages) > 6:
            # Pega as mensagens mais antigas para compactar
            antigas = st.session_state.messages[:-4]
            # Mantém as últimas 4 mensagens intactas para a janela de curto prazo
            st.session_state.messages = st.session_state.messages[-4:]
            # Atualiza o resumo consolidado
            st.session_state.resumo_memoria = gerar_resumo_estado(antigas)

        # Monta o System Prompt definitivo injetando o resumo condensado atualizado
        system_prompt_dinamico = SYSTEM_PROMPT_BASE + f"\n\n# ESTADO CONSOLIDADO DA CONVERSA (MEMÓRIA DE LONGO PRAZO):\n{st.session_state.resumo_memoria}"

        # Monta a lista final enviada à API
        mensagens_para_ia = [{"role": "system", "content": system_prompt_dinamico}] + st.session_state.messages
        
        with st.chat_message("assistant"):
            with st.spinner("Transmitindo dados pelo canal de bordo..."):
                resposta = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=mensagens_para_ia,
                    temperature=0.6,
                )
                texto_resposta = resposta.choices[0].message.content
                st.markdown(texto_resposta)
                
        st.session_state.messages.append({"role": "assistant", "content": texto_resposta})

    except Exception as e:
        error_msg = f"Falha na comunicação de bordo: {str(e)}"
        st.error(error_msg)