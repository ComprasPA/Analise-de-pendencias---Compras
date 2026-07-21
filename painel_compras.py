import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go
import matplotlib
matplotlib.use('Agg') # Garante o processamento seguro de imagens em segundo plano na nuvem
import matplotlib.pyplot as plt
import io

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Panorama Executivo de Suprimentos")

# ==========================================
# CSS CUSTOMIZADO (Visual Sólido e Limpo)
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
    /* Cartões executivos com fundo sólido garantido */
    .kpi-card-solid {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 10px;
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
        # PASSO 1: CABEÇALHO E CARTÕES COM FUNDO SÓLIDO
        # ==========================================
        st.markdown(f"""
        <div class="header-box">
            <span style="font-size: 1.2rem; font-weight: bold;">PANORAMA DE PENDÊNCIAS DE REQUISIÇÕES DE COMPRA</span>
            <span style="font-size: 0.9rem;">DADOS CONSOLIDADOS | {hoje.strftime("%d/%m/%Y")}</span>
        </div>
        <div class="resumo-bar">DIAGNÓSTICO E VALIDAÇÃO ESTRATÉGICA (INDICADORES EXECUTIVOS)</div>
        """, unsafe_allow_html=True)

        kpi_c1, kpi_c2, kpi_c3 = st.columns(3)

        with kpi_c1:
            st.markdown(f"""
            <div class="kpi-card-solid">
                <div style="font-size: 0.75rem; color: #475569; font-weight: bold; text-transform: uppercase;">TOTAL DE REQUISIÇÕES (ÚNICAS)</div>
                <div style="font-size: 2rem; font-weight: bold; color: #2b6cb0; margin: 5px 0;">{total_sc_unicas}</div>
                <div style="font-size: 0.75rem; color: #64748b;">Volume Bruto: <b>{total_linhas} itens</b> processados</div>
            </div>
            """, unsafe_allow_html=True)

        with kpi_c2:
            st.markdown(f"""
            <div class="kpi-card-solid">
                <div style="font-size: 0.75rem; color: #475569; font-weight: bold; text-transform: uppercase;">BACKLOG CRÍTICO (>=20 DIAS)</div>
                <div style="font-size: 2rem; font-weight: bold; color: #e53e3e; margin: 5px 0;">{backlog_critico} 🔥</div>
                <div style="font-size: 0.75rem; color: #64748b;"><b>{(backlog_critico/total_sc_unicas*100 if total_sc_unicas > 0 else 0):.1f}%</b> das SCs ativas</div>
            </div>
            """, unsafe_allow_html=True)

        with kpi_c3:
            st.markdown(f"""
            <div class="kpi-card-solid">
                <div style="font-size: 0.75rem; color: #475569; font-weight: bold; text-transform: uppercase;">TAXA DE ATENDIMENTO / SAÚDE</div>
                <div style="font-size: 2rem; font-weight: bold; color: #388e3c; margin: 5px 0;">{taxa_atendimento_val:.1f}% ↗</div>
                <div style="font-size: 0.75rem; color: #64748b;">Dentro do SLA padrão (&lt;20 dias)</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Botão de comando para gerar os gráficos
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            if not st.session_state['executar_analise']:
                if st.button("🚀 Gerar Detalhamento Analítico e Gráfico", type="primary", use_container_width=True):
                    st.session_state['executar_analise'] = True
                    st.rerun()
            else:
                if st.button("🔄 Ocultar / Atualizar Análise", use_container_width=True):
                    st.session_state['executar_analise'] = False
                    st.rerun()

        # ==========================================
        # PASSO 2: RENDERIZAÇÃO DOS GRÁFICOS + BOTÃO DE DOWNLOAD DE IMAGEM
        # ==========================================
        if st.session_state['executar_analise']:
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

            # ==========================================
            # BOTÃO DE GERAR E BAIXAR IMAGEM DOS INDICADORES
            # ==========================================
            st.markdown("<br>", unsafe_allow_html=True)
            down_col1, down_col2, down_col3 = st.columns([1, 2, 1])
            with down_col2:
                if st.button("📥 Baixar Relatório em Imagem (PNG)", type="secondary", use_container_width=True):
                    # Criação da imagem consolidada via Matplotlib
                    fig_img, ax_img = plt.subplots(figsize=(10, 5), facecolor='#ffffff')
                    ax_img.axis('off')

                    # Desenha um painel estilo executivo resumido
                    ax_img.text(0.5, 0.85, 'PANORAMA DE PENDÊNCIAS DE REQUISIÇÕES DE COMPRA', ha='center', va='center', fontsize=16, fontweight='bold', color='#1f3b58')
                    ax_img.text(0.5, 0.75, f'DADOS CONSOLIDADOS | {hoje.strftime("%d/%m/%Y")}', ha='center', va='center', fontsize=11, color='#475569')

                    # Caixas de texto simulando os KPIs
                    ax_img.text(0.2, 0.45, f'Total de SCs (Únicas)\n{total_sc_unicas}', ha='center', va='center', fontsize=13, fontweight='bold', color='#2b6cb0', bbox=dict(boxstyle='round,pad=0.8', facecolor='#f1f5f9', edgecolor='#cbd5e1'))
                    ax_img.text(0.5, 0.45, f'Backlog Crítico (>=20d)\n{backlog_critico}', ha='center', va='center', fontsize=13, fontweight='bold', color='#e53e3e', bbox=dict(boxstyle='round,pad=0.8', facecolor='#f1f5f9', edgecolor='#cbd5e1'))
                    ax_img.text(0.8, 0.45, f'Taxa de Atendimento\n{taxa_atendimento_val:.1f}%', ha='center', va='center', fontsize=13, fontweight='bold', color='#388e3c', bbox=dict(boxstyle='round,pad=0.8', facecolor='#f1f5f9', edgecolor='#cbd5e1'))

                    ax_img.text(0.5, 0.15, f'Fonte do arquivo: {uploaded_file.name} | Total de linhas: {total_linhas}', ha='center', va='center', fontsize=9, color='#94a3b8')

                    # Salva em memória
                    buf = io.BytesIO()
                    fig_img.savefig(buf, format="png", dpi=200, bbox_inches='tight')
                    plt.close(fig_img)

                    st.download_button(
                        label="💾 Clique aqui para salvar a Imagem PNG",
                        data=buf.getvalue(),
                        file_name=f"panorama_compras_{hoje.strftime('%Y%m%d')}.png",
                        mime="image/png"
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
    st.info("💡 Faça o upload da planilha de pendências no topo à direita para carregar a validação analítica.")
