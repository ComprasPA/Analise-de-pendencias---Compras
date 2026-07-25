import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go
import os
import json

# 1. CONFIGURAÇÃO DA PÁGINA (Wide com barra de rolagem habilitada)
st.set_page_config(layout="wide", page_title="Panorama Executivo de Suprimentos")

# ==========================================
# PAINEL DE CONFIGURAÇÕES (RETRÁTIL)
# ==========================================
with st.expander("⚙️ Abrir / Fechar Configurações (Upload, Data Base e Tema)", expanded=False):
    col_cfg1, col_cfg2, col_cfg3 = st.columns([2, 1, 1])
    with col_cfg1:
        uploaded_file = st.file_uploader("Upload do arquivo de pendências (.xlsx / .csv)", type=["xlsx", "xls", "csv"])
    with col_cfg2:
        data_base = st.date_input("Data base SLA:", datetime.date.today())
    with col_cfg3:
        tema_selecionado = st.selectbox(
            "Selecione o Tema:",
            ["Padrão do Sistema", "Claro", "Escuro", "Black (Preto Absoluto)"],
            index=0
        )

# ==========================================
# CSS CUSTOMIZADO DINÂMICO
# ==========================================
if tema_selecionado == "Black (Preto Absoluto)":
    css_tema = """
        .stApp { background-color: #000000 !important; color: #f8fafc !important; }
        .header-box { background-color: #111111 !important; border: 1px solid #333333; }
        .resumo-bar, .section-header { background-color: #1a1a1a !important; color: #ffffff !important; border: 1px solid #333333; }
        div[data-testid="stVerticalBlock"] > div[style*="background-color: white"] { background-color: #121212 !important; border: 1px solid #333333 !important; color: #ffffff !important; }
        p, span, label, div, h1, h2, h3, h4, h5, h6 { color: #f8fafc !important; }
    """
elif tema_selecionado == "Escuro":
    css_tema = """
        .stApp { background-color: #0e1117 !important; color: #f8fafc !important; }
        .header-box { background-color: #1f3b58 !important; }
        .resumo-bar, .section-header { background-color: #2b4c7e !important; }
        p, span, label, div, h1, h2, h3, h4, h5, h6 { color: #f8fafc !important; }
    """
else:
    css_tema = ""

st.markdown(f"""
    <style>
    header[data-testid="stHeader"], [data-testid="stDecoration"], .viewerBadge_container__1QSob, [data-testid="manage-app-button"], #MainMenu, footer {{
        visibility: hidden;
        display: none !important;
    }}
    .block-container {{
        padding-top: 1rem;
        padding-bottom: 2rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
        max-width: 100% !important;
    }}
    .header-box {{
        color: white;
        padding: 12px 20px;
        border-radius: 4px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }}
    .header-title {{ font-size: 2.0rem; font-weight: bold; }}
    .header-sub {{ font-size: 1.1rem; }}
    .resumo-bar {{
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 1rem;
        padding: 6px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 15px;
        border-radius: 2px;
    }}
    .section-header {{
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 0.95rem;
        padding: 6px;
        text-transform: uppercase;
        border-radius: 2px;
        margin-bottom: 8px;
    }}
    .gauge-footer {{
        text-align: center;
        font-size: 1.05rem;
        font-weight: 800;
        margin-top: -5px;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.10);
    }}
    div[data-testid="stDataFrame"] {{
        max-width: 85% !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }}
    .stDataFrame td, .stDataFrame th {{
        font-size: 0.9rem !important;
        font-weight: 700 !important;
        padding: 4px 6px !important;
        text-align: center !important;
    }}
    {css_tema}
    </style>
""", unsafe_allow_html=True)

# Cores dinâmicas para títulos de gráficos conforme o tema
cor_texto_grafico = "#ffffff" if tema_selecionado in ["Escuro", "Black (Preto Absoluto)"] else "#111827"

# ==========================================
# MAPEAMENTO DOS COMPRADORES POR CENTRO DE CUSTO
# ==========================================
MAPA_COMPRADORES = {
    '1225': 'Ednilson', '1235': 'Ednilson', '1244': 'Ednilson', '1241': 'Ednilson', '1236': 'Ednilson',
    '1238': 'Dayana', '1243': 'Dayana', '1217': 'Dayana', '1237': 'Dayana',
    '1223': 'Luiz', '1240': 'Luiz', '9001': 'Luiz', '2003': 'Luiz', '2002': 'Luiz', '2001': 'Luiz',
    '3003': 'Luiz', '2010': 'Luiz', '3007': 'Luiz', '3010': 'Luiz', '3000': 'Luiz', '3002': 'Luiz',
    '3006': 'Luiz', '1239': 'Luiz', '3013': 'Luiz', '3024': 'Luiz'
}

# ==========================================
# PROCESSAMENTO ANALÍTICO DE DADOS (MEMÓRIA GLOBAL)
# ==========================================
ARQUIVO_MEMORIA = "base_ativa_painel.xlsx"
ARQUIVO_HISTORICO = "historico_volumetria.json"
df = None

# Carrega histórico anterior (mantendo até 15 dias de registros)
historico = {}
if os.path.exists(ARQUIVO_HISTORICO):
    try:
        with open(ARQUIVO_HISTORICO, "r") as f:
            historico = json.load(f)
    except:
        historico = {}

if "serie_historica" not in historico:
    historico["serie_historica"] = []

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_novo = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8')
        else:
            xls = pd.ExcelFile(uploaded_file)
            sheet_name = 'Solicitações' if 'Solicitações' in xls.sheet_names else xls.sheet_names[0]
            df_novo = pd.read_excel(uploaded_file, sheet_name=sheet_name)
        
        with open(ARQUIVO_MEMORIA, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success("✅ Base atualizada com sucesso por Silvio Silveira! Esta base agora é a padrão para todos os usuários.")
        df = df_novo
    except Exception as e:
        st.error(f"Erro ao ler o arquivo enviado: {e}")

elif os.path.exists(ARQUIVO_MEMORIA):
    try:
        xls = pd.ExcelFile(ARQUIVO_MEMORIA)
        sheet_name = 'Solicitações' if 'Solicitações' in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(ARQUIVO_MEMORIA, sheet_name=sheet_name)
    except Exception as e:
        st.error(f"Erro ao ler a base salva no servidor: {e}")

if df is not None:
    try:
        df.columns = df.columns.astype(str).str.strip()

        col_status = 'STATUS' if 'STATUS' in df.columns else None
        col_criticidade = 'CRITICIDADE' if 'CRITICIDADE' in df.columns else None
        col_sc = 'Solicitação' if 'Solicitação' in df.columns else ('Cod SC. SCM' if 'Cod SC. SCM' in df.columns else None)
        col_cc = 'Centro de Custo' if 'Centro de Custo' in df.columns else None
        
        col_dt_emissao = 'Data Solicitação' if 'Data Solicitação' in df.columns else ('Data emissão Solicitação' if 'Data emissão Solicitação' in df.columns else None)
        col_dt_pedido = 'Data Pedido' if 'Data Pedido' in df.columns else ('Data emissão Pedido' if 'Data emissão Pedido' in df.columns else None)

        if not col_sc or not col_cc or not col_dt_emissao:
            st.error(f"⚠️ Erro: Coluna de solicitação, centro de custo ou 'Data Solicitação' não encontrada. Colunas disponíveis: {list(df.columns)}")
            st.stop()

        # Conversão de Datas
        hoje = pd.to_datetime(data_base)
        df[col_dt_emissao] = pd.to_datetime(df[col_dt_emissao], errors='coerce')
        
        if col_dt_pedido:
            df[col_dt_pedido] = pd.to_datetime(df[col_dt_pedido], errors='coerce')

        # Tratamento Compradores e Centro de Custo (SEM .0)
        df['CC_clean'] = pd.to_numeric(df[col_cc], errors='coerce').fillna(df[col_cc]).astype(str).str.split('.').str[0].str.strip()
        df['Comprador_Resp'] = df['CC_clean'].map(MAPA_COMPRADORES).fillna('Não Mapeado / Outros')
        
        def detalhar_status(x):
            x_str = str(x).strip().upper()
            if x_str == 'FINALIZADO': return 'Atendidas'
            elif 'FORA' in x_str: return 'Fora do Prazo'
            elif 'ATENÇÃO' in x_str: return 'Atenção'
            else: return 'No Prazo'
        
        if col_status:
            df['Status_Detalhado'] = df[col_status].apply(detalhar_status)
        else:
            df['Status_Detalhado'] = 'No Prazo'

        # --- CÁLCULO INTELIGENTE DO SLA ---
        def calcular_sla(row):
            status = str(row.get(col_status, '')).strip().upper()
            dt_ini = row[col_dt_emissao]
            if pd.isna(dt_ini):
                return 0
            
            if status == 'FINALIZADO' and col_dt_pedido and not pd.isna(row[col_dt_pedido]):
                dias = (row[col_dt_pedido] - dt_ini).days
                return max(dias, 0)
            else:
                dias = (hoje - dt_ini).days
                return max(dias, 0)

        df['Days'] = df.apply(calcular_sla, axis=1)

        df_aberto = df[df['Status_Detalhado'] != 'Atendidas'].copy()
        df_aberto = df_aberto.dropna(subset=[col_sc])
        df_aberto[col_sc] = df_aberto[col_sc].astype(str).str.split('.').str[0].str.zfill(6)

        total_linhas_aberto = int(len(df_aberto)) 
        unique_scs_aberto = df_aberto.drop_duplicates(subset=[col_sc]).copy()
        total_sc_unicas_aberto = int(len(unique_scs_aberto))
        
        # --- GESTÃO DO HISTÓRICO DE 15 DIAS ---
        data_str = hoje.strftime("%Y-%m-%d")
        serie_hist = historico["serie_historica"]
        
        registro_hoje = {"data": data_str, "total_scs": total_sc_unicas_aberto, "total_itens": total_linhas_aberto}
        
        if serie_hist and serie_hist[-1]["data"] == data_str:
            serie_hist[-1] = registro_hoje
        else:
            serie_hist.append(registro_hoje)
            
        if len(serie_hist) > 15:
            serie_hist = serie_hist[-15:]
            
        historico["serie_historica"] = serie_hist
        
        diff_scs = 0
        diff_itens = 0
        
        if len(serie_hist) >= 2:
            penultimo = serie_hist[-2]
            diff_scs = int(total_sc_unicas_aberto - penultimo["total_scs"])
            diff_itens = int(total_linhas_aberto - penultimo["total_itens"])

        if uploaded_file is not None or not os.path.exists(ARQUIVO_HISTORICO):
            with open(ARQUIVO_HISTORICO, "w") as f:
                json.dump(historico, f)

        # --- CÁLCULO DO SLA MÉDIO GERAL ATUAL ---
        df_geral_crit = df.copy()
        if col_dt_emissao in df_geral_crit.columns:
            mask_luiz_antigo = (df_geral_crit['Comprador_Resp'] == 'Luiz') & (df_geral_crit[col_dt_emissao] < pd.to_datetime('2026-07-06'))
            df_geral_crit = df_geral_crit[~mask_luiz_antigo]

        if col_criticidade:
            df_geral_crit = df_geral_crit[df_geral_crit[col_criticidade].astype(str).str.upper().isin(['ROTINEIRA', 'EMERGENCIAL'])]

        mean_rot = df_geral_crit[df_geral_crit[col_criticidade].astype(str).str.upper() == 'ROTINEIRA']['Days'].mean() if col_criticidade and not df_geral_crit.empty else float('nan')
        mean_emg = df_geral_crit[df_geral_crit[col_criticidade].astype(str).str.upper() == 'EMERGENCIAL']['Days'].mean() if col_criticidade and not df_geral_crit.empty else float('nan')

        sla_geral_rot = int(round(mean_rot, 0)) if not pd.isna(mean_rot) else 0
        sla_geral_emg = int(round(mean_emg, 0)) if not pd.isna(mean_emg) else 0

        criticos_df = unique_scs_aberto[unique_scs_aberto['Days'] >= 20]
        
        # Consolidações para os Velocímetros da Linha 1
        status_counts = df_aberto['Status_Detalhado'].value_counts()
        qtd_no_prazo = status_counts.get('No Prazo', 0)
        qtd_atencao = status_counts.get('Atenção', 0)
        qtd_fora = status_counts.get('Fora do Prazo', 0)
        
        crit_counts = df_aberto[col_criticidade].astype(str).str.upper().value_counts() if col_criticidade else {}
        qtd_rot = crit_counts.get('ROTINEIRA', 0)
        qtd_emg = crit_counts.get('EMERGENCIAL', 0)

        # ==========================================
        # PASSO 1: QUADRANTE DE VOLUMETRIA E VELOCÍMETROS GERAIS (COM LINHA DIVISÓRIA VERTICAL)
        # ==========================================
        st.markdown(f"""
        <div class="header-box">
            <span class="header-title">PANORAMA DE REQUISIÇÕES PENDENTES DE COMPRA (EM ABERTO)</span>
            <span class="header-sub">DADOS CONSOLIDADOS | {hoje.strftime("%d/%m/%Y")}</span>
        </div>
        <div class="resumo-bar">DIAGNÓSTICO E VALIDAÇÃO ESTRATÉGICA (VOLUMETRIA, STATUS E CRITICIDADE)</div>
        """, unsafe_allow_html=True)

        def criar_gauge(titulo, valor, max_val, cor_barra, sufixo="", altura=130, title_size=10):
            fig = go.Figure(go.Indicator(
                mode = "gauge+number", value = valor,
                number = {'suffix': sufixo, 'font': {'size': 20, 'color': cor_texto_grafico, 'family': 'Arial Black'}},
                title = {'text': titulo, 'font': {'size': title_size, 'color': cor_texto_grafico, 'family': 'Arial Black'}},
                gauge = {
                    'axis': {'range': [None, max_val], 'tickwidth': 1, 'tickcolor': "#475569", 'tickfont': {'size': 9, 'color': cor_texto_grafico, 'family': 'Arial Black'}},
                    'bar': {'color': cor_barra}, 'bgcolor': "rgba(0,0,0,0)", 'borderwidth': 0,
                    'steps': [{'range': [0, max_val * 0.6], 'color': '#2a3b4c' if tema_selecionado != 'Claro' else '#f1f5f9'}, 
                              {'range': [max_val * 0.6, max_val], 'color': '#1f2937' if tema_selecionado != 'Claro' else '#e2e8f0'}],
                }
            ))
            fig.update_layout(height=altura, margin=dict(l=10, r=10, t=40, b=5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            return fig

        row1_c1, row1_c2, row1_c3, row1_c4, row1_div, row1_c5, row1_c6 = st.columns([1.5, 1, 1, 1, 0.2, 1, 1])

        with row1_c1:
            cor_delta_scs = "#ff6b6b" if diff_scs > 0 else "#51cf66"
            sinal_scs = "+" if diff_scs > 0 else ""
            seta_scs = "▲" if diff_scs > 0 else ("▼" if diff_scs < 0 else "•")
            
            cor_delta_itens = "#ff6b6b" if diff_itens > 0 else "#51cf66"
            sinal_itens = "+" if diff_itens > 0 else ""
            seta_itens = "▲" if diff_itens > 0 else ("▼" if diff_itens < 0 else "•")

            st.markdown(f"""
            <div style="border: 1px solid #cbd5e1; border-radius: 4px; padding: 8px; text-align: center; height: 150px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 0.85rem; font-family: 'Arial Black'; margin-bottom: 2px;">VOLUMETRIA EM ABERTO</div>
                <div style="font-size: 1.4rem; font-weight: bold; color: #4dabf7; line-height: 1;">{total_sc_unicas_aberto} <span style="font-size: 0.9rem; color: {cor_delta_scs};">{seta_scs} {sinal_scs}{abs(diff_scs)}</span></div>
                <div style="font-size: 0.62rem; font-weight: bold;">Solicitações (SCs) (vs ant.)</div>
                <div style="border-top: 1px dashed #cbd5e1; margin: 3px 0;"></div>
                <div style="font-size: 1.4rem; font-weight: bold; color: #ffa94d; line-height: 1;">{total_linhas_aberto} <span style="font-size: 0.9rem; color: {cor_delta_itens};">{seta_itens} {sinal_itens}{abs(diff_itens)}</span></div>
                <div style="font-size: 0.62rem; font-weight: bold;">Total de Itens (vs ant.)</div>
            </div>
            """, unsafe_allow_html=True)

        def render_gauge(col, titulo, valor, max_val, cor):
            with col:
                st.plotly_chart(criar_gauge(titulo, valor, max_val, cor, altura=130), use_container_width=True, config={'displayModeBar': False})
                perc = (valor / max_val * 100) if max_val > 0 else 0
                st.markdown(f"<div class='gauge-footer' style='color: {cor};'>{perc:.1f}%</div>", unsafe_allow_html=True)

        render_gauge(row1_c2, "NO PRAZO", qtd_no_prazo, total_linhas_aberto, "#388e3c")
        render_gauge(row1_c3, "ATENÇÃO", qtd_atencao, total_linhas_aberto, "#d97706")
        render_gauge(row1_c4, "FORA DO PRAZO", qtd_fora, total_linhas_aberto, "#e53e3e")

        with row1_div:
            st.markdown(f"""
            <div style="border-left: 2px solid {'#333333' if tema_selecionado != 'Claro' else '#cbd5e1'}; height: 140px; margin: auto; margin-top: 5px;"></div>
            """, unsafe_allow_html=True)

        render_gauge(row1_c5, "ROTINEIRA", qtd_rot, total_linhas_aberto, "#2b6cb0")
        render_gauge(row1_c6, "EMERGENCIAL", qtd_emg, total_linhas_aberto, "#805ad5")

        st.markdown("<br>", unsafe_allow_html=True)

        # ==========================================
        # PASSO 2: CENTROS DE CUSTO & ITENS CRÍTICOS (3 COLUNAS)
        # ==========================================
        st.markdown("---")
        row2_c1, row2_c2, row2_c3 = st.columns([1, 1, 0.6])

        with row2_c1:
            st.markdown('<div class="section-header">TOP 10 CC (VOLUME DE ITENS)</div>', unsafe_allow_html=True)
            cc_volume = df_aberto.groupby('CC_clean').size().reset_index(name='Quantidade').sort_values(by='Quantidade', ascending=False).head(10)
            cc_volume['CC_clean'] = cc_volume['CC_clean'].astype(str)
            
            cores_barras = ['#3273a8'] + ['#ed8034'] * (len(cc_volume) - 1)
            fig_cc_it = go.Figure(go.Bar(
                x=cc_volume.sort_values(by='Quantidade', ascending=True)['Quantidade'],
                y=cc_volume.sort_values(by='Quantidade', ascending=True)['CC_clean'],
                orientation='h', text=cc_volume.sort_values(by='Quantidade', ascending=True)['Quantidade'],
                textposition='outside', textfont=dict(size=11, color=cor_texto_grafico, family='Arial Black'), marker_color=cores_barras[::-1]
            ))
            fig_cc_it.update_layout(
                xaxis_title="Qtd. Itens", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color=cor_texto_grafico),
                margin=dict(l=5, r=10, t=10, b=10), height=320, xaxis=dict(showgrid=True, gridcolor='#333333' if tema_selecionado != 'Claro' else '#e2e8f0'), yaxis=dict(type='category', tickfont=dict(family='Arial Black', size=10, color=cor_texto_grafico))
            )
            st.plotly_chart(fig_cc_it, use_container_width=True, config={'displayModeBar': False})

        with row2_c2:
            st.markdown('<div class="section-header">TOP 10 CC (QTD. REQUISIÇÕES)</div>', unsafe_allow_html=True)
            cc_scs = unique_scs_aberto.groupby('CC_clean')[col_sc].nunique().reset_index(name='Qtd_SCs').sort_values(by='Qtd_SCs', ascending=False).head(10)
            cc_scs['CC_clean'] = cc_scs['CC_clean'].astype(str)
            
            cores_barras_sc = ['#2b6cb0'] + ['#319795'] * (len(cc_scs) - 1)
            fig_cc_sc = go.Figure(go.Bar(
                x=cc_scs.sort_values(by='Qtd_SCs', ascending=True)['Qtd_SCs'],
                y=cc_scs.sort_values(by='Qtd_SCs', ascending=True)['CC_clean'],
                orientation='h', text=cc_scs.sort_values(by='Qtd_SCs', ascending=True)['Qtd_SCs'],
                textposition='outside', textfont=dict(size=11, color=cor_texto_grafico, family='Arial Black'), marker_color=cores_barras_sc[::-1]
            ))
            fig_cc_sc.update_layout(
                xaxis_title="Qtd. Requisições (SCs)", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color=cor_texto_grafico),
                margin=dict(l=5, r=10, t=10, b=10), height=320, xaxis=dict(showgrid=True, gridcolor='#333333' if tema_selecionado != 'Claro' else '#e2e8f0'), yaxis=dict(type='category', tickfont=dict(family='Arial Black', size=10, color=cor_texto_grafico))
            )
            st.plotly_chart(fig_cc_sc, use_container_width=True, config={'displayModeBar': False})

        with row2_c3:
            st.markdown('<div class="section-header">ITENS CRÍTICOS</div>', unsafe_allow_html=True)
            top_critical = criticos_df.sort_values(by='Days', ascending=False)[[col_sc, 'CC_clean', 'Days']].head(8)
            top_critical.columns = ['Nº SC', 'C. CUSTO', 'ATRASO']
            top_critical['ATRASO'] = top_critical['ATRASO'].astype(str) + " DIAS 🔥"
            st.dataframe(top_critical, use_container_width=True, height=320, hide_index=True)

        # ==========================================
        # PASSO 3: TOP 10 COMPRA DIRETA & CRITICIDADE VS STATUS (COM CAIXA DE SETA AO LADO)
        # ==========================================
        st.markdown("---")
        row3_c1, row3_c2, row3_c3 = st.columns([1, 1, 0.4])

        col_tipo = None
        for c in ['Tipo SC', 'Tipo', 'Grupo', 'Subgrupo']:
            if c in df.columns:
                col_tipo = c
                break

        with row3_c1:
            st.markdown('<div class="section-header">TOP 10 COMPRA DIRETA (QTD. REQUISIÇÕES)</div>', unsafe_allow_html=True)
            
            df_direta = df_aberto.copy()
            if col_tipo:
                mask_direta = df_direta[col_tipo].astype(str).str.upper().str.contains('DIRETA', na=False)
                if mask_direta.sum() > 0:
                    df_direta = df_direta[mask_direta]
            
            cc_direta = df_direta.drop_duplicates(subset=[col_sc]).groupby('CC_clean')[col_sc].nunique().reset_index(name='Qtd_SCs').sort_values(by='Qtd_SCs', ascending=False).head(10)
            cc_direta['CC_clean'] = cc_direta['CC_clean'].astype(str)

            if not cc_direta.empty:
                cores_direta = ['#2b6cb0'] + ['#319795'] * (len(cc_direta) - 1)
                fig_direta = go.Figure(go.Bar(
                    x=cc_direta.sort_values(by='Qtd_SCs', ascending=True)['Qtd_SCs'],
                    y=cc_direta.sort_values(by='Qtd_SCs', ascending=True)['CC_clean'],
                    orientation='h', text=cc_direta.sort_values(by='Qtd_SCs', ascending=True)['Qtd_SCs'],
                    textposition='outside', textfont=dict(size=11, color=cor_texto_grafico, family='Arial Black'), marker_color=cores_direta[::-1]
                ))
                fig_direta.update_layout(
                    xaxis_title="Qtd. Requisições (Compra Direta)", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=320,
                    font=dict(color=cor_texto_grafico),
                    margin=dict(l=5, r=20, t=10, b=10), xaxis=dict(showgrid=True, gridcolor='#333333' if tema_selecionado != 'Claro' else '#e2e8f0'), yaxis=dict(type='category', tickfont=dict(family='Arial Black', color=cor_texto_grafico))
                )
                st.plotly_chart(fig_direta, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Nenhum registro de Compra Direta encontrado.")

        with row3_c2:
            st.markdown('<div class="section-header">CRITICIDADE VS STATUS (QTD. ITENS)</div>', unsafe_allow_html=True)
            if col_criticidade and col_status:
                df_crit_stat = df_aberto[df_aberto[col_criticidade].astype(str).str.upper().isin(['ROTINEIRA', 'EMERGENCIAL'])]
                if not df_crit_stat.empty:
                    crit_stats = df_crit_stat.groupby([col_criticidade, col_status]).size().reset_index(name='Quantidade')
                    color_map = {'NO PRAZO': '#388e3c', 'ATENÇÃO': '#d97706', 'FORA DO PRAZO': '#e53e3e'}
                    fig_crit_stat = go.Figure()
                    for status_val in ['NO PRAZO', 'ATENÇÃO', 'FORA DO PRAZO']:
                        df_sub = crit_stats[crit_stats[col_status].str.upper() == status_val]
                        if not df_sub.empty:
                            fig_crit_stat.add_trace(go.Bar(
                                x=df_sub[col_criticidade], y=df_sub['Quantidade'], name=status_val.title(),
                                marker_color=color_map.get(status_val, '#718096'),
                                text=df_sub['Quantidade'], textposition='auto', 
                                textfont=dict(size=12, color=cor_texto_grafico, family='Arial Black')
                            ))
                    fig_crit_stat.update_layout(
                        barmode='group', xaxis_title="", yaxis_title="Qtd. ITENS EM ABERTO", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=320,
                        font=dict(color=cor_texto_grafico),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(family='Arial Black', color=cor_texto_grafico)),
                        xaxis=dict(showgrid=False, tickfont=dict(size=12, family='Arial Black', color=cor_texto_grafico)), yaxis=dict(showgrid=True, gridcolor='#333333' if tema_selecionado != 'Claro' else '#e2e8f0')
                    )
                    st.plotly_chart(fig_crit_stat, use_container_width=True, config={'displayModeBar': False})

        with row3_c3:
            st.markdown('<div class="section-header">TENDÊNCIA (ANT. VS ATUAL)</div>', unsafe_allow_html=True)
            
            cor_seta_scs = "#ff6b6b" if diff_scs > 0 else ("#51cf66" if diff_scs < 0 else "#94a3b8")
            simbolo_scs = "▲" if diff_scs > 0 else ("▼" if diff_scs < 0 else "•")
            
            cor_seta_itens = "#ff6b6b" if diff_itens > 0 else ("#51cf66" if diff_itens < 0 else "#94a3b8")
            simbolo_itens = "▲" if diff_itens > 0 else ("▼" if diff_itens < 0 else "•")

            st.markdown(f"""
            <div style="background-color: {'#111827' if tema_selecionado != 'Claro' else '#f8fafc'}; border: 1px solid {'#374151' if tema_selecionado != 'Claro' else '#cbd5e1'}; border-radius: 4px; padding: 18px; text-align: center; height: 320px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 0.85rem; font-family: 'Arial Black'; color: {'#60a5fa' if tema_selecionado != 'Claro' else '#1f3b58'}; margin-bottom: 8px;">VÁRIAÇÃO DE SCs</div>
                <div style="font-size: 2.2rem; font-weight: bold; color: {cor_seta_scs}; line-height: 1.1;">{simbolo_scs} {abs(diff_scs)}</div>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-bottom: 20px;">{'Aumento' if diff_scs > 0 else ('Redução' if diff_scs < 0 else 'Estável')} de solicitações</div>
                
                <div style="font-size: 0.85rem; font-family: 'Arial Black'; color: {'#60a5fa' if tema_selecionado != 'Claro' else '#1f3b58'}; margin-bottom: 8px;">VÁRIAÇÃO DE ITENS</div>
                <div style="font-size: 2.2rem; font-weight: bold; color: {cor_seta_itens}; line-height: 1.1;">{simbolo_itens} {abs(diff_itens)}</div>
                <div style="font-size: 0.75rem; color: #94a3b8;">{'Aumento' if diff_itens > 0 else ('Redução' if diff_itens < 0 else 'Estável')} de itens</div>
            </div>
            """, unsafe_allow_html=True)

        # ==========================================
        # PASSO 4: DESEMPENHO POR COMPRADOR
        # ==========================================
        st.markdown("---")
        st.markdown('<div class="section-header" style="background-color: #2b4c7e;">DESEMPENHO INDIVIDUAL POR COMPRADOR</div>', unsafe_allow_html=True)
        
        row4_c1, row4_c2, row4_c3 = st.columns(3)
        compradores = ['Ednilson', 'Dayana', 'Luiz']
        colunas_st = [row4_c1, row4_c2, row4_c3]
        
        color_status_map = {'No Prazo': '#388e3c', 'Atenção': '#d97706', 'Fora do Prazo': '#e53e3e'}
        ordem_status_aberto = ['Fora do Prazo', 'Atenção', 'No Prazo']
        
        for comp, col_st in zip(compradores, colunas_st):
            with col_st:
                st.markdown(f'<div style="text-align: center; font-weight: bold; font-size: 1.15rem; margin-bottom: 2px;">👤 {comp}</div>', unsafe_allow_html=True)
                
                df_comp_total = df[df['Comprador_Resp'] == comp].copy()
                
                if comp == 'Luiz' and col_dt_emissao in df_comp_total.columns:
                    df_comp_total = df_comp_total[df_comp_total[col_dt_emissao] >= pd.to_datetime('2026-07-06')]
                
                if not df_comp_total.empty and 'Status_Detalhado' in df_comp_total.columns:
                    
                    total_emitidas = len(df_comp_total)
                    qtd_atendidas = len(df_comp_total[df_comp_total['Status_Detalhado'] == 'Atendidas'])
                    taxa_rendimento_comp = (qtd_atendidas / total_emitidas * 100) if total_emitidas > 0 else 0
                    
                    if col_criticidade:
                        df_comp_crit = df_comp_total[df_comp_total[col_criticidade].astype(str).str.upper().isin(['ROTINEIRA', 'EMERGENCIAL'])]
                    else:
                        df_comp_crit = pd.DataFrame()
                        
                    sla_rot_val = int(round(df_comp_crit[df_comp_crit[col_criticidade].astype(str).str.upper() == 'ROTINEIRA']['Days'].mean(), 0)) if not df_comp_crit.empty and not pd.isna(df_comp_crit[df_comp_crit[col_criticidade].astype(str).str.upper() == 'ROTINEIRA']['Days'].mean()) else 0
                    sla_emg_val = int(round(df_comp_crit[df_comp_crit[col_criticidade].astype(str).str.upper() == 'EMERGENCIAL']['Days'].mean(), 0)) if not df_comp_crit.empty and not pd.isna(df_comp_crit[df_comp_crit[col_criticidade].astype(str).str.upper() == 'EMERGENCIAL']['Days'].mean()) else 0

                    # 1. Velocímetro de Rendimento
                    cor_gauge_comp = '#388e3c' if taxa_rendimento_comp >= 75 else ('#d97706' if taxa_rendimento_comp >= 50 else '#e53e3e')
                    fig_gauge = criar_gauge("RENDIMENTO (ATENDIDAS / TOTAL)", taxa_rendimento_comp, 100, cor_gauge_comp, sufixo="%", altura=120, title_size=11)
                    st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})

                    # 2. Gráfico de Barras do Backlog
                    df_comp_aberto = df_comp_total[df_comp_total['Status_Detalhado'] != 'Atendidas'].copy()
                    
                    if not df_comp_aberto.empty:
                        comp_stats = df_comp_aberto.groupby('Status_Detalhado').size().reset_index(name='Quantidade')
                        total_aberto = comp_stats['Quantidade'].sum()
                        comp_stats['Percentual'] = (comp_stats['Quantidade'] / total_aberto * 100).round(1)
                        
                        comp_stats['Status_Detalhado'] = pd.Categorical(comp_stats['Status_Detalhado'], categories=ordem_status_aberto, ordered=True)
                        comp_stats = comp_stats.sort_values('Status_Detalhado')
                        
                        cores = [color_status_map.get(s, '#718096') for s in comp_stats['Status_Detalhado']]
                        comp_stats['Texto_Label'] = comp_stats.apply(lambda row: f"{int(row['Quantidade'])} ({row['Percentual']}%)", axis=1)
                        
                        fig_comp_ind = go.Figure(go.Bar(
                            x=comp_stats['Percentual'],
                            y=comp_stats['Status_Detalhado'],
                            orientation='h',
                            text=comp_stats['Texto_Label'],
                            textposition='outside',
                            textfont=dict(size=11, color=cor_texto_grafico, family='Arial Black'), 
                            marker_color=cores
                        ))
                        
                        fig_comp_ind.update_layout(
                            xaxis_title="% do Backlog Restante", yaxis_title="",
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=140,
                            font=dict(color=cor_texto_grafico),
                            margin=dict(l=5, r=30, t=0, b=10),
                            xaxis=dict(showgrid=True, gridcolor='#333333' if tema_selecionado != 'Claro' else '#e2e8f0', range=[0, max(comp_stats['Percentual'].max() * 1.35, 100)], tickfont=dict(size=9, color=cor_texto_grafico)), 
                            yaxis=dict(type='category', tickfont=dict(family='Arial Black', size=10, color=cor_texto_grafico))
                        )
                        st.plotly_chart(fig_comp_ind, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.info(f"Fila limpa! Nenhum item pendente para {comp}.")
                    
                    # 3. Caixa de Itens Atendidos
                    st.markdown(f"""
                    <div style='text-align: center; font-size: 0.9rem; font-weight: bold; background-color: {'#1a202c' if tema_selecionado != 'Claro' else '#f1f5f9'}; color: {'#63b3ed' if tema_selecionado != 'Claro' else '#2b6cb0'}; padding: 6px; border-radius: 4px; margin-top: 10px; margin-bottom: 0px; border: 1px solid {'#333333' if tema_selecionado != 'Claro' else 'transparent'};'>
                        ✅ {qtd_atendidas} de {total_emitidas} Itens Atendidos
                    </div>
                    """, unsafe_allow_html=True)

                    # 4. Velocímetros de SLA
                    cor_rot = "#ff6b6b" if sla_rot_val > 15 else "#339af0"
                    fig_rot = go.Figure(go.Indicator(
                        mode = "gauge+number", value = sla_rot_val,
                        number = {'font': {'size': 20, 'color': cor_texto_grafico, 'family': 'Arial Black'}},
                        gauge = {
                            'axis': {'range': [0, 30], 'tickwidth': 1, 'tickcolor': "#475569", 'tickfont': {'size': 9, 'color': cor_texto_grafico, 'family': 'Arial Black'}},
                            'bar': {'color': cor_rot}, 'bgcolor': "rgba(0,0,0,0)", 'borderwidth': 0,
                            'steps': [{'range': [0, 15], 'color': '#2a3b4c' if tema_selecionado != 'Claro' else '#e2e8f0'}, 
                                      {'range': [15, 30], 'color': '#4a2525' if tema_selecionado != 'Claro' else '#fed7d7'}],
                            'threshold': {'line': {'color': 'red', 'width': 4}, 'thickness': 0.75, 'value': 15}
                        }
                    ))
                    fig_rot.update_layout(height=100, margin=dict(l=5, r=5, t=25, b=5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

                    cor_emg = "#ff6b6b" if sla_emg_val > 3 else "#b197fc"
                    fig_emg = go.Figure(go.Indicator(
                        mode = "gauge+number", value = sla_emg_val,
                        number = {'font': {'size': 20, 'color': cor_texto_grafico, 'family': 'Arial Black'}},
                        gauge = {
                            'axis': {'range': [0, 20], 'tickwidth': 1, 'tickcolor': "#475569", 'tickfont': {'size': 10, 'color': cor_texto_grafico, 'family': 'Arial Black'}},
                            'bar': {'color': cor_emg}, 'bgcolor': "rgba(0,0,0,0)", 'borderwidth': 0,
                            'steps': [{'range': [0, 3], 'color': '#2a3b4c' if tema_selecionado != 'Claro' else '#e2e8f0'}, 
                                      {'range': [3, 20], 'color': '#4a2525' if tema_selecionado != 'Claro' else '#fed7d7'}],
                            'threshold': {'line': {'color': 'red', 'width': 4}, 'thickness': 0.75, 'value': 3}
                        }
                    ))
                    fig_emg.update_layout(height=100, margin=dict(l=5, r=5, t=25, b=5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

                    sub_c1, sub_c2 = st.columns(2)
                    with sub_c1:
                        st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
                        st.plotly_chart(fig_rot, use_container_width=True, config={'displayModeBar': False})
                        st.markdown(f"<div style='text-align: center; font-size: 0.8rem; font-weight: bold; color: {cor_texto_grafico}; margin-top: -2px;'>SLA ROTINEIRA</div><div style='text-align: center; font-size: 0.75rem; font-weight: bold; color: #94a3b8; margin-top: 2px;'>Limite: 15 dias</div>", unsafe_allow_html=True)
                    with sub_c2:
                        st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
                        st.plotly_chart(fig_emg, use_container_width=True, config={'displayModeBar': False})
                        st.markdown(f"<div style='text-align: center; font-size: 0.8rem; font-weight: bold; color: {cor_texto_grafico}; margin-top: -2px;'>SLA EMERGENCIAL</div><div style='text-align: center; font-size: 0.75rem; font-weight: bold; color: #94a3b8; margin-top: 2px;'>Limite: 3 dias</div>", unsafe_allow_html=True)
                    
                else:
                    st.info(f"Sem dados mapeados para {comp}.")

        # ==========================================
        # PASSO 5: CAIXA DE SLA MÉDIO GERAL (CONSOLIDADO) - DUAS CAIXINHAS LADO A LADO SEM O TEXTO DE DIA ANTERIOR
        # ==========================================
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header" style="background-color: #111827; border: 1px solid #374151; margin-bottom: 12px;">📊 SLA MÉDIO GERAL CONSOLIDADO</div>', unsafe_allow_html=True)

        col_box1, col_box2 = st.columns(2)

        with col_box1:
            cor_val_rot = "#ff6b6b" if sla_geral_rot > 15 else "#339af0"
            st.markdown(f"""
            <div style="background-color: {'#111827' if tema_selecionado != 'Claro' else '#f8fafc'}; border: 1px solid {'#374151' if tema_selecionado != 'Claro' else '#cbd5e1'}; border-radius: 6px; padding: 15px; text-align: center;">
                <div style="font-size: 1.0rem; font-family: 'Arial Black'; color: {'#60a5fa' if tema_selecionado != 'Claro' else '#1f3b58'}; margin-bottom: 0px; text-transform: uppercase;">SLA ROTINEIRA MÉDIO</div>
                <div style="font-size: 0.75rem; font-weight: bold; color: #94a3b8; margin-bottom: 6px;">(Limite: 15 dias)</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: {cor_val_rot}; line-height: 1.1;">{sla_geral_rot} dias</div>
            </div>
            """, unsafe_allow_html=True)

        with col_box2:
            cor_val_emg = "#ff6b6b" if sla_geral_emg > 3 else "#b197fc"
            st.markdown(f"""
            <div style="background-color: {'#111827' if tema_selecionado != 'Claro' else '#f8fafc'}; border: 1px solid {'#374151' if tema_selecionado != 'Claro' else '#cbd5e1'}; border-radius: 6px; padding: 15px; text-align: center;">
                <div style="font-size: 1.0rem; font-family: 'Arial Black'; color: {'#60a5fa' if tema_selecionado != 'Claro' else '#1f3b58'}; margin-bottom: 0px; text-transform: uppercase;">SLA EMERGENCIAL MÉDIO</div>
                <div style="font-size: 0.75rem; font-weight: bold; color: #94a3b8; margin-bottom: 6px;">(Limite: 3 dias)</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: {cor_val_emg}; line-height: 1.1;">{sla_geral_emg} dias</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <hr style='margin: 15px 0px 8px 0px;'>
        <div style="font-size: 1.05rem; display: flex; justify-content: space-between; font-weight: 700;">
            <span><b>→ Base Salva:</b> O último arquivo enviado fica salvo como base de consulta para toda a equipe.</span>
            <span><b>Metodologia:</b> Limites vigentes: Rotineira (&lt;= 15 dias) | Emergencial (&lt;= 3 dias).</span>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"⚠️ Erro analítico no processamento. Detalhe técnico: {e}")
else:
    st.info("💡 Clique em **⚙️ Abrir / Fechar Configurações** no topo para atualizar a base de dados.")
