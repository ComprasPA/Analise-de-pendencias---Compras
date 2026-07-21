import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Painel Executivo de Suprimentos")

# ==========================================
# CSS CUSTOMIZADO (Estética Industrial/Warehouse)
# ==========================================
st.markdown("""
    <style>
    .main-header {
        font-size: 1.8rem;
        color: #1f3b58;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1rem;
        color: #6c757d;
        margin-bottom: 20px;
    }
    .card-container {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# CABEÇALHO E FILTROS DO TOPO
# ==========================================
st.markdown('<p class="main-header">📦 Painel de Operações e Backlog de Compras</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Monitoramento de Requisições, Níveis de Serviço (SLA) e Atividades por Centro de Custo</p>', unsafe_allow_html=True)

header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    uploaded_file = st.file_uploader("Carregar base de dados de pendências (.xlsx ou .csv)", type=["xlsx", "xls", "csv"])
with header_col2:
    data_base = st.date_input("Data base de corte (SLA):", datetime.date.today())

st.markdown("---")

# ==========================================
# PROCESSAMENTO DE DADOS
# ==========================================
if uploaded_file is not None:
    with st.spinner('Processando indicadores operacionais...'):
        try:
            # 1. Leitura do Arquivo
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8', header=0)
            else:
                df = pd.read_excel(uploaded_file, header=0)
                
            if 'Numero da SC' not in df.columns:
                new_header = df.iloc[0]
                df = df[1:]
                df.columns = new_header
                
            # 2. Cálculos e SLA
            hoje = pd.to_datetime(data_base)
            df['DT Emissao'] = pd.to_datetime(df['DT Emissao'], errors='coerce')
            df['Days'] = (hoje - df['DT Emissao']).dt.days
            
            unique_scs = df.drop_duplicates(subset=['Numero da SC'])
            total_linhas = len(df) 
            total_sc_unicas = len(unique_scs)
            
            # Critérios de Backlog (Ex: >= 20 dias)
            criticos_df = unique_scs[unique_scs['Days'] >= 20]
            backlog_critico = len(criticos_df)
            no_prazo = total_sc_unicas - backlog_critico
            
            # Taxa de atendimento / conformidade simulada para o Gauge
            taxa_conformidade = (no_prazo / total_sc_unicas * 100) if total_sc_unicas > 0 else 100

            # ==========================================
            # BLOCO 1: GAUGES (MEDIDORES ESTILO VELOCÍMETRO)
            # ==========================================
            st.markdown("##### 📈 Indicadores de Desempenho e Nível de Serviço (SLA)")
            
            gauge_col1, gauge_col2, gauge_col3 = st.columns(3)
            
            def criar_gauge(titulo, valor, total_ref, cor_ponteiro):
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = valor,
                    title = {'text': titulo, 'font': {'size': 14}},
                    number = {'font': {'size': 24, 'color': '#1f3b58'}},
                    gauge = {
                        'axis': {'range': [None, max(total_ref, valor * 1.5, 10)], 'tickwidth': 1, 'tickcolor': "darkblue"},
                        'bar': {'color': cor_ponteiro},
                        'bgcolor': "white",
                        'borderwidth': 2,
                        'bordercolor': "#dcdcdc",
                        'steps': [
                            {'range': [0, total_ref * 0.5], 'color': '#e8f5e9'},
                            {'range': [total_ref * 0.5, total_ref * 0.85], 'color': '#fffde7'},
                            {'range': [total_ref * 0.85, max(total_ref * 1.5, valor * 1.5, 10)], 'color': '#ffebee'}
                        ],
                    }
                ))
                fig.update_layout(height=180, margin=dict(l=20, r=20, t=30, b=10))
                return fig

            with gauge_col1:
                fig1 = criar_gauge("Total de Requisições Ativas", total_sc_unicas, total_sc_unicas, "#2b6cb0")
                st.plotly_chart(fig1, use_container_width=True)
                st.markdown(f"<p style='text-align: center; color: #6c757d; font-size: 0.85rem;'><b>{total_linhas}</b> linhas totais na extração</p>", unsafe_allow_html=True)

            with gauge_col2:
                fig2 = criar_gauge("Requisições No Prazo (< 20 dias)", no_prazo, total_sc_unicas, "#388e3c")
                st.plotly_chart(fig2, use_container_width=True)
                taxa_prazo = (no_prazo / total_sc_unicas * 100) if total_sc_unicas > 0 else 0
                st.markdown(f"<p style='text-align: center; color: #388e3c; font-size: 0.85rem;'><b>{taxa_prazo:.1f}%</b> da carteira saudável</p>", unsafe_allow_html=True)

            with gauge_col3:
                fig3 = criar_gauge("Backlog Crítico (>= 20 dias)", backlog_critico, total_sc_unicas, "#e53e3e")
                st.plotly_chart(fig3, use_container_width=True)
                st.markdown(f"<p style='text-align: center; color: #e53e3e; font-size: 0.85rem;'><b>{backlog_critico}</b> itens ultrapassaram o SLA</p>", unsafe_allow_html=True)

            st.markdown("---")

            # ==========================================
            # BLOCO 2: CARTÕES DE ATIVIDADE EM BLOCOS COLORIDOS
            # ==========================================
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            
            with metric_col1:
                st.markdown(f"""
                <div style="background-color: #1f3b58; color: white; padding: 15px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 2rem; font-weight: bold;">{total_sc_unicas}</div>
                    <div style="font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;">Requisições Totais (Únicas)</div>
                </div>
                """, unsafe_allow_html=True)
                
            with metric_col2:
                st.markdown(f"""
                <div style="background-color: #388e3c; color: white; padding: 15px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 2rem; font-weight: bold;">{no_prazo}</div>
                    <div style="font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;">Itens no Fluxo Normal</div>
                </div>
                """, unsafe_allow_html=True)
                
            with metric_col3:
                st.markdown(f"""
                <div style="background-color: #ed8034; color: white; padding: 15px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 2rem; font-weight: bold;">{backlog_critico}</div>
                    <div style="font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;">Backlog Exigindo Ação</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ==========================================
            # BLOCO 3: GRÁFICO DE BARRAS POR DATA E TABELA DETALHADA
            # ==========================================
            row_col1, row_col2 = st.columns([1.3, 1])

            with row_col1:
                st.markdown("##### 📊 Requisições por Data de Emissão (Volume Diário)")
                
                # Agrupando por data de emissão para simular o gráfico de barras temporais da referência
                df_grouped_date = df.dropna(subset=['DT Emissao']).copy()
                df_grouped_date['Data_Emissao_Fmt'] = df_grouped_date['DT Emissao'].dt.strftime('%Y-%m-%d')
                
                date_counts = df_grouped_date.groupby('Data_Emissao_Fmt').size().reset_index(name='Quantidade')
                date_counts = date_counts.sort_values('Data_Emissao_Fmt').tail(15) # Exibe os últimos 15 dias com movimento
                
                fig_date = px.bar(
                    date_counts,
                    x='Data_Emissao_Fmt',
                    y='Quantidade',
                    text='Quantidade',
                    color='Quantidade',
                    color_continuous_scale='Teal'
                )
                fig_date.update_layout(
                    xaxis_title="Data de Emissão",
                    yaxis_title="Volume de SCs",
                    plot_bgcolor="rgba(0,0,0,0)",
                    coloraxis_showscale=False,
                    margin=dict(l=0, r=0, t=20, b=0),
                    height=400
                )
                fig_date.update_traces(textposition='outside')
                st.plotly_chart(fig_date, use_container_width=True)

            with row_col2:
                st.markdown("##### ⚠️ Detalhamento de Itens Críticos (Top 10 SLA)")
                
                top_critical = criticos_df.sort_values(by='Days', ascending=False)[['Numero da SC', 'C Custo', 'Days']].head(10)
                top_critical.columns = ['Nº da SC', 'Centro de Custo', 'Dias em Atraso']
                top_critical['Centro de Custo'] = top_critical['Centro de Custo'].astype(str)

                def color_critical(val):
                    color = '#e53e3e' if isinstance(val, int) and val >= 20 else 'black'
                    return f'color: {color}; font-weight: bold'
                
                styled_table = top_critical.style.map(
                    color_critical, subset=['Dias em Atraso']
                ).format({"Dias em Atraso": "{} dias"})
                
                st.dataframe(
                    styled_table, 
                    use_container_width=True,
                    height=400,
                    hide_index=True
                )

        except Exception as e:
            st.error(f"⚠️ Erro ao processar o arquivo. Detalhe técnico: {e}")
