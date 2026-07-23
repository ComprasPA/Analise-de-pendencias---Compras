import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# 1. CONFIGURAÇÃO DA PÁGINA (Wide)
st.set_page_config(layout="wide", page_title="Panorama Executivo de Suprimentos")

# ==========================================
# CSS CUSTOMIZADO (Visual Executivo e Responsivo)
# ==========================================
st.markdown("""
    <style>
    header[data-testid="stHeader"], [data-testid="stDecoration"], .viewerBadge_container__1QSob, [data-testid="manage-app-button"], #MainMenu, footer {
        visibility: hidden;
        display: none !important;
    }
    .block-container {
        padding-top: 0.6rem;
        padding-bottom: 0.6rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100% !important;
    }
    .header-box {
        background-color: #1f3b58;
        color: white;
        padding: 8px 16px;
        border-radius: 4px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    .header-title {
        font-size: 1.2rem;
        font-weight: bold;
    }
    .header-sub {
        font-size: 0.95rem;
    }
    .resumo-bar {
        background-color: #2b4c7e;
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 0.85rem;
        padding: 4px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
        border-radius: 2px;
    }
    .section-header {
        background-color: #1f3b58;
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 0.85rem;
        padding: 4px;
        text-transform: uppercase;
        border-radius: 2px;
        margin-bottom: 4px;
    }
    .gauge-footer {
        text-align: center;
        color: #1e293b;
        font-size: 0.9rem;
        font-weight: 800;
        margin-top: -2px;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.15);
    }
    .stDataFrame td, .stDataFrame th {
        font-size: 0.9rem !important;
        font-weight: 800 !important;
        padding: 2px 4px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# PAINEL DE CONFIGURAÇÕES (Sempre visível para upload)
# ==========================================
st.markdown("### ⚙️ Painel Executivo de Suprimentos - Configurações")
col_up1, col_up2 = st.columns([3, 1])
with col_up1:
    uploaded_file = st.file_uploader("Faça o upload do arquivo de pendências (.xlsx / .csv)", type=["xlsx", "xls", "csv"])
with col_up2:
    data_base = st.date_input("Data base para cálculo de SLA:", datetime.date.today())

st.markdown("---")

# ==========================================
# PROCESSAMENTO ANALÍTICO DE DADOS
# ==========================================
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8')
        else:
            xls = pd.ExcelFile(uploaded_file)
            sheet_name = 'Solicitações' if 'Solicitações' in xls.sheet_names else xls.sheet_names[0]
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
            
        df.columns = df.columns.astype(str).str.strip()

        col_status = 'STATUS' if 'STATUS' in df.columns else None
        col_criticidade = 'CRITICIDADE' if 'CRITICIDADE' in df.columns else None
        col_sc = 'Solicitação' if 'Solicitação' in df.columns else ('Cod SC. SCM' if 'Cod SC. SCM' in df.columns else None)
        col_cc = 'Centro de Custo' if 'Centro de Custo' in df.columns else None
        col_dt = 'DT Emissao' if 'DT Emissao' in df.columns else None

        if not col_sc or not col_cc or not col_dt:
            st.error(f"⚠️ Erro: Colunas essenciais não encontradas. Colunas disponíveis: {list(df.columns)}")
            st.stop()

        # Considerar apenas solicitações que NÃO estejam com status 'FINALIZADO'
        if col_status:
            df_aberto = df[df[col_status].astype(str).str.strip().str.upper() != 'FINALIZADO'].copy()
        else:
            df_aberto = df.copy()

        df_aberto = df_aberto.dropna(subset=[col_sc])
        df_aberto[col_sc] = df_aberto[col_sc].astype(str).str.split('.').str[0].str.zfill(6)

        hoje = pd.to_datetime(data_base)
        df_aberto[col_dt] = pd.to_datetime(df_aberto[col_dt], errors='coerce')
        df_aberto['Days'] = (hoje - df_aberto[col_dt]).dt.days

        total_linhas_aberto = len(df_aberto) 
        unique_scs_aberto = df_aberto.drop_duplicates(subset=[col_sc]).copy()
        total_sc_unicas_aberto = len(unique_scs_aberto)
        
        criticos_df = unique_scs_aberto[unique_scs_aberto['Days'] >= 20]
        backlog_critico = len(criticos_df)
        
        no_prazo = total_sc_unicas_aberto - backlog_critico
        taxa_atendimento_val = (no_prazo / total_sc_unicas_aberto * 100) if total_sc_unicas_aberto > 0 else 100

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
                number = {'suffix': sufixo, 'font': {'size': 24, 'color': '#1f3b58', 'family': 'Arial Black'}},
                title = {'text': titulo, 'font': {'size': 12, 'color': '#111827', 'family': 'Arial Black'}},
                gauge = {
                    'axis': {'range': [None, max_val], 'tickwidth': 1, 'tickcolor': "#475569", 'tickfont': {'size': 10, 'family': 'Arial Black'}},
                    'bar': {'color': cor_barra},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 0,
                    'steps': [
                        {'range': [0, max_val * 0.6], 'color': '#f1f5f9'},
                        {'range': [max_val * 0.6, max_val], 'color': '#e2e8f0'}
                    ],
                }
            ))
            fig.update_layout(height=110, margin=dict(l=10, r=10, t=25, b=0), paper_bgcolor='rgba(0,0,0,0)')
            return fig

        gauge_col1, gauge_col2, gauge_col3 = st.columns(3)

        with gauge_col1:
            max_sc = max(total_sc_unicas_aberto * 1.5, 10)
            fig1 = criar_gauge("TOTAL DE REQUISIÇÕES (ÚNICAS ABERTAS)", total_sc_unicas_aberto, max_sc, "#2b6cb0")
            st.plotly_chart(fig1, use_container_width=True)
            st.markdown(f"<div class='gauge-footer'>Volume Bruto: <b>{total_linhas_aberto} itens</b></div>", unsafe_allow_html=True)

        with gauge_col2:
            max_backlog = max(total_sc_unicas_aberto, 10)
            fig2 = criar_gauge("BACKLOG CRÍTICO (>=20 DIAS)", backlog_critico, max_backlog, "#e53e3e")
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown(f"<div class='gauge-footer' style='color: #e53e3e;'><b>{(backlog_critico/total_sc_unicas_aberto*100 if total_sc_unicas_aberto > 0 else 0):.1f}%</b> das SCs ativas</div>", unsafe_allow_html=True)

        with gauge_col3:
            fig3 = criar_gauge("TAXA DE ATENDIMENTO / SAÚDE", round(taxa_atendimento_val, 1), 100, "#388e3c", sufixo="%")
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown(f"<div class='gauge-footer' style='color: #388e3c;'>Dentro do SLA padrão (&lt;20 dias)</div>", unsafe_allow_html=True)

        # ==========================================
        # PASSO 2: RENDERIZAÇÃO PANORÂMICA (GRÁFICO STATUS SLA + TOP 10 CC + TABELA CRÍTICOS)
        # ==========================================
        st.markdown("<hr style='margin: 8px 0px;'>", unsafe_allow_html=True)
        
        col_g1, col_g2, col_tabela = st.columns([1, 1, 1.1])

        with col_g1:
            st.markdown('<div class="section-header">STATUS DE PRAZO (SLA) EM ABERTO</div>', unsafe_allow_html=True)
            
            if col_status:
                status_count = df_aberto.groupby(col_status).size().reset_index(name='Quantidade').sort_values(by='Quantidade', ascending=False)
                status_count[col_status] = status_count[col_status].astype(str)
                status_count = status_count.sort_values(by='Quantidade', ascending=True)
                
                cores_status = []
                for s in status_count[col_status]:
                    if 'FORA' in s.upper():
                        cores_status.append('#e53e3e')
                    elif 'ATENÇÃO' in s.upper():
                        cores_status.append('#d97706')
                    else:
                        cores_status.append('#388e3c')

                fig_status = go.Figure(go.Bar(
                    x=status_count['Quantidade'],
                    y=status_count[col_status],
                    orientation='h',
                    text=status_count['Quantidade'],
                    textposition='outside',
                    textfont=dict(size=10, color='#1f2937', family='Arial Black'),
                    marker_color=cores_status
                ))
                
                fig_status.update_layout(
                    xaxis_title="Qtd. Solicitações", 
                    yaxis_title="Status de Prazo",
                    xaxis_title_font=dict(size=10, family='Arial Black'),
                    yaxis_title_font=dict(size=10, family='Arial Black'),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=2, r=15, t=2, b=2),
                    height=200,
                    xaxis=dict(showgrid=True, gridcolor='#e2e8f0', tickfont=dict(size=9)),
                    yaxis=dict(type='category', tickfont=dict(size=9, family='Arial Black'))
                )
                st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.info("Coluna STATUS não encontrada.")

        with col_g2:
            st.markdown('<div class="section-header">TOP 10 CC (VOLUME DE ITENS)</div>', unsafe_allow_html=True)
            
            cc_volume = df_aberto.groupby(col_cc).size().reset_index(name='Quantidade').sort_values(by='Quantidade', ascending=False).head(10)
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
                textfont=dict(size=10, color='#1f2937', family='Arial Black'),
                marker_color=cores_barras
            ))
            
            fig1.update_layout(
                xaxis_title="Qtd. Itens", 
                yaxis_title="Centro de Custo",
                xaxis_title_font=dict(size=10, family='Arial Black'),
                yaxis_title_font=dict(size=10, family='Arial Black'),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=2, r=15, t=2, b=2),
                height=200,
                xaxis=dict(showgrid=True, gridcolor='#e2e8f0', tickfont=dict(size=9)),
                yaxis=dict(type='category', tickfont=dict(size=9, family='Arial Black'))
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col_tabela:
            st.markdown('<div class="section-header">ITENS CRÍTICOS (MAIORES SLAS)</div>', unsafe_allow_html=True)
            
            top_critical = criticos_df.sort_values(by='Days', ascending=False)[[col_sc, col_cc, 'Days']].head(10)
            top_critical.columns = ['Nº SC', 'C. CUSTO', 'ATRASO']
            top_critical['Nº SC'] = top_critical['Nº SC'].astype(str)
            top_critical['C. CUSTO'] = top_critical['C. CUSTO'].astype(str)
            top_critical['ATRASO'] = top_critical['ATRASO'].astype(str) + " DIAS 🔥"

            st.dataframe(
                top_critical, 
                use_container_width=True,
                height=200,
                hide_index=True
            )

        st.markdown("""
        <hr style='margin: 4px 0px;'>
        <div style="font-size: 0.85rem; color: #4a5568; display: flex; justify-content: space-between; font-weight: 700;">
            <span><b style="color: #e53e3e;">→ Alerta Crítico:</b> Backlog superior a 20 dias</span>
            <span><b style="color: #3273a8;">→ Status de Prazo:</b> Reflete regras de SLA (3d úteis emergencial / 15d rotineira)</span>
            <span><b style="color: #388e3c;">Metodologia:</b> Contagem Protheus (6 dígitos, exceto Finalizados)</span>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"⚠️ Erro analítico no processamento do arquivo. Detalhe técnico: {e}")
else:
    st.info("💡 Faça o upload do arquivo de pendências (`.xlsx` ou `.csv`) no topo da página para carregar o panorama executivo.")
