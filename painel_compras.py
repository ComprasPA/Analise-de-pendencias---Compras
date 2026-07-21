import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA (Modo Wide otimizado para visão única)
st.set_page_config(layout="wide", page_title="Painel Executivo de Compras")

# ==========================================
# CSS CUSTOMIZADO (Compacto e Profissional)
# ==========================================
st.markdown("""
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.0rem;
    }
    .kpi-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        border-left: 5px solid;
        text-align: left;
    }
    .kpi-title {
        font-size: 0.8rem;
        color: #64748b;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 800;
        margin: 2px 0 0 0;
    }
    .kpi-blue { border-left-color: #2b6cb0; }
    .kpi-red { border-left-color: #e53e3e; }
    .kpi-green { border-left-color: #388e3c; }
    
    .kpi-value-blue { color: #2b6cb0; }
    .kpi-value-red { color: #e53e3e; }
    .kpi-value-green { color: #388e3c; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# CABEÇALHO COMPACTO
# ==========================================
header_col1, header_col2, header_col3 = st.columns([2.2, 1.5, 1])
with header_col1:
    st.markdown("### 📊 Painel Executivo - Suprimentos")
with header_col2:
    uploaded_file = st.file_uploader("Arquivo de pendências (.xlsx/.csv)", type=["xlsx", "xls", "csv"], label_visibility="collapsed")
with header_col3:
    data_base = st.date_input("Data base SLA:", datetime.date.today(), label_visibility="collapsed")

st.markdown("<hr style='margin: 5px 0px 15px 0px;'>", unsafe_allow_html=True)

# ==========================================
# PROCESSAMENTO DE DADOS
# ==========================================
if uploaded_file is not None:
    try:
        # 1. Leitura
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
        
        # Backlog Crítico (>= 20 dias)
        criticos_df = unique_scs[unique_scs['Days'] >= 20]
        backlog_critico = len(criticos_df)
        
        # Simulação lógica da Taxa de Rendimento Mensal (Itens resolvidos ou dentro do prazo padrão vs passivo)
        no_prazo = total_sc_unicas - backlog_critico
        taxa_rendimento = (no_prazo / total_sc_unicas * 100) if total_sc_unicas > 0 else 100

        # ==========================================
        # LINHA 1: CARDS EXECUTIVOS (KPIs)
        # ==========================================
        kpi1, kpi2, kpi3 = st.columns(3)
        
        with kpi1:
            st.markdown(f"""
            <div class="kpi-card kpi-blue">
                <div class="kpi-title">Total de Requisições Pendentes</div>
                <div class="kpi-value kpi-value-blue">{total_sc_unicas} <span style="font-size:0.9rem; font-weight:normal; color:#64748b;">({total_linhas} linhas)</span></div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi2:
            st.markdown(f"""
            <div class="kpi-card kpi-red">
                <div class="kpi-title">Backlog Crítico (>= 20 dias)</div>
                <div class="kpi-value kpi-value-red">{backlog_critico} <span style="font-size:0.9rem; font-weight:normal; color:#64748b;">(~{(backlog_critico/total_sc_unicas*100):.1f}% do total)</span></div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi3:
            st.markdown(f"""
            <div class="kpi-card kpi-green">
                <div class="kpi-title">Taxa de Rendimento Mensal</div>
                <div class="kpi-value kpi-value-green">{taxa_rendimento:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ==========================================
        # LINHA 2: GRÁFICO E TABELA (Lado a Lado na mesma tela)
        # ==========================================
        col_grafico, col_tabela = st.columns([1.1, 1])

        with col_grafico:
            st.markdown("##### 📊 Top 10 Centros de Custo (Volume de Pendências)")
            
            # Agrupamento Top 10 CC
            cc_volume = df.groupby('C Custo').size().reset_index(name='Quantidade').sort_values(by='Quantidade', ascending=False).head(10)
            cc_volume['C Custo'] = cc_volume['C Custo'].astype(str)
            cc_volume = cc_volume.sort_values(by='Quantidade', ascending=True) # Inverte para o maior ficar em cima no gráfico de barras horizontais

            fig = px.bar(
                cc_volume, 
                x='Quantidade', 
                y='C Custo', 
                orientation='h',
                text='Quantidade', 
                color='Quantidade', 
                color_continuous_scale='Blues'
            )
            
            fig.update_layout(
                xaxis_title="", 
                yaxis_title="",
                plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False,
                margin=dict(l=0, r=20, t=10, b=0),
                height=350
            )
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

        with col_tabela:
            st.markdown("##### 🔥 Itens Críticos (Maiores SLAs em Atraso)")
            
            # Preparação da tabela exigida: Solicitação + Centro de Custo + Dias em Atraso
            top_critical = criticos_df.sort_values(by='Days', ascending=False)[['Numero da SC', 'C Custo', 'Days']].head(8)
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
                height=350,
                hide_index=True
            )

    except Exception as e:
        st.error(f"⚠️ Erro ao processar o arquivo. Detalhe técnico: {e}")
else:
    st.info("💡 Faça o upload da planilha no campo superior direito para renderizar o painel executivo.")
