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
