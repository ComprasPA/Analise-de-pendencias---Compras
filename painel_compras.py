import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Panorama Executivo de Suprimentos")

# ==========================================
# CSS CUSTOMIZADO (Layout Compacto e Limpo)
# ==========================================
st.markdown("""
    <style>
    header[data-testid="stHeader"] {
        visibility: hidden;
        display: none;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .header-box {
        background-color: #1f3b58;
        color: white;
        padding: 14px 22px;
        border-radius: 4px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .header-title {
        font-size: 1.5rem;
        font-weight: bold;
    }
    .header-sub {
        font-size: 1.2rem;
    }
    .resumo-bar {
        background-color: #2b4c7e;
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 1.15rem;
        padding: 8px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 25px;
        border-radius: 2px;
    }
    .section-header {
        background-color: #1f3b58;
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 1.15rem;
        padding: 8px;
        text-transform: uppercase;
        border-radius: 2px;
        margin-bottom: 8px;
    }
    .gauge-footer {
        text-align: center;
        color: #1e293b;
        font-size: 1.2rem;
        font-weight: 800;
        margin-top: 5px;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.15);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# PAINEL RETRÁTIL (Configurações e Upload)
# ==========================================
with st.expander("⚙️ Abrir / Fechar Configurações (Upload de Arquivo e Data Base)", expanded=False):
    top_c1, top_c2 = st.columns([3, 1])
    with top_c1:
        uploaded_file = st.file_uploader("Upload do arquivo de pendências (.xlsx/.csv)", type=["xlsx", "xls", "csv"])
    with top_c2:
        data_base = st.date_input("Data base para cálculo de SLA:", datetime.date.today())

# ==========================================
# PROCESSAMENTO ANALÍTICO DE DADOS
# ==========================================
if uploaded_file is not None:
    try:
        # Leitura estruturada do layout real do Protheus (cabeçalho na linha 1)
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8', header=1)
        else:
            df = pd.read_excel(uploaded_file, header=1)
            
        df.columns = df.columns.astype(str).str.strip()

        col_sc = 'Numero da SC' if 'Numero da SC' in df.columns else None
        col_cc = 'C Custo' if 'C Custo' in df.columns else None
        col_dt = 'DT Emissao' if 'DT Emissao' in df.columns else None

        if not col_sc or not col_cc or not col_dt:
            st.error(f"⚠️ Erro: O arquivo não contém as colunas esperadas ('Numero da SC', 'C Custo', 'DT Emissao'). Colunas encontradas: {list(df.columns)}")
            st.stop()

        df = df.dropna(subset=[col_sc])
        hoje = pd.to_datetime(data_base)
        df[col_dt] = pd.to_datetime(df[col_dt], errors='coerce')
        df['Days'] = (hoje - df[col_dt]).dt.days

        total_linhas = len(df) 
        unique_scs = df.drop_duplicates(subset=[col_sc]).copy()
        total_sc_unicas = len(unique_scs)
        
        criticos_df = unique_scs[unique_scs['Days'] >= 20]
        backlog_critico = len(criticos_df)
        
        no_prazo = total_sc_unicas - backlog_critico
        taxa_atendimento_val = (no_prazo / total_sc_unicas * 100) if total_sc_unicas > 0 else 100

        # ==========================================
        # PASSO 1: CABEÇALHO E VELOCÍMETROS
        # ==========================================
        st.markdown(f"""
        <div class="header-box">
            <span class="header-title">PANORAMA DE REQUISIÇÕES PENDENTES DE COMPRA (EM ABERTO)</span>
            <span class="header-sub">DADOS CONSOLIDADOS | {hoje.strftime("%d/%m/%Y")}</span>
        </div>
        <div class="resumo-bar">DIAGNÓSTICO E VALIDAÇÃO ESTRATÉGICA (VELOCÍMETROS DE DESEMPENHO)</div>
        """, unsafe_allow_html=True)

        def criar_gauge(titulo, valor, max_val, cor_barra, sufixo=""):
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = valor,
                number = {'suffix': sufixo, 'font': {'size': 34, 'color': '#1f3b58', 'family': 'Arial Black'}},
                title = {'text': titulo, 'font': {'size': 16, 'color': '#111827', 'family': 'Arial Black'}},
                gauge = {
                    'axis': {'range': [None, max_val], 'tickwidth': 1, 'tickcolor': "#475569", 'tickfont': {'size': 13, 'family': 'Arial Black'}},
                    'bar': {'color': cor_barra},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 0,
                    'steps': [
                        {'range': [0, max_val * 0.6], 'color': '#f1f5f9'},
                        {'range': [max_val * 0.6, max_val], 'color': '#e2e8f0'}
                    ],
                }
            ))
            fig.update_layout(height=180, margin=dict(l=20, r=20, t=45, b=10), paper_bgcolor='rgba(0,0,0,0)')
            return fig

        gauge_col1, gauge_col2, gauge_col3 = st.columns(3)

        with gauge_col1:
            max_sc = max(total_sc_unicas * 1.5, 10)
            fig1 = criar_gauge("TOTAL DE REQUISIÇÕES (ÚNICAS)", total_sc_unicas, max_sc, "#2b6cb0")
            st.plotly_chart(fig1, use_container_width=True)
            st.markdown(f"<div class='gauge-footer'>Volume Bruto: <b>{total_linhas} itens</b></div>", unsafe_allow_html=True)

        with gauge_col2:
            max_backlog = max(total_sc_unicas, 10)
            fig2 = criar_gauge("BACKLOG CRÍTICO (>=20 DIAS)", backlog_critico, max_backlog, "#e53e3e")
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown(f"<div class='gauge-footer' style='color: #e53e3e;'><b>{(backlog_critico/total_sc_unicas*100 if total_sc_unicas > 0 else 0):.1f}%</b> das SCs ativas</div>", unsafe_allow_html=True)

        with gauge_col3:
            fig3 = criar_gauge("TAXA DE ATENDIMENTO / SAÚDE", round(taxa_atendimento_val, 1), 100, "#388e3c", sufixo="%")
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown(f"<div class='gauge-footer' style='color: #388e3c;'>Dentro do SLA padrão (&lt;20 dias)</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ==========================================
        # PASSO 2: RENDERIZAÇÃO DOS GRÁFICOS E TABELA COMPACTA
        # ==========================================
        st.markdown("---")
        
        # Dividimos em 3 colunas: [Gráfico 1: Itens] [Gráfico 2: Requisições Únicas] [Tabela: Críticos Compacta]
        col_g1, col_g2, col_tabela = st.columns([1, 1, 1.1])

        with col_g1:
            st.markdown('<div class="section-header">TOP 10 CC (VOLUME DE ITENS)</div>', unsafe_allow_html=True)
            
            cc_volume = df.groupby(col_cc).size().reset_index(name='Quantidade').sort_values(by='Quantidade', ascending=False).head(10)
            cc_volume[col_cc] = cc_volume[col_cc].astype(str)
            
            cores_barras = ['#3273a8'] + ['#ed8034'] * (len(cc_volume) - 1)
            cc_volume = cc_volume.sort_values(by='Quantidade', ascending=True)
            cores_barras = cores_barras[::-1]

            fig1 = go.Figure(go.Bar(
                x=cc_volume['Quantidade'],
                y=cc_volume[col_cc],
                orientation='h',
                text=cc_volume['Quantidade'],
                textposition='outside',
                textfont=dict(size=12, color='#1f2937', family='Arial Black'),
                marker_color=cores_barras
            ))
            
            fig1.update_layout(
                xaxis_title="Qtd. Itens", 
                yaxis_title="Centro de Custo",
                xaxis_title_font=dict(size=12, family='Arial Black'),
                yaxis_title_font=dict(size=12, family='Arial Black'),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=5, r=20, t=10, b=10),
                height=350,
                xaxis=dict(showgrid=True, gridcolor='#e2e8f0', tickfont=dict(size=11)),
                yaxis=dict(type='category', tickfont=dict(size=11, family='Arial Black'))
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col_g2:
            st.markdown('<div class="section-header">TOP 10 CC (QTD. REQUISIÇÕES)</div>', unsafe_allow_html=True)
            
            # Agrupamento por Requisições únicas (Contagem distinta de SCs por Centro de Custo)
            cc_scs = unique_scs.groupby(col_cc)[col_sc].nunique().reset_index(name='Qtd_SCs').sort_values(by='Qtd_SCs', ascending=False).head(10)
            cc_scs[col_cc] = cc_scs[col_cc].astype(str)
            
            cores_barras_sc = ['#2b6cb0'] + ['#319795'] * (len(cc_scs) - 1)
            cc_scs = cc_scs.sort_values(by='Qtd_SCs', ascending=True)
            cores_barras_sc = cores_barras_sc[::-1]

            fig2 = go.Figure(go.Bar(
                x=cc_scs['Qtd_SCs'],
                y=cc_scs[col_cc],
                orientation='h',
                text=cc_scs['Qtd_SCs'],
                textposition='outside',
                textfont=dict(size=12, color='#1f2937', family='Arial Black'),
                marker_color=cores_barras_sc
            ))
            
            fig2.update_layout(
                xaxis_title="Qtd. Requisições (SCs)", 
                yaxis_title="Centro de Custo",
                xaxis_title_font=dict(size=12, family='Arial Black'),
                yaxis_title_font=dict(size=12, family='Arial Black'),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=5, r=20, t=10, b=10),
                height=350,
                xaxis=dict(showgrid=True, gridcolor='#e2e8f0', tickfont=dict(size=11)),
                yaxis=dict(type='category', tickfont=dict(size=11, family='Arial Black'))
            )
            st.plotly_chart(fig2, use_container_width=True)

        with col_tabela:
            st.markdown('<div class="section-header">ITENS CRÍTICOS (MAIORES SLAS)</div>', unsafe_allow_html=True)
            
            top_critical = criticos_df.sort_values(by='Days', ascending=False)[[col_sc, col_cc, 'Days']].head(10)
            top_critical.columns = ['Nº SC', 'C. CUSTO', 'ATRASO']
            top_critical['Nº SC'] = top_critical['Nº SC'].astype(str)
            top_critical['C. CUSTO'] = top_critical['C. CUSTO'].astype(str)
            top_critical['ATRASO'] = top_critical['ATRASO'].astype(str) + " DIAS 🔥"

            st.markdown("""
                <style>
                dataframe, th, td {
                    font-size: 0.95rem !important;
                }
                </style>
            """, unsafe_allow_html=True)

            st.dataframe(
                top_critical, 
                use_container_width=True,
                height=350,
                hide_index=True
            )

        st.markdown("""
        <hr style='margin: 15px 0px 8px 0px;'>
        <div style="font-size: 1.05rem; color: #4a5568; display: flex; justify-content: space-between; font-weight: 700;">
            <span><b style="color: #e53e3e;">→ Alerta Crítico:</b> Backlog com inércia superior a 20 dias</span>
            <span><b style="color: #3273a8;">→ Top 10 CC:</b> Comparativo de volume de itens vs. quantidade de requisições</span>
            <span><b style="color: #388e3c;">Metodologia:</b> Contagem consolidada de SCs e itens do Protheus</span>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"⚠️ Erro analítico no processamento do arquivo. Detalhe técnico: {e}")
else:
    st.info("💡 Clique em **⚙️ Abrir / Fechar Configurações** no topo para anexar o arquivo de pendências e selecionar a data base.")
