import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA (Deve ser a 1ª linha)
st.set_page_config(layout="wide", page_title="Painel Executivo de Compras")

# ==========================================
# CSS CUSTOMIZADO (Para deixar com cara Premium)
# ==========================================
st.markdown("""
    <style>
    .kpi-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid;
        text-align: center;
        margin-bottom: 20px;
    }
    .kpi-title {
        font-size: 1.1rem;
        color: #6c757d;
        margin-bottom: 10px;
        font-weight: 600;
        text-transform: uppercase;
    }
    .kpi-value {
        font-size: 2.8rem;
        font-weight: 700;
        margin: 0;
    }
    .kpi-blue { border-left-color: #2b6cb0; }
    .kpi-red { border-left-color: #e53e3e; }
    .kpi-value-blue { color: #2b6cb0; }
    .kpi-value-red { color: #e53e3e; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# CABEÇALHO DO DASHBOARD
# ==========================================
st.title("📊 Painel Executivo - Requisições de Compra")
st.markdown("Monitoramento de pendências, volumes e Backlog Crítico por Centro de Custo.")

with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        uploaded_file = st.file_uploader("Upload do relatório (Excel ou CSV)", type=["xlsx", "xls", "csv"])
    with col2:
        data_base = st.date_input("Data base para SLA:", datetime.date.today())

# ==========================================
# PROCESSAMENTO DE DADOS
# ==========================================
if uploaded_file is not None:
    with st.spinner('Consolidando dados do relatório...'):
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
            
            criticos_df = unique_scs[unique_scs['Days'] >= 20]
            backlog_critico = len(criticos_df)
            percentual_critico = (backlog_critico / total_sc_unicas * 100) if total_sc_unicas > 0 else 0
            
            # 3. TOP 10 Volume por CC (Para o Gráfico)
            cc_volume = df.groupby('C Custo').size().reset_index(name='Quantidade').sort_values(by='Quantidade', ascending=False).head(10)
            cc_volume['C Custo'] = cc_volume['C Custo'].astype(str)
            # Inverter a ordem para o gráfico de barras horizontais ficar com o maior no topo
            cc_volume = cc_volume.sort_values(by='Quantidade', ascending=True)

            # 4. TOP 10 Críticos (Para a Tabela)
            top_critical = criticos_df.sort_values(by='Days', ascending=False)[['Numero da SC', 'C Custo', 'Days']].head(10)
            top_critical.columns = ['Nº da SC', 'Centro de Custo', 'Dias em Atraso']
            top_critical['Centro de Custo'] = top_critical['Centro de Custo'].astype(str)

            # ==========================================
            # RENDERIZAÇÃO NA TELA
            # ==========================================
            st.markdown("---")
            st.markdown(f"#### 📅 DADOS CONSOLIDADOS: {hoje.strftime('%d/%m/%Y')} | Fonte: `{uploaded_file.name}`")
            
            # --- CARDS HTML PREMIUM ---
            kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
            
            with kpi_col1:
                st.markdown(f"""
                <div class="kpi-card kpi-blue">
                    <div class="kpi-title">Total de Requisições (Únicas)</div>
                    <div class="kpi-value kpi-value-blue">{total_sc_unicas}</div>
                    <div style="color: #6c757d; font-size: 0.9rem; margin-top: 5px;">{total_linhas} linhas/itens processados</div>
                </div>
                """, unsafe_allow_html=True)
                
            with kpi_col2:
                st.markdown(f"""
                <div class="kpi-card kpi-red">
                    <div class="kpi-title">Backlog Crítico (>= 20 dias)</div>
                    <div class="kpi-value kpi-value-red">{backlog_critico}</div>
                    <div style="color: #6c757d; font-size: 0.9rem; margin-top: 5px;">Representa ~{percentual_critico:.1f}% do passivo total</div>
                </div>
                """, unsafe_allow_html=True)
                
            with kpi_col3:
                 # Simulador de status baseado no volume de atrasos
                 status_color = "kpi-value-red" if backlog_critico > 0 else "kpi-value-blue"
                 status_text = "ALERTA ATIVO" if backlog_critico > 0 else "NORMAL"
                 border_color = "kpi-red" if backlog_critico > 0 else "kpi-blue"
                 
                 st.markdown(f"""
                <div class="kpi-card {border_color}">
                    <div class="kpi-title">Status da Carteira</div>
                    <div class="kpi-value {status_color}">{status_text}</div>
                    <div style="color: #6c757d; font-size: 0.9rem; margin-top: 5px;">Acompanhamento de SLAs em inércia</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # --- GRÁFICO E TABELA (Usando Plotly Express para visual Premium) ---
            dash_col1, dash_col2 = st.columns([1.2, 1])
            
            with dash_col1:
                st.markdown("##### 📊 TOP 10 CENTROS DE CUSTO (Volume de Pendências)")
                
                # Criando gráfico Plotly profissional
                fig = px.bar(
                    cc_volume, 
                    x='Quantidade', 
                    y='C Custo', 
                    orientation='h',
                    text='Quantidade', # Mostra o número na ponta da barra
                    color='Quantidade', # Gradiente de cor baseado no volume
                    color_continuous_scale='Blues' # Usa paleta de azul
                )
                
                # Ajustando o visual do gráfico
                fig.update_layout(
                    xaxis_title="", 
                    yaxis_title="Código do CC",
                    plot_bgcolor="rgba(0,0,0,0)", # Fundo transparente limpo
                    coloraxis_showscale=False, # Esconde a barra de legenda lateral
                    margin=dict(l=0, r=20, t=30, b=0),
                    height=450
                )
                fig.update_traces(textposition='outside') # Coloca o número logo fora da barra
                
                st.plotly_chart(fig, use_container_width=True)

            with dash_col2:
                st.markdown("##### 🔥 ITENS CRÍTICOS COM MAIORES SLAs (>= 20 Dias)")
                st.markdown("Visão detalhada das requisições com maior inércia.")
                
                # Aplicando um estilo na tabela para as células de atraso ficarem vermelhas
                def color_critical(val):
                    color = '#e53e3e' if isinstance(val, int) and val >= 20 else 'black'
                    return f'color: {color}; font-weight: bold'
                
                styled_table = top_critical.style.applymap(
                    color_critical, subset=['Dias em Atraso']
                ).format({"Dias em Atraso": "{} dias"})
                
                st.dataframe(
                    styled_table, 
                    use_container_width=True,
                    height=450,
                    hide_index=True
                )

        except Exception as e:
            st.error(f"⚠️ Ocorreu um erro no processamento do arquivo. \n\nDetalhe técnico: {e}")
