import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Panorama Executivo de Suprimentos")

# ==========================================
# CSS CUSTOMIZADO (Fundos Sólidos e Alta Legibilidade)
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
    .gauge-card {
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        text-align: center;
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
        # PASSO 1: CABEÇALHO E VELOCÍMETROS COM FUNDO SÓLIDO
        # ==========================================
        st.markdown(f"""
        <div class="header-box">
            <span style="font-size: 1.2rem; font-weight: bold;">PANORAMA DE PENDÊNCIAS DE REQUISIÇÕES DE COMPRA</span>
            <span style="font-size: 0.9rem;">DADOS CONSOLIDADOS | {hoje.strftime("%d/%m/%Y")}</span>
        </div>
        <div class="resumo-bar">DIAGNÓSTICO E VALIDAÇÃO ESTRATÉGICA (VELOCÍMETROS DE DESEMPENHO)</div>
        """, unsafe_allow_html=True)

        def criar_gauge(titulo, valor, max_val, cor_barra, sufixo=""):
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = valor,
                number = {'suffix': sufixo, 'font': {'size': 26, 'color': '#1f3b58', 'family': 'Arial'}},
                title = {'text': titulo, 'font': {'size': 12, 'color': '#1f2937', 'family': 'Arial'}},
                gauge = {
                    'axis': {'range': [None, max_val], 'tickwidth': 1, 'tickcolor': "#475569"},
                    'bar': {'color': cor_barra},
                    'bgcolor': "#ffffff",
                    'borderwidth': 1,
                    'bordercolor': "#cbd5e1",
                    'steps': [
                        {'range': [0, max_val * 0.6], 'color': '#f1f5f9'},
                        {'range': [max_val * 0.6, max_val], 'color': '#e2e8f0'}
                    ],
                }
            ))
            fig.update_layout(height=150, margin=dict(l=20, r=20, t=30, b=10), paper_bgcolor='rgba(0,0,0,0)')
            return fig

        gauge_col1, gauge_col2, gauge_col3 = st.columns(3)

        with gauge_col1:
            max_sc = max(total_sc_unicas * 1.5, 10)
            fig1 = criar_gauge("TOTAL DE REQUISIÇÕES (ÚNICAS)", total_sc_unicas, max_sc, "#2b6cb0")
            st.markdown('<div class="gauge-card">', unsafe_allow_html=True)
            st.plotly_chart(fig1, use_container_width=True)
            st.markdown(f"<p style='text-align: center; color: #475569; font-size: 0.75rem; margin-top: -5px;'>Volume Bruto: <b>{total_linhas} itens</b></p>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with gauge_col2:
            max_backlog = max(total_sc_unicas, 10)
            fig2 = criar_gauge("BACKLOG CRÍTICO (>=20 DIAS)", backlog_critico, max_backlog, "#e53e3e")
            st.markdown('<div class="gauge-card">', unsafe_allow_html=True)
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown(f"<p style='text-align: center; color: #e53e3e; font-size: 0.75rem; margin-top: -5px;'><b>{(backlog_critico/total_sc_unicas*100 if total_sc_unicas > 0 else 0):.1f}%</b> das SCs ativas</p>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with gauge_col3:
            fig3 = criar_gauge("TAXA DE ATENDIMENTO / SAÚDE", round(taxa_atendimento_val, 1), 100, "#388e3c", sufixo="%")
            st.markdown('<div class="gauge-card">', unsafe_allow_html=True)
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown(f"<p style='text-align: center; color: #388e3c; font-size: 0.75rem; margin-top: -5px;'>Dentro do SLA padrão (&lt;20 dias)</p>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ==========================================
        # PASSO 2: RENDERIZAÇÃO DIRETA DOS GRÁFICOS (TOP 10 CC + TABELA CRÍTICOS)
        # ==========================================
        st.markdown("---")
        col_grafico, col_tabela = st.columns([1.1, 1.1])

        with col_grafico:
            st.markdown('<div class="section-header">TOP 10 CENTROS DE CUSTO (VOLUME DE PENDÊNCIAS)</div>', unsafe_allow_html=True)
            
            cc_volume = df.groupby(col_cc).size().reset_index(name='Quantidade').sort_values(by='Quantidade', ascending=False).head(10)
            cc_volume[col_cc] = cc_volume[col_cc].astype(str)
            
            cores_barras = ['#3273a8'] + ['#ed8034'] * (len(cc_volume) - 1)
            cc_volume = cc_volume.sort_values(by='Quantidade', ascending=True)
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
                yaxis=dict(type='category')
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_tabela:
            st.markdown('<div class="section-header">ITENS CRÍTICOS COM MAIORES SLAS EM ATRASO</div>', unsafe_allow_html=True)
            
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
    st.info("💡 Faça o upload da planilha de pendências no topo à direita para carregar o panorama executivo completo.")
