import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import pandas as pd

st.set_page_config(page_title="Painel de Coletas - Jarbas", page_icon="🚛", layout="wide")

css_seguro = """
<style>
@keyframes fadeSlideUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.main .block-container { animation: fadeSlideUp 0.5s cubic-bezier(0.25, 1, 0.5, 1); }
</style>
"""
st.markdown(css_seguro, unsafe_allow_html=True)

def conectar_planilha():
    escopo = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    cred_dict = json.loads(st.secrets["google_credentials"])
    credenciais = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, escopo)
    cliente = gspread.authorize(credenciais)
    return cliente.open_by_url("https://docs.google.com/spreadsheets/d/1yHThW-nbcwxCcNTnb66PP1YHbHpCE9_ep3DC33-OZs4/edit?usp=sharing")

def obter_dados_jarbas():
    planilha = conectar_planilha()
    aba = planilha.worksheet("JARBAS")
    dados = []
    for l in aba.get_all_values()[1:]:
        if len(l) >= 2 and str(l[1]).strip() != "" and l[3].strip() == "":
            dados.append({
                "Nota (Nº)": str(l[1]).strip(),
                "QTD Volumes": l[0].strip(),
                "Prioridade": l[6].strip() if len(l)>6 else "Normal",
                "Data Solicitação": l[2].strip(),
                "Data Emissão": l[4].strip() if len(l)>4 else "-",
                "Cidade Destino": l[8].strip() if len(l)>8 else "Não informada" 
            })
    return dados

col1, col2 = st.columns([4, 1])
with col1:
    st.title("🚛 Painel de Coletas: JARBAS")
    st.markdown("Lista de cargas liberadas aguardando retirada na filial Speedmax.")
with col2:
    st.write("")
    if st.button("🔄 Atualizar Painel", use_container_width=True):
        st.rerun()

st.markdown("---")

with st.spinner("Conectando ao servidor da filial..."):
    try:
        pendentes = obter_dados_jarbas()
        
        if pendentes:
            st.warning(f"Temos **{len(pendentes)}** nota(s) aguardando coleta neste momento.")
            df = pd.DataFrame(pendentes)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.success("🎉 Nenhuma carga pendente no momento. Expedição limpa!")
            
    except Exception as e:
        st.error(f"Erro ao conectar com o banco de dados: {e}")
