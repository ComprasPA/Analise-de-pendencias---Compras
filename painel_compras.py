import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# 1. CONFIGURAÇÃO DA PÁGINA (Wide com barra de rolagem habilitada)
st.set_page_config(layout="wide", page_title="Panorama Executivo de Suprimentos")

# ==========================================
# CSS CUSTOMIZADO (Visual Executivo Completo)
# ==========================================
st.markdown("""
    <style>
    header[data-testid="stHeader"], [data-testid="stDecoration"], .viewerBadge_container__1QSob, [data-testid="manage-app-button"], #MainMenu, footer {
        visibility: hidden;
        display: none !important;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
        max-width: 100% !important;
    }
    .header-box {
        background-color: #1f3b58;
        color: white;
        padding: 12px 20px;
        border-radius: 4px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .header-title {
        font-size: 1.4rem;
        font-weight: bold;
    }
    .header-sub {
        font-size: 1.1rem;
    }
    .resumo-bar {
        background-color: #2b4c7e;
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 1rem;
        padding: 6px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 15px;
        border-radius: 2px;
    }
    .section-header {
        background-color: #1f3b58;
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 1rem;
        padding: 6px;
        text-transform: uppercase;
        border-radius: 2px;
        margin-bottom: 8px;
    }
    .gauge-footer {
        text-align: center;
        color: #1e293b;
        font-size: 1.05rem;
        font-weight: 800;
        margin-top: 5px;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.15);
    }
    .stDataFrame td, .stDataFrame th {
        font-size: 1.05rem !important;
        font-weight: 800 !important;
        padding: 4px 6px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# PAINEL DE CONFIGURAÇÕES
# ==========================================
st.markdown("### ⚙️ Painel Executivo de Suprimentos - Configurações")
col_up1, col_up2 = st.columns([3, 1])
with col_up1:
    uploaded_file = st.file_uploader("Faça o upload do arquivo de pendências (.xlsx / .csv)", type=["xlsx", "xls", "csv"])
with col_up2:
    data_base = st.date_input("Data base para cálculo de SLA:", datetime.date.today())

st.markdown("---")

# ==========================================
# MAPEAMENTO DOS COMPRADORES POR CENTRO DE CUSTO
# ==========================================
MAPA_COMPRADORES = {
    # Ednilson (Comp 01)
    '1225': 'Ednilson', '1235': 'Ednilson', '1244': 'Ednilson', '1241': 'Ednilson', '1236': 'Ednilson',
    # Dayana (Comp 02)
    '1238': 'Dayana', '1243': 'Dayana', '1217': 'Dayana', '1237': 'Dayana',
    # Luiz (Comp 03)
    '1223': 'Luiz', '1240': 'Luiz', '9001': 'Luiz', '2003': 'Luiz', '2002': 'Luiz', '2001': 'Luiz',
    '3003': 'Luiz', '2010': 'Luiz', '3007': 'Luiz', '3010': 'Luiz', '3000': 'Luiz', '3002': 'Luiz',
    '3006': 'Luiz', '1239': 'Luiz', '3013': 'Luiz', '3024': 'Luiz'
}

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

        # Tratamento do Centro de Custo para String Limpa (remove decimais .0 e espaços)
        df['CC_clean'] = df[col_cc].astype(str).str.split('.').str[0].str.strip()
        
        # Mapeamento do Comprador
        df['Comprador_Resp'] = df['CC_clean'].map(MAPA_COMPRADORES).fillna('Não Mapeado / Outros')
        
        # Status Simplificado (Atendidas vs Pendentes)
        df['Status_Simplificado'] = df[col_status].apply(
            lambda x: 'Atendidas' if str(x).strip().upper() == 'FINALIZADO' else 'Pendentes'
        )

        # Base para gráficos de Backlog (Sem as Finalizadas)
        df_aberto = df[df['Status_Simplificado'] == 'Pendentes'].copy()
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
                number = {'suffix': sufixo, 'font': {'size': 32, 'color': '#1f3b58', 'family': 'Arial Black'}},
                title = {'text': titulo, 'font': {'size': 15, 'color': '#111827', 'family': 'Arial Black'}},
                gauge = {
                    'axis': {'range': [None, max_val], 'tickwidth': 1, 'tickcolor': "#475569", 'tickfont': {'size': 12, 'family': 'Arial Black'}},
                    'bar': {'color': cor_barra},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 0,
                    'steps': [
                        {'range': [0, max_val * 0.6], 'color': '#f1f5f9'},
                        {'range': [max_val * 0.6, max_val], 'color': '#e2e8f0'}
                    ],
                }
            ))
            fig.update_layout(height=160, margin=dict(l=15, r=15, t=35, b=5), paper_bgcolor='rgba(0,0,0,0)')
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

        st.markdown("<br>", unsafe_allow_html=True)

        # ==========================================
        # PASSO 2: PRIMEIRA LINHA (TOP 10 CC)
        # ==========================================
        st.markdown("---")
        row1_c1, row1_c2 = st.columns(2)

        with row1_c1:
            st.markdown('<div class="section-header">TOP 10 CENTROS DE CUSTO (VOLUME DE ITENS)</div>', unsafe_allow_html=True)
            cc_volume = df_aberto.groupby(col_cc).size().reset_index(name='Quantidade').sort_values(by='Quantidade', ascending=False).head(10)
            cc_volume[col_cc] = cc_volume[col_cc].astype(str)
            
            cores_barras = ['#3273a8'] + ['#ed8034'] * (len(cc_volume) - 1)
            fig_cc_it = go.Figure(go.Bar(
                x=cc_volume.sort_values(by='Quantidade', ascending=True)['Quantidade'],
                y=cc_volume.sort_values(by='Quantidade', ascending=True)[col_cc],
                orientation='h',
                text=cc_volume.sort_values(by='Quantidade', ascending=True)['Quantidade'],
                textposition='outside',
                textfont=dict(size=12, color='#1f2937', family='Arial Black'),
                marker_color=cores_barras[::-1]
            ))
            fig_cc_it.update_layout(
                xaxis_title="Qtd. Itens", yaxis_title="Centro de Custo",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=5, r=20, t=10, b=10), height=350,
                xaxis=dict(showgrid=True, gridcolor='#e2e8f0'), yaxis=dict(type='category', tickfont=dict(family='Arial Black'))
            )
            st.plotly_chart(fig_cc_it, use_container_width=True)

        with row1_c2:
            st.markdown('<div class="section-header">TOP 10 CENTROS DE CUSTO (QTD. REQUISIÇÕES / SCs)</div>', unsafe_allow_html=True)
            cc_scs = unique_scs_aberto.groupby(col_cc)[col_sc].nunique().reset_index(name='Qtd_SCs').sort_values(by='Qtd_SCs', ascending=False).head(10)
            cc_scs[col_cc] = cc_scs[col_cc].astype(str)
            
            cores_barras_sc = ['#2b6cb0'] + ['#319795'] * (len(cc_scs) - 1)
            fig_cc_sc = go.Figure(go.Bar(
                x=cc_scs.sort_values(by='Qtd_SCs', ascending=True)['Qtd_SCs'],
                y=cc_scs.sort_values(by='Qtd_SCs', ascending=True)[col_cc],
                orientation='h',
                text=cc_scs.sort_values(by='Qtd_SCs', ascending=True)['Qtd_SCs'],
                textposition='outside',
                textfont=dict(size=12, color='#1f2937', family='Arial Black'),
                marker_color=cores_barras_sc[::-1]
            ))
            fig_cc_sc.update_layout(
                xaxis_title="Qtd. Requisições (SCs)", yaxis_title="Centro de Custo",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=5, r=20, t=10, b=10), height=350,
                xaxis=dict(showgrid=True, gridcolor='#e2e8f0'), yaxis=dict(type='category', tickfont=dict(family='Arial Black'))
            )
            st.plotly_chart(fig_cc_sc, use_container_width=True)

        # ==========================================
        # PASSO 3: SEGUNDA LINHA (STATUS SLA E ITENS CRÍTICOS)
        # ==========================================
        st.markdown("---")
        row2_c1, row2_c2 = st.columns(2)

        with row2_c1:
            st.markdown('<div class="section-header">CONSOLIDAÇÃO GERAL: STATUS DE PRAZO (SLA)</div>', unsafe_allow_html=True)
            if col_status:
                status_count = df_aberto.groupby(col_status).size().reset_index(name='Quantidade').sort_values(by='Quantidade', ascending=False)
                status_count[col_status] = status_count[col_status].astype(str)
                status_count = status_count.sort_values(by='Quantidade', ascending=True)
                
                cores_status = ['#e53e3e' if 'FORA' in s.upper() else '#d97706' if 'ATENÇÃO' in s.upper() else '#388e3c' for s in status_count[col_status]]
                fig_status = go.Figure(go.Bar(
                    x=status_count['Quantidade'], y=status_count[col_status], orientation='h',
                    text=status_count['Quantidade'], textposition='outside', textfont=dict(size=12, family='Arial Black'), marker_color=cores_status
                ))
                fig_status.update_layout(
                    xaxis_title="Qtd. Solicitações", yaxis_title="Status",
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=350,
                    margin=dict(l=5, r=20, t=10, b=10), xaxis=dict(showgrid=True, gridcolor='#e2e8f0'), yaxis=dict(type='category', tickfont=dict(family='Arial Black'))
                )
                st.plotly_chart(fig_status, use_container_width=True)

        with row2_c2:
            st.markdown('<div class="section-header">ITENS CRÍTICOS (MAIORES SLAS EM ATRASO)</div>', unsafe_allow_html=True)
            top_critical = criticos_df.sort_values(by='Days', ascending=False)[[col_sc, col_cc, 'Days']].head(10)
            top_critical.columns = ['Nº SC', 'C. CUSTO', 'ATRASO']
            top_critical['ATRASO'] = top_critical['ATRASO'].astype(str) + " DIAS 🔥"
            st.dataframe(top_critical, use_container_width=True, height=350, hide_index=True)

        # ==========================================
        # PASSO 4: TERCEIRA LINHA (DESEMPENHO COMPRADORES & CRITICIDADE FILTRADA)
        # ==========================================
        st.markdown("---")
        row3_c1, row3_c2 = st.columns(2)

        with row3_c1:
            st.markdown('<div class="section-header">DESEMPENHO POR COMPRADOR (ATENDIDAS VS PENDENTES)</div>', unsafe_allow_html=True)
            
            # Base total de compradores nomeados (ignorando não mapeados para o visual ficar limpo)
            df_compradores = df[df['Comprador_Resp'] != 'Não Mapeado / Outros'].copy()
            
            if not df_compradores.empty:
                comp_stats = df_compradores.groupby(['Comprador_Resp', 'Status_Simplificado']).size().reset_index(name='Quantidade')
                fig_comp = go.Figure()
                
                color_status_map = {'Atendidas': '#2b6cb0', 'Pendentes': '#ed8034'}
                for status_val in ['Atendidas', 'Pendentes']:
                    df_sub = comp_stats[comp_stats['Status_Simplificado'] == status_val]
                    if not df_sub.empty:
                        fig_comp.add_trace(go.Bar(
                            x=df_sub['Comprador_Resp'], y=df_sub['Quantidade'], name=status_val,
                            marker_color=color_status_map.get(status_val),
                            text=df_sub['Quantidade'], textposition='auto', textfont=dict(size=12, color='white', family='Arial Black')
                        ))
                
                fig_comp.update_layout(
                    barmode='group', xaxis_title="Compradores", yaxis_title="Volume Total",
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=400,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(family='Arial Black')),
                    xaxis=dict(showgrid=False, tickfont=dict(size=12, family='Arial Black')), yaxis=dict(showgrid=True, gridcolor='#e2e8f0')
                )
                st.plotly_chart(fig_comp, use_container_width=True)
            else:
                st.info("Nenhum item localizado com os centros de custo dos compradores mapeados.")

        with row3_c2:
            st.markdown('<div class="section-header">CRITICIDADE VS STATUS (ROTINEIRA E EMERGENCIAL)</div>', unsafe_allow_html=True)
            if col_criticidade and col_status:
                # Filtrar apenas Rotineira e Emergencial
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
                                text=df_sub['Quantidade'], textposition='auto', textfont=dict(size=12, color='white', family='Arial Black')
                            ))
                    
                    fig_crit_stat.update_layout(
                        barmode='group', xaxis_title="Classificação", yaxis_title="Qtd. Solicitações em Aberto",
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=400,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(family='Arial Black')),
                        xaxis=dict(showgrid=False, tickfont=dict(size=12, family='Arial Black')), yaxis=dict(showgrid=True, gridcolor='#e2e8f0')
                    )
                    st.plotly_chart(fig_crit_stat, use_container_width=True)
                else:
                    st.info("Nenhuma solicitação Rotineira ou Emergencial em aberto.")

    except Exception as e:
        st.error(f"⚠️ Erro analítico no processamento. Detalhe técnico: {e}")
else:
    st.info("💡 Faça o upload do arquivo de pendências (`.xlsx` ou `.csv`) no topo da página para carregar o panorama executivo.")
