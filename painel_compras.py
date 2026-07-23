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
        font-size: 0.95rem;
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
        font-size: 1rem !important;
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
    '1225': 'Ednilson', '1235': 'Ednilson', '1244': 'Ednilson', '1241': 'Ednilson', '1236': 'Ednilson',
    '1238': 'Dayana', '1243': 'Dayana', '1217': 'Dayana', '1237': 'Dayana',
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

        # Tratamento Compradores
        df['CC_clean'] = df[col_cc].astype(str).str.split('.').str[0].str.strip()
        df['Comprador_Resp'] = df['CC_clean'].map(MAPA_COMPRADORES).fillna('Não Mapeado / Outros')
        
        def detalhar_status(x):
            x_str = str(x).strip().upper()
            if x_str == 'FINALIZADO': return 'Atendidas'
            elif 'FORA' in x_str: return 'Fora do Prazo'
            elif 'ATENÇÃO' in x_str: return 'Atenção'
            else: return 'No Prazo'
        
        if col_status:
            df['Status_Detalhado'] = df[col_status].apply(detalhar_status)
            df_aberto = df[df['Status_Detalhado'] != 'Atendidas'].copy()
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
                mode = "gauge+number", value = valor,
                number = {'suffix': sufixo, 'font': {'size': 32, 'color': '#1f3b58', 'family': 'Arial Black'}},
                title = {'text': titulo, 'font': {'size': 15, 'color': '#111827', 'family': 'Arial Black'}},
                gauge = {
                    'axis': {'range': [None, max_val], 'tickwidth': 1, 'tickcolor': "#475569", 'tickfont': {'size': 12, 'family': 'Arial Black'}},
                    'bar': {'color': cor_barra}, 'bgcolor': "rgba(0,0,0,0)", 'borderwidth': 0,
                    'steps': [{'range': [0, max_val * 0.6], 'color': '#f1f5f9'}, {'range': [max_val * 0.6, max_val], 'color': '#e2e8f0'}],
                }
            ))
            fig.update_layout(height=160, margin=dict(l=15, r=15, t=35, b=5), paper_bgcolor='rgba(0,0,0,0)')
            return fig

        gauge_col1, gauge_col2, gauge_col3 = st.columns(3)
        with gauge_col1:
            st.plotly_chart(criar_gauge("TOTAL DE REQUISIÇÕES (ÚNICAS ABERTAS)", total_sc_unicas_aberto, max(total_sc_unicas_aberto * 1.5, 10), "#2b6cb0"), use_container_width=True)
            st.markdown(f"<div class='gauge-footer'>Volume Bruto: <b>{total_linhas_aberto} itens</b></div>", unsafe_allow_html=True)
        with gauge_col2:
            st.plotly_chart(criar_gauge("BACKLOG CRÍTICO (>=20 DIAS)", backlog_critico, max(total_sc_unicas_aberto, 10), "#e53e3e"), use_container_width=True)
            st.markdown(f"<div class='gauge-footer' style='color: #e53e3e;'><b>{(backlog_critico/total_sc_unicas_aberto*100 if total_sc_unicas_aberto > 0 else 0):.1f}%</b> das SCs ativas</div>", unsafe_allow_html=True)
        with gauge_col3:
            st.plotly_chart(criar_gauge("TAXA DE ATENDIMENTO / SAÚDE", round(taxa_atendimento_val, 1), 100, "#388e3c", sufixo="%"), use_container_width=True)
            st.markdown(f"<div class='gauge-footer' style='color: #388e3c;'>Dentro do SLA padrão (&lt;20 dias)</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ==========================================
        # PASSO 2: CENTROS DE CUSTO & ITENS CRÍTICOS (3 COLUNAS)
        # ==========================================
        st.markdown("---")
        row2_c1, row2_c2, row2_c3 = st.columns([1, 1, 1.1])

        with row2_c1:
            st.markdown('<div class="section-header">TOP 10 CC (VOLUME DE ITENS)</div>', unsafe_allow_html=True)
            cc_volume = df_aberto.groupby(col_cc).size().reset_index(name='Quantidade').sort_values(by='Quantidade', ascending=False).head(10)
            cc_volume[col_cc] = cc_volume[col_cc].astype(str)
            
            cores_barras = ['#3273a8'] + ['#ed8034'] * (len(cc_volume) - 1)
            fig_cc_it = go.Figure(go.Bar(
                x=cc_volume.sort_values(by='Quantidade', ascending=True)['Quantidade'],
                y=cc_volume.sort_values(by='Quantidade', ascending=True)[col_cc],
                orientation='h', text=cc_volume.sort_values(by='Quantidade', ascending=True)['Quantidade'],
                textposition='outside', textfont=dict(size=11, color='#1f2937', family='Arial Black'), marker_color=cores_barras[::-1]
            ))
            fig_cc_it.update_layout(
                xaxis_title="Qtd. Itens", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=5, r=10, t=10, b=10), height=320, xaxis=dict(showgrid=True, gridcolor='#e2e8f0'), yaxis=dict(type='category', tickfont=dict(family='Arial Black', size=10))
            )
            st.plotly_chart(fig_cc_it, use_container_width=True)

        with row2_c2:
            st.markdown('<div class="section-header">TOP 10 CC (QTD. REQUISIÇÕES)</div>', unsafe_allow_html=True)
            cc_scs = unique_scs_aberto.groupby(col_cc)[col_sc].nunique().reset_index(name='Qtd_SCs').sort_values(by='Qtd_SCs', ascending=False).head(10)
            cc_scs[col_cc] = cc_scs[col_cc].astype(str)
            
            cores_barras_sc = ['#2b6cb0'] + ['#319795'] * (len(cc_scs) - 1)
            fig_cc_sc = go.Figure(go.Bar(
                x=cc_scs.sort_values(by='Qtd_SCs', ascending=True)['Qtd_SCs'],
                y=cc_scs.sort_values(by='Qtd_SCs', ascending=True)[col_cc],
                orientation='h', text=cc_scs.sort_values(by='Qtd_SCs', ascending=True)['Qtd_SCs'],
                textposition='outside', textfont=dict(size=11, color='#1f2937', family='Arial Black'), marker_color=cores_barras_sc[::-1]
            ))
            fig_cc_sc.update_layout(
                xaxis_title="Qtd. Requisições (SCs)", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=5, r=10, t=10, b=10), height=320, xaxis=dict(showgrid=True, gridcolor='#e2e8f0'), yaxis=dict(type='category', tickfont=dict(family='Arial Black', size=10))
            )
            st.plotly_chart(fig_cc_sc, use_container_width=True)

        with row2_c3:
            st.markdown('<div class="section-header">ITENS CRÍTICOS (MAIORES SLAS)</div>', unsafe_allow_html=True)
            top_critical = criticos_df.sort_values(by='Days', ascending=False)[[col_sc, col_cc, 'Days']].head(8)
            top_critical.columns = ['Nº SC', 'C. CUSTO', 'ATRASO']
            top_critical['ATRASO'] = top_critical['ATRASO'].astype(str) + " DIAS 🔥"
            st.dataframe(top_critical, use_container_width=True, height=320, hide_index=True)

        # ==========================================
        # PASSO 3: GERAL SLA & CRITICIDADE (2 COLUNAS)
        # ==========================================
        st.markdown("---")
        row3_c1, row3_c2 = st.columns(2)

        with row3_c1:
            # Título atualizado para refletir explicitamente que a contagem é de ITENS
            st.markdown('<div class="section-header">CONSOLIDAÇÃO GERAL: STATUS DE PRAZO (QTD. ITENS)</div>', unsafe_allow_html=True)
            if col_status:
                status_count = df_aberto.groupby(col_status).size().reset_index(name='Quantidade').sort_values(by='Quantidade', ascending=False)
                status_count[col_status] = status_count[col_status].astype(str)
                status_count = status_count.sort_values(by='Quantidade', ascending=True)
                
                cores_status = ['#e53e3e' if 'FORA' in s.upper() else '#d97706' if 'ATENÇÃO' in s.upper() else '#388e3c' for s in status_count[col_status]]
                fig_status = go.Figure(go.Bar(
                    x=status_count['Quantidade'], y=status_count[col_status], orientation='h',
                    text=status_count['Quantidade'], 
                    textposition='outside', 
                    textfont=dict(size=12, color='#1f2937', family='Arial Black'), # Sempre preto/escuro pois fica fora
                    marker_color=cores_status
                ))
                fig_status.update_layout(
                    xaxis_title="Qtd. Itens em Aberto", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=320,
                    margin=dict(l=5, r=20, t=10, b=10), xaxis=dict(showgrid=True, gridcolor='#e2e8f0'), yaxis=dict(type='category', tickfont=dict(family='Arial Black'))
                )
                st.plotly_chart(fig_status, use_container_width=True)

        with row3_c2:
            # Título atualizado para refletir explicitamente que a contagem é de ITENS
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
                                text=df_sub['Quantidade'], 
                                textposition='auto', 
                                textfont=dict(size=12, family='Arial Black'),
                                insidetextfont=dict(color='white'),       # Se couber dentro: Branco
                                outsidetextfont=dict(color='#1f2937')     # Se for ejetado para fora: Escuro
                            ))
                    fig_crit_stat.update_layout(
                        barmode='group', xaxis_title="", yaxis_title="Qtd. Itens em Aberto", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=320,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(family='Arial Black')),
                        xaxis=dict(showgrid=False, tickfont=dict(size=12, family='Arial Black')), yaxis=dict(showgrid=True, gridcolor='#e2e8f0')
                    )
                    st.plotly_chart(fig_crit_stat, use_container_width=True)

        # ==========================================
        # PASSO 4: DESEMPENHO POR COMPRADOR (PERCENTUAIS)
        # ==========================================
        st.markdown("---")
        st.markdown('<div class="section-header" style="background-color: #2b4c7e;">DESEMPENHO INDIVIDUAL POR COMPRADOR (% DOS ITENS EM ABERTO)</div>', unsafe_allow_html=True)
        
        row4_c1, row4_c2, row4_c3 = st.columns(3)
        compradores = ['Ednilson', 'Dayana', 'Luiz']
        colunas_st = [row4_c1, row4_c2, row4_c3]
        
        color_status_map = {'No Prazo': '#388e3c', 'Atenção': '#d97706', 'Fora do Prazo': '#e53e3e'}
        ordem_status_aberto = ['Fora do Prazo', 'Atenção', 'No Prazo']
        
        for comp, col_st in zip(compradores, colunas_st):
            with col_st:
                st.markdown(f'<div style="text-align: center; font-weight: bold; font-size: 1.15rem; margin-bottom: 5px; color: #1f3b58;">👤 {comp}</div>', unsafe_allow_html=True)
                
                df_comp_total = df[df['Comprador_Resp'] == comp].copy()
                
                if not df_comp_total.empty and 'Status_Detalhado' in df_comp_total.columns:
                    
                    qtd_atendidas = len(df_comp_total[df_comp_total['Status_Detalhado'] == 'Atendidas'])
                    df_comp_aberto = df_comp_total[df_comp_total['Status_Detalhado'] != 'Atendidas'].copy()
                    
                    if not df_comp_aberto.empty:
                        comp_stats = df_comp_aberto.groupby('Status_Detalhado').size().reset_index(name='Quantidade')
                        total_aberto = comp_stats['Quantidade'].sum()
                        comp_stats['Percentual'] = (comp_stats['Quantidade'] / total_aberto * 100).round(1)
                        
                        comp_stats['Status_Detalhado'] = pd.Categorical(comp_stats['Status_Detalhado'], categories=ordem_status_aberto, ordered=True)
                        comp_stats = comp_stats.sort_values('Status_Detalhado')
                        
                        cores = [color_status_map.get(s, '#718096') for s in comp_stats['Status_Detalhado']]
                        
                        fig_comp_ind = go.Figure(go.Bar(
                            x=comp_stats['Percentual'],
                            y=comp_stats['Status_Detalhado'],
                            orientation='h',
                            text=comp_stats['Percentual'].astype(str) + '%',
                            textposition='outside',
                            textfont=dict(size=12, color='#1f2937', family='Arial Black'), # Sempre escuro pois fica fora
                            marker_color=cores
                        ))
                        
                        fig_comp_ind.update_layout(
                            xaxis_title="Percentual (%) do Backlog Pendente", yaxis_title="",
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=250,
                            margin=dict(l=5, r=30, t=10, b=10),
                            xaxis=dict(showgrid=True, gridcolor='#e2e8f0', range=[0, max(comp_stats['Percentual'].max() * 1.25, 100)]), 
                            yaxis=dict(type='category', tickfont=dict(family='Arial Black', size=11))
                        )
                        st.plotly_chart(fig_comp_ind, use_container_width=True)
                    else:
                        st.info(f"Fila limpa! Nenhum item pendente para {comp}.")
                    
                    st.markdown(f"""
                    <div style='text-align: center; font-size: 0.95rem; color: #2b6cb0; font-weight: bold; background-color: #f1f5f9; padding: 6px; border-radius: 4px; margin-top: -15px;'>
                        ✅ {qtd_atendidas} Itens Atendidos (Finalizados)
                    </div>
                    """, unsafe_allow_html=True)
                    
                else:
                    st.info(f"Sem dados mapeados para {comp}.")

        st.markdown("""
        <hr style='margin: 15px 0px 8px 0px;'>
        <div style="font-size: 1.05rem; color: #4a5568; display: flex; justify-content: space-between; font-weight: 700;">
            <span><b style="color: #2b4c7e;">→ Performance:</b> Gráficos percentuais calculados exclusivamente sobre o backlog em aberto.</span>
            <span><b style="color: #388e3c;">Metodologia:</b> Status mapeados diretamente da base Protheus Parente Andrade.</span>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"⚠️ Erro analítico no processamento. Detalhe técnico: {e}")
else:
    st.info("💡 Faça o upload do arquivo de pendências (`.xlsx` ou `.csv`) no topo da página para carregar o panorama executivo.")
