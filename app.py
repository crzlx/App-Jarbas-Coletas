import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime, timedelta, timezone
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

def parse_data(data_str):
    try: return datetime.strptime(data_str, "%d/%m/%Y").date()
    except: return None

def obter_dados_jarbas():
    planilha = conectar_planilha()
    aba = planilha.worksheet("JARBAS")
    pendentes = []
    historico = []
    
    fuso_br = timezone(timedelta(hours=-3))
    hoje_dt = datetime.now(fuso_br).date()
    
    for l in aba.get_all_values()[1:]:
        if len(l) >= 2 and str(l[1]).strip() != "":
            nota = str(l[1]).strip()
            qtd = l[0].strip()
            data_sol_str = l[2].strip()
            data_col_str = l[3].strip()
            data_emi = l[4].strip() if len(l)>4 else "-"
            prioridade = l[6].strip() if len(l)>6 else "Normal"
            cidade = l[8].strip() if len(l)>8 else "Não informada"
            hora_sol = l[9].strip() if len(l)>9 else "-"
            
            dt_sol = parse_data(data_sol_str)
            
            if data_col_str == "": 
                atraso_str = "🟢 Hoje"
                if dt_sol:
                    dias = (hoje_dt - dt_sol).days
                    if dias <= 0: atraso_str = "🟢 Hoje"
                    elif dias == 1: atraso_str = "🟡 1 dia de atraso"
                    else: atraso_str = f"🔴 {dias} dias de atraso"
                
                pendentes.append({
                    "Nota (Nº)": nota,
                    "QTD Volumes": qtd,
                    "Prioridade": prioridade,
                    "Data Solicitação": data_sol_str,
                    "Hora Registro": hora_sol,
                    "Cidade Destino": cidade,
                    "Situação": atraso_str
                })
            else: 
                dt_col = parse_data(data_col_str)
                tempo_coleta = "🟢 No mesmo dia"
                if dt_sol and dt_col:
                    dias = (dt_col - dt_sol).days
                    if dias <= 0: tempo_coleta = "🟢 No mesmo dia"
                    elif dias == 1: tempo_coleta = "🟡 1 dia de atraso"
                    else: tempo_coleta = f"🔴 {dias} dias de atraso"
                    
                historico.append({
                    "Nota (Nº)": nota,
                    "QTD Volumes": qtd,
                    "Data Solicitação": data_sol_str,
                    "Hora Registro": hora_sol,
                    "Data da Coleta": data_col_str,
                    "Tempo Demorado": tempo_coleta,
                    "Cidade Destino": cidade
                })
                
    return pendentes, historico

col1, col2 = st.columns([4, 1])
with col1:
    st.title("🚛 Painel de Coletas: JARBAS")
with col2:
    st.write("")
    if st.button("🔄 Atualizar Painel", use_container_width=True):
        st.rerun()

st.markdown("---")

@st.fragment(run_every=30)
def painel_monitoramento_jarbas():
    try:
        pendentes, historico = obter_dados_jarbas()
        
        aba_pendentes, aba_historico = st.tabs(["🚨 Coletas Pendentes", "✅ Histórico de Coletas"])
        
        with aba_pendentes:
            if pendentes:
                st.warning(f"Temos **{len(pendentes)}** nota(s) aguardando coleta neste momento.")
                df_p = pd.DataFrame(pendentes)
                st.dataframe(df_p, use_container_width=True, hide_index=True)
            else:
                st.success("🎉 Nenhuma carga pendente no momento. Expedição limpa!")
        
        with aba_historico:
            with st.expander("🔍 Filtro Complementar (Opcional)", expanded=False):
                cf1, cf2, cf3 = st.columns(3)
                with cf1:
                    f_nota = st.text_input("Filtrar por Nota (Nº)", autocomplete="off")
                with cf2:
                    f_cidade = st.text_input("Filtrar por Cidade", autocomplete="off")
                with cf3:
                    f_hora = st.text_input("Filtrar por Hora (Ex: 14:30)", autocomplete="off")
            
            if historico:
                historico.reverse()
                historico_filtrado = historico
                
                if f_nota:
                    historico_filtrado = [h for h in historico_filtrado if f_nota.lower() in h["Nota (Nº)"].lower()]
                if f_cidade:
                    historico_filtrado = [h for h in historico_filtrado if f_cidade.lower() in h["Cidade Destino"].lower()]
                if f_hora:
                    historico_filtrado = [h for h in historico_filtrado if f_hora in h["Hora Registro"]]

                if historico_filtrado:
                    st.info(f"**{len(historico_filtrado)}** coletas encontradas.")
                    df_h = pd.DataFrame(historico_filtrado)
                    st.dataframe(df_h, use_container_width=True, hide_index=True)
                else:
                    st.warning("⚠️ Nenhum histórico encontrado com esses filtros.")
            else:
                st.write("Nenhum histórico de coleta encontrado.")
            
    except Exception as e:
        st.error(f"Erro ao conectar com o banco de dados: {e}")

painel_monitoramento_jarbas()
