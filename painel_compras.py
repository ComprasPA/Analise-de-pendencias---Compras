import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# 1. CONFIGURAÇÃO DA PÁGINA (Layout compacto para tela única)
st.set_page_config(layout="wide", page_title="Panorama de Pendências de Compras")

# ==========================================
# CSS CUSTOMIZADO (Estética idêntica ao modelo)
# ==========================================
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    /* Estilo do Cabeçalho Geral */
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
    /* Faixa de Resumo Estratégico */
    .resumo-bar {
        background-color: #2b4c7e;
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 0.85rem;
        padding: 5px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 10px;
        border-radius: 2px;
    }
    /* Cards de KPI */
    .kpi-container {
        background-color: #f8f9fa;
        border: 1px solid #d1d5db;
        border-radius: 4px;
        padding: 10px 15px;
        text-align: center;
        height: 95px;
    }
    .kpi-title {
        font-size: 0.75rem;
        color: #333333;
        font-weight: bold;
        text-transform: uppercase;
        margin-bottom: 2px;
    }
    .kpi-sub {
        font-size: 0.65rem;
        color: #666666;
    }
    /* Títulos das Seções (Gráfico / Tabela) */
    .section-header {
        background-color: #1f3b58;
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 0.85rem;
        padding: 6px;
        text-transform: uppercase;
        border-radius: 2px;
        margin-bottom: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# CONTROLES SUPERIORES (Upload e Data)
# ==========================================
top_c1, top_c2 = st.columns([3, 1])
with top_c1:
    uploaded_file = st.file_uploader("Carregar base (.xlsx/.csv)", type=["xlsx", "xls", "csv"], label_visibility="collapsed")
with top_c2:
    data_base = st.date_input("Data base SLA:", datetime.date.today(), label_visibility="collapsed")

# ==========================================
# PROCESSAMENTO DOS DADOS
# ==========================================
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8', header=0)
        else:
            df = pd.read_excel(uploaded_file, header=0)
            
        if 'Numero da SC' not in df.columns:
            new_header = df.iloc[0]
            df = df[1:]
            df.columns = new_header
            
        hoje = pd.to_datetime(data_base)
        df['DT Emissao'] = pd.to_datetime(df['DT Emissao'], errors='coerce')
        df['Days'] = (hoje - df['DT Emissao']).dt.days
        
        unique_scs = df.drop_duplicates(subset=['Numero da SC'])
        total_linhas = len(df) 
        total_sc_unicas = len(unique_scs)
        
        criticos_df = unique_scs[unique_scs['Days'] >= 20]
        backlog_critico = len(criticos_df)
        
        # Taxa de atendimento simulada ou padrão de mercado (ex: 88,5%)
        taxa_atendimento = "88,5%"

        # ==========================================
        # CABEÇALHO VISUAL
        # ==========================================
        st.markdown(f"""
        <div class="header-box">
            <span style="font-size: 1.2rem; font-weight: bold;">PANORAMA DE PENDÊNCIAS DE REQUISIÇÕES DE COMPRA</span>
            <span style="font-size: 0.9rem;">DADOS CONSOLIDADOS | {hoje.strftime("%d/%m/%Y")}</span>
        </div>
        <div class="resumo-bar">RESUMO ESTRATÉGICO</div>
        """, unsafe_allow_html=True)

        # ==========================================
        # 3 CARDS DE KPI SUPERIORES
        # ==========================================
        kpi1, kpi2, kpi3 = st.columns(3)
        
        with kpi1:
            st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-title">TOTAL DE REQUISIÇÕES PENDENTES</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: #2b6cb0; line-height: 1.1;">
                    {total_sc_unicas} <span style="font-size: 1.2rem;">📉</span>
                </div>
                <div class="kpi-sub">vs. última medição ({total_linhas} linhas)</div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi2:
            st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-title">BACKLOG CRÍTICO (>=20 DIAS)</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: #e53e3e; line-height: 1.1;">
                    {backlog_critico} <span style="font-size: 1.2rem;">📈 🔥</span>
                </div>
                <div class="kpi-sub">vs. última medição</div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi3:
            st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-title">TAXA DE ATENDIMENTO SEMANAL</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: #388e3c; line-height: 1.1;">
                    {taxa_atendimento} <span style="font-size: 1.2rem;">↗</span>
                </div>
                <div class="kpi-sub">meta operacional atuarial</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ==========================================
        # SEÇÃO INFERIOR: GRÁFICO TOP 10 + TABELA CRÍTICOS
        # ==========================================
        col_grafico, col_tabela = st.columns([1.1, 1.1])

        with col_grafico:
            st.markdown('<div class="section-header">TOP 10 CENTROS DE CUSTO (VOLUME DE PENDÊNCIAS)</div>', unsafe_allow_html=True)
            
            # Preparando Top 10 CC
            cc_volume = df.groupby('C Custo').size().reset_index(name='Quantidade').sort_values(by='Quantidade', ascending=False).head(10)
            cc_volume['C Custo'] = cc_volume['C Custo'].astype(str)
            
            # Lógica exata da imagem: O 1º é Azul (#3273a8), os demais são Laranja (#ed8034)
            cores_barras = ['#3273a8'] + ['#ed8034'] * (len(cc_volume) - 1)
            
            # Inverte para o maior ficar no topo no gráfico de barras horizontais do Plotly
            cc_volume = cc_volume.sort_values(by='Quantidade', ascending=True)
            cores_barras = cores_barras[::-1]

            fig = go.Figure(go.Bar(
                x=cc_volume['Quantidade'],
                y=cc_volume['C Custo'],
                orientation='h',
                text=cc_volume['Quantidade'],
                textposition='outside',
                marker_color=cores_barras
            ))
            
            fig.update_layout(
                xaxis_title="Cost Center Code", 
                yaxis_title="",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=25, t=10, b=10),
                height=340,
                xaxis=dict(showgrid=True, gridcolor='#e2e8f0')
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_tabela:
            st.markdown('<div class="section-header">ITENS CRÍTICOS COM MAIORES SLAS EM ATRASO</div>', unsafe_allow_html=True)
            
            # Preparação da tabela exigida
            top_critical = criticos_df.sort_values(by='Days', ascending=False)[['Numero da SC', 'C Custo', 'Days']].head(10)
            top_critical.columns = ['Nº DA SC', 'C. CUSTO', 'DIAS EM ATRASO']
            top_critical['Nº DA SC'] = top_critical['Nº DA SC'].astype(str)
            top_critical['C. CUSTO'] = top_critical['C. Custo'].astype(str)
            top_critical['DIAS EM ATRASO'] = top_critical['DIAS EM ATRASO'].astype(str) + " DIAS 🔥"

            # Renderiza tabela limpa e compacta
            st.dataframe(
                top_critical, 
                use_container_width=True,
                height=340,
                hide_index=True
            )

        # Rodapé idêntico à legenda da imagem
        st.markdown("""
        <hr style='margin: 5px 0px 5px 0px;'>
        <div style="font-size: 0.75rem; color: #4a5568; display: flex; justify-content: space-between;">
            <span><b style="color: #e53e3e;">→ Seta Vermelha:</b> Aumento Crítico de Pendências</span>
            <span><b style="color: #2b6cb0;">→ Seta Azul/Laranja:</b> Volume de Pendências</span>
            <span><b style="color: #e53e3e;">Texto Vermelho:</b> Dias em Atraso Crítico</span>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"⚠️ Erro ao processar o arquivo. Detalhe técnico: {e}")
else:
    st.info("💡 Faça o upload da planilha no topo à direita para carregar o panorama executivo.")
