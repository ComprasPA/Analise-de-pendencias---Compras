import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Panorama de Pendências de Compras")

# ==========================================
# CSS CUSTOMIZADO (Visual Executivo Compacto)
# ==========================================
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
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
    uploaded_file = st.file_uploader("Upload do arquivo de pendências (.xlsx/.csv)", type=["xlsx", "xls", "csv"])
with top_c2:
    data_base = st.date_input("Data base para cálculo de SLA:", datetime.date.today())

# Inicializa estado para controle do botão
if 'executar_analise' not in st.session_state:
    st.session_state['executar_analise'] = False

if uploaded_file is None:
    st.session_state['executar_analise'] = False

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
            
        # Limpeza de espaços nos nomes das colunas
        df.columns = df.columns.astype(str).str.strip()

        # Validação e correção das colunas essenciais baseadas no arquivo real
        col_sc = 'Numero da SC' if 'Numero da SC' in df.columns else None
        col_cc = 'C Custo' if 'C Custo' in df.columns else None
        col_dt = 'DT Emissao' if 'DT Emissao' in df.columns else None

        if not col_sc or not col_cc or not col_dt:
            st.error(f"⚠️ Erro: O arquivo não contém as colunas esperadas ('Numero da SC', 'C Custo', 'DT Emissao'). Colunas encontradas: {list(df.columns)}")
            st.stop()

        # Limpeza e conversões de datas e SLA
        df = df.dropna(subset=[col_sc])
        hoje = pd.to_datetime(data_base)
        df[col_dt] = pd.to_datetime(df[col_dt], errors='coerce')
        df['Days'] = (hoje - df[col_dt]).dt.days

        # Métricas Consolidadas Reais
        total_linhas = len(df) # 297 itens totais
        unique_scs = df.drop_duplicates(subset=[col_sc]).copy()
        total_sc_unicas = len(unique_scs) # 103 requisições únicas
        
        criticos_df = unique_scs[unique_scs['Days'] >= 20]
        backlog_critico = len(criticos_df)
        
        no_prazo = total_sc_unicas - backlog_critico
        taxa_atendimento_val = (no_prazo / total_sc_unicas * 100) if total_sc_unicas > 0 else 100

        # ==========================================
        # PASSO 1: EXIBIÇÃO DO DIAGNÓSTICO NUMÉRICO
        # ==========================================
        st.markdown(f"""
        <div class="header-box">
            <span style="font-size: 1.2rem; font-weight: bold;">PANORAMA DE PENDÊNCIAS DE REQUISIÇÕES DE COMPRA</span>
            <span style="font-size: 0.9rem;">DADOS CONSOLIDADOS | {hoje.strftime("%d/%m/%Y")}</span>
        </div>
        <div class="resumo-bar">DIAGNÓSTICO E VALIDAÇÃO ESTRATÉGICA</div>
        """, unsafe_allow_html=True)

        kpi1, kpi2, kpi3 = st.columns(3)
        
        with kpi1:
            st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-title">TOTAL DE REQUISIÇÕES (ÚNICAS / ITENS)</div>
                <div style="font-size: 1.6rem; font-weight: bold; color: #2b6cb0; line-height: 1.1;">
                    {total_sc_unicas} SCs <span style="font-size: 0.9rem; font-weight:normal;">({total_linhas} itens)</span>
                </div>
                <div class="kpi-sub">Volume consolidado sem duplicidade de cabeçalho</div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi2:
            st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-title">BACKLOG CRÍTICO (>=20 DIAS)</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: #e53e3e; line-height: 1.1;">
                    {backlog_critico} <span style="font-size: 1.2rem;">📈 🔥</span>
                </div>
                <div class="kpi-sub">{(backlog_critico/total_sc_unicas*100 if total_sc_unicas > 0 else 0):.1f}% das SCs ativas</div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi3:
            st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-title">TAXA DE ATENDIMENTO / SAÚDE</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: #388e3c; line-height: 1.1;">
                    {taxa_atendimento_val:.1f}% <span style="font-size: 1.2rem;">↗</span>
                </div>
                <div class="kpi-sub">Dentro do SLA padrão (<20 dias)</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Botão de comando para gerar os gráficos
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            if not st.session_state['executar_analise']:
                if st.button("🚀 Gerar Gráficos e Detalhamento Analítico", type="primary", use_container_width=True):
                    st.session_state['executar_analise'] = True
                    st.rerun()
            else:
                if st.button("🔄 Ocultar / Atualizar Análise", use_container_width=True):
                    st.session_state['executar_analise'] = False
                    st.rerun()

        # ==========================================
        # PASSO 2: RENDERIZAÇÃO DOS GRÁFICOS (TOP 10 CC + TABELA CRÍTICOS)
        # ==========================================
        if st.session_state['executar_analise']:
            st.markdown("---")
            col_grafico, col_tabela = st.columns([1.1, 1.1])

            with col_grafico:
                st.markdown('<div class="section-header">TOP 10 CENTROS DE CUSTO (VOLUME DE PENDÊNCIAS)</div>', unsafe_allow_html=True)
                
                # Agrupamento rigoroso do Top 10 Centros de Custo baseado na coluna 'C Custo'
                cc_volume = df.groupby(col_cc).size().reset_index(name='Quantidade').sort_values(by='Quantidade', ascending=False).head(10)
                cc_volume[col_cc] = cc_volume[col_cc].astype(str)
                
                # Cores padrão: 1º Azul Escuro, demais Laranja Operacional
                cores_barras = ['#3273a8'] + ['#ed8034'] * (len(cc_volume) - 1)
                cc_volume = cc_volume.sort_values(by='Quantidade', ascending=True) # Inverte para o maior no topo
                cores_barras = cores_barras[::-1]

                fig = go.Figure(go.Bar(
                    x=cc_volume['Quantidade'],
                    y=cc_volume[col_cc],
                    orientation='h',
                    text=cc_volume['Quantidade'],
                    textposition='outside',
                    marker_color=cores_barras
                ))
                
                fig.update_layout(
                    xaxis_title="Volume de Requisições / Itens", 
                    yaxis_title="Centro de Custo",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=25, t=10, b=10),
                    height=360,
                    xaxis=dict(showgrid=True, gridcolor='#e2e8f0'),
                    yaxis=dict(type='category') # Força o eixo Y a tratar os códigos como texto/categorias fixas
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_tabela:
                st.markdown('<div class="section-header">ITENS CRÍTICOS COM MAIORES SLAS EM ATRASO</div>', unsafe_allow_html=True)
                
                # Tabela restrita a Solicitação + Centro de Custo + Dias em Atraso (Top 10)
                top_critical = criticos_df.sort_values(by='Days', ascending=False)[[col_sc, col_cc, 'Days']].head(10)
                top_critical.columns = ['Nº DA SC', 'C. CUSTO', 'DIAS EM ATRASO']
                top_critical['Nº DA SC'] = top_critical['Nº DA SC'].astype(str)
                top_critical['C. CUSTO'] = top_critical['C. CUSTO'].astype(str)
                top_critical['DIAS EM ATRASO'] = top_critical['DIAS EM ATRASO'].astype(str) + " DIAS 🔥"

                st.dataframe(
                    top_critical, 
                    use_container_width=True,
                    height=360,
                    hide_index=True
                )

            st.markdown("""
            <hr style='margin: 10px 0px 5px 0px;'>
            <div style="font-size: 0.75rem; color: #4a5568; display: flex; justify-content: space-between;">
                <span><b style="color: #e53e3e;">→ Alerta Crítico:</b> Backlog com inércia superior a 20 dias</span>
                <span><b style="color: #3273a8;">→ Top 10 CC:</b> Eixo Y com os 10 principais centros de custo mapeados</span>
                <span><b style="color: #388e3c;">Metodologia:</b> Contagem consolidada de SCs e itens do Protheus</span>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"⚠️ Erro analítico no processamento do arquivo. Detalhe técnico: {e}")
else:
    st.info("💡 Faça o upload da planilha de pendências no topo à direita para carregar a validação analítica inicial.")
