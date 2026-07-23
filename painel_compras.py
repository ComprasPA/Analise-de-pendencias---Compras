import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go
import os

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
        font-size: 1.05rem;
        font-weight: 800;
        margin-top: -5px;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.10);
    }
    .stDataFrame td, .stDataFrame th {
        font-size: 1rem !important;
        font-weight: 800 !important;
        padding: 4px 6px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# PAINEL DE CONFIGURAÇÕES (RETRÁTIL)
# ==========================================
with st.expander("⚙️ Abrir / Fechar Configurações (Upload de Arquivo e Data Base)", expanded=False):
    col_up1, col_up2 = st.columns([3, 1])
    with col_up1:
        uploaded_file = st.file_uploader("Faça o upload do arquivo de pendências (.xlsx / .csv) para atualizar a base", type=["xlsx", "xls", "csv"])
    with col_up2:
        data_base = st.date_input("Data base para cálculo de SLA:", datetime.date.today())

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
df = None

# 1. Se o usuário acabou de fazer um upload
if uploaded_file is not None:
    try:
        # Salva o arquivo fisicamente no servidor para os próximos acessos
        with open(ARQUIVO_MEMORIA, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("✅ Base atualizada com sucesso por Silvio Silveira! Esta base agora é a padrão para todos os usuários.")
        
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8')
        else:
            xls = pd.ExcelFile(uploaded_file)
            sheet_name = 'Solicitações' if 'Solicitações' in xls.sheet_names else xls.sheet_names[0]
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo enviado: {e}")

# 2. Se não tem upload agora, busca o arquivo salvo no servidor
elif os.path.exists(ARQUIVO_MEMORIA):
    try:
        xls = pd.ExcelFile(ARQUIVO_MEMORIA)
        sheet_name = 'Solicitações' if 'Solicitações' in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(ARQUIVO_MEMORIA, sheet_name=sheet_name)
    except Exception as e:
        st.error(f"Erro ao ler a base salva no servidor: {e}")

# 3. Executa a construção do painel apenas se o df foi carregado
if df is not None:
    try:
        df.columns = df.columns.astype(str).str.strip()

        col_status = 'STATUS' if 'STATUS' in df.columns else None
        col_criticidade = 'CRITICIDADE' if 'CRITICIDADE' in df.columns else None
        col_sc = 'Solicitação' if 'Solicitação' in df.columns else ('Cod SC. SCM' if 'Cod SC. SCM' in df.columns else None)
        col_cc = 'Centro de Custo' if 'Centro de Custo' in df.columns else None
        col_dt = 'DT Emissao' if 'DT Emissao' in df.columns else None

        if not col_sc or not col_cc or not col_dt:
            st.error(f"⚠️ Erro: Colunas essenciais não encontradas. Colunas disponíveis: {list(df.columns)}")
            st.stop()

        # Converte a data para lidar com a regra do Luiz
        if col_dt:
            df[col_dt] = pd.to_datetime(df[col_dt], errors='coerce')

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
        df_aberto['Days'] = (hoje - df_aberto[col_dt]).dt.days

        total_linhas_aberto = len(df_aberto) 
        unique_scs_aberto = df_aberto.drop_duplicates(subset=[col_sc]).copy()
        total_sc_unicas_aberto = len(unique_scs_aberto)
        
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
        # PASSO 1: QUADRANTE DE VOLUMETRIA E VELOCÍMETROS GERAIS
        # ==========================================
        st.markdown(f"""
        <div class="header-box">
            <span class="header-title">PANORAMA DE REQUISIÇÕES PENDENTES DE COMPRA (EM ABERTO)</span>
            <span class="header-sub">DADOS CONSOLIDADOS | {hoje.strftime("%d/%m/%Y")}</span>
        </div>
        <div class="resumo-bar">DIAGNÓSTICO E VALIDAÇÃO ESTRATÉGICA (VOLUMETRIA, STATUS E CRITICIDADE)</div>
        """, unsafe_allow_html=True)

        def criar_gauge(titulo, valor, max_val, cor_barra):
            fig = go.Figure(go.Indicator(
                mode = "gauge+number", value = valor,
                number = {'font': {'size': 24, 'color': '#1f3b58', 'family': 'Arial Black'}},
                title = {'text': titulo, 'font': {'size': 11, 'color': '#111827', 'family': 'Arial Black'}},
                gauge = {
                    'axis': {'range': [None, max_val], 'tickwidth': 1, 'tickcolor': "#475569", 'tickfont': {'size': 9, 'family': 'Arial Black'}},
                    'bar': {'color': cor_barra}, 'bgcolor': "rgba(0,0,0,0)", 'borderwidth': 0,
                    'steps': [{'range': [0, max_val * 0.6], 'color': '#f1f5f9'}, {'range': [max_val * 0.6, max_val], 'color': '#e2e8f0'}],
                }
            ))
            fig.update_layout(height=140, margin=dict(l=10, r=10, t=30, b=5), paper_bgcolor='rgba(0,0,0,0)')
            return fig

        row1_c1, row1_c2, row1_c3, row1_c4, row1_c5, row1_c6 = st.columns([1.5, 1, 1, 1, 1, 1])

        with row1_c1:
            st.markdown(f"""
            <div style="background-color: white; border: 1px solid #cbd5e1; border-radius: 4px; padding: 10px; text-align: center; height: 160px; display: flex; flex-direction: column; justify-content: center;">
                <div style="color: #1f3b58; font-size: 1rem; font-family: 'Arial Black'; margin-bottom: 5px;">VOLUMETRIA EM ABERTO</div>
                <div style="font-size: 2rem; font-weight: bold; color: #2b6cb0; line-height: 1;">{total_sc_unicas_aberto}</div>
                <div style="font-size: 0.75rem; color: #475569; font-weight: bold; text-transform: uppercase; margin-bottom: 5px;">Solicitações (SCs)</div>
                <div style="border-top: 1px dashed #cbd5e1; margin: 5px 0;"></div>
                <div style="font-size: 2rem; font-weight: bold; color: #ed8034; line-height: 1;">{total_linhas_aberto}</div>
                <div style="font-size: 0.75rem; color: #475569; font-weight: bold; text-transform: uppercase;">Total de Itens</div>
            </div>
            """, unsafe_allow_html=True)

        def render_gauge(col, titulo, valor, max_val, cor):
            with col:
                st.plotly_chart(criar_gauge(titulo, valor, max_val, cor), use_container_width=True)
                perc = (valor / max_val * 100) if max_val > 0 else 0
                st.markdown(f"<div class='gauge-footer' style='color: {cor};'>{perc:.1f}%</div>", unsafe_allow_html=True)

        render_gauge(row1_c2, "NO PRAZO", qtd_no_prazo, total_linhas_aberto, "#388e3c")
        render_gauge(row1_c3, "ATENÇÃO", qtd_atencao, total_linhas_aberto, "#d97706")
        render_gauge(row1_c4, "FORA DO PRAZO", qtd_fora, total_linhas_aberto, "#e53e3e")
        render_gauge(row1_c5, "ROTINEIRA", qtd_rot, total_linhas_aberto, "#2b6cb0")
        render_gauge(row1_c6, "EMERGENCIAL", qtd_emg, total_linhas_aberto, "#805ad5")

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
            st.markdown('<div class="section-header">CONSOLIDAÇÃO GERAL: STATUS DE PRAZO (QTD. ITENS)</div>', unsafe_allow_html=True)
            if col_status:
                status_count = df_aberto.groupby(col_status).size().reset_index(name='Quantidade').sort_values(by='Quantidade', ascending=False)
                status_count[col_status] = status_count[col_status].astype(str)
                status_count = status_count.sort_values(by='Quantidade', ascending=True)
                
                cores_status = ['#e53e3e' if 'FORA' in s.upper() else '#d97706' if 'ATENÇÃO' in s.upper() else '#388e3c' for s in status_count[col_status]]
                fig_status = go.Figure(go.Bar(
                    x=status_count['Quantidade'], y=status_count[col_status], orientation='h',
                    text=status_count['Quantidade'], textposition='outside', 
                    textfont=dict(size=12, color='#1f2937', family='Arial Black'), 
                    marker_color=cores_status
                ))
                fig_status.update_layout(
                    xaxis_title="Qtd. Itens em Aberto", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=320,
                    margin=dict(l=5, r=20, t=10, b=10), xaxis=dict(showgrid=True, gridcolor='#e2e8f0'), yaxis=dict(type='category', tickfont=dict(family='Arial Black'))
                )
                st.plotly_chart(fig_status, use_container_width=True)

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
                                textfont=dict(size=12, family='Arial Black'),
                                insidetextfont=dict(color='white'),       
                                outsidetextfont=dict(color='#1f2937')     
                            ))
                    fig_crit_stat.update_layout(
                        barmode='group', xaxis_title="", yaxis_title="Qtd. Itens em Aberto", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=320,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(family='Arial Black')),
                        xaxis=dict(showgrid=False, tickfont=dict(size=12, family='Arial Black')), yaxis=dict(showgrid=True, gridcolor='#e2e8f0')
                    )
                    st.plotly_chart(fig_crit_stat, use_container_width=True)

        # ==========================================
        # PASSO 4: DESEMPENHO POR COMPRADOR (RENDIMENTO + BACKLOG PENDENTE)
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
                st.markdown(f'<div style="text-align: center; font-weight: bold; font-size: 1.15rem; margin-bottom: 2px; color: #1f3b58;">👤 {comp}</div>', unsafe_allow_html=True)
                
                # Base total do comprador (Finalizadas + Pendentes)
                df_comp_total = df[df['Comprador_Resp'] == comp].copy()
                
                # ------ REGRA DE EXCEÇÃO: LUIZ APENAS A PARTIR DE 06/07/2026 ------
                if comp == 'Luiz' and col_dt in df_comp_total.columns:
                    st.markdown("<div style='text-align: center; font-size: 0.75rem; font-weight: bold; color: #e53e3e; margin-bottom: 8px;'>*(Análise iniciada em 06/07/2026)</div>", unsafe_allow_html=True)
                    df_comp_total = df_comp_total[df_comp_total[col_dt] >= pd.to_datetime('2026-07-06')]
                else:
                    st.markdown("<div style='text-align: center; font-size: 0.75rem; color: transparent; margin-bottom: 8px;'>.</div>", unsafe_allow_html=True)
                
                if not df_comp_total.empty and 'Status_Detalhado' in df_comp_total.columns:
                    
                    total_emitidas = len(df_comp_total)
                    qtd_atendidas = len(df_comp_total[df_comp_total['Status_Detalhado'] == 'Atendidas'])
                    taxa_rendimento_comp = (qtd_atendidas / total_emitidas * 100) if total_emitidas > 0 else 0
                    
                    # ----- VELOCÍMETRO DE RENDIMENTO INDIVIDUAL -----
                    cor_gauge_comp = '#388e3c' if taxa_rendimento_comp >= 75 else ('#d97706' if taxa_rendimento_comp >= 50 else '#e53e3e')
                    
                    fig_gauge = go.Figure(go.Indicator(
                        mode = "gauge+number", value = taxa_rendimento_comp,
                        number = {'suffix': "%", 'font': {'size': 20, 'color': '#1f3b58', 'family': 'Arial Black'}},
                        title = {'text': "RENDIMENTO (ATENDIDAS / TOTAL)", 'font': {'size': 10, 'color': '#111827', 'family': 'Arial Black'}},
                        gauge = {
                            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#475569", 'tickfont': {'size': 9, 'family': 'Arial Black'}},
                            'bar': {'color': cor_gauge_comp}, 'bgcolor': "rgba(0,0,0,0)", 'borderwidth': 0,
                            'steps': [{'range': [0, 60], 'color': '#f1f5f9'}, {'range': [60, 100], 'color': '#e2e8f0'}],
                        }
                    ))
                    fig_gauge.update_layout(height=130, margin=dict(l=10, r=10, t=20, b=5), paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_gauge, use_container_width=True)

                    # ----- GRÁFICO DE BARRAS PERCENTUAIS DO BACKLOG PENDENTE -----
                    df_comp_aberto = df_comp_total[df_comp_total['Status_Detalhado'] != 'Atendidas'].copy()
                    
                    if not df_comp_aberto.empty:
                        comp_stats = df_comp_aberto.groupby('Status_Detalhado').size().reset_index(name='Quantidade')
                        total_aberto = comp_stats['Quantidade'].sum()
                        comp_stats['Percentual'] = (comp_stats['Quantidade'] / total_aberto * 100).round(1)
                        
                        comp_stats['Status_Detalhado'] = pd.Categorical(comp_stats['Status_Detalhado'], categories=ordem_status_aberto, ordered=True)
                        comp_stats = comp_stats.sort_values('Status_Detalhado')
                        
                        cores = [color_status_map.get(s, '#718096') for s in comp_stats['Status_Detalhado']]
                        
                        # Combinando Quantidade e Percentual na mesma Label
                        comp_stats['Texto_Label'] = comp_stats.apply(lambda row: f"{int(row['Quantidade'])} ({row['Percentual']}%)", axis=1)
                        
                        fig_comp_ind = go.Figure(go.Bar(
                            x=comp_stats['Percentual'],
                            y=comp_stats['Status_Detalhado'],
                            orientation='h',
                            text=comp_stats['Texto_Label'],
                            textposition='outside',
                            textfont=dict(size=12, color='#1f2937', family='Arial Black'), 
                            marker_color=cores
                        ))
                        
                        fig_comp_ind.update_layout(
                            xaxis_title="% do Backlog Restante", yaxis_title="",
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=150,
                            margin=dict(l=5, r=30, t=0, b=10),
                            xaxis=dict(showgrid=True, gridcolor='#e2e8f0', range=[0, max(comp_stats['Percentual'].max() * 1.35, 100)], tickfont=dict(size=9)), 
                            yaxis=dict(type='category', tickfont=dict(family='Arial Black', size=11))
                        )
                        st.plotly_chart(fig_comp_ind, use_container_width=True)
                    else:
                        st.info(f"Fila limpa! Nenhum item pendente para {comp}.")
                    
                    st.markdown(f"""
                    <div style='text-align: center; font-size: 0.95rem; color: #2b6cb0; font-weight: bold; background-color: #f1f5f9; padding: 6px; border-radius: 4px; margin-top: 5px;'>
                        ✅ {qtd_atendidas} de {total_emitidas} Itens Atendidos
                    </div>
                    """, unsafe_allow_html=True)
                    
                else:
                    st.info(f"Sem dados mapeados para {comp}.")

        st.markdown("""
        <hr style='margin: 15px 0px 8px 0px;'>
        <div style="font-size: 1.05rem; color: #4a5568; display: flex; justify-content: space-between; font-weight: 700;">
            <span><b style="color: #2b4c7e;">→ Base Salva:</b> O último arquivo enviado fica salvo como base de consulta para toda a equipe.</span>
            <span><b style="color: #388e3c;">Metodologia:</b> Gráficos atualizados via integração analítica Protheus Parente Andrade.</span>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"⚠️ Erro analítico no processamento. Detalhe técnico: {e}")
else:
    st.info("💡 Clique em **⚙️ Abrir / Fechar Configurações** no topo para atualizar a base de dados.")
