import streamlit as st
import pandas as pd
import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Painel de Compras")

# ==========================================
# INTERFACE DO USUÁRIO
# ==========================================
st.title("📊 Painel Interativo de Requisições de Compra")
st.markdown("Faça o upload do arquivo Excel para visualizar o panorama consolidado diretamente na tela.")

col1, col2 = st.columns([3, 1])
with col1:
    uploaded_file = st.file_uploader("Upload do arquivo de pendências", type=["xlsx", "xls", "csv"])
with col2:
    data_base = st.date_input("Data base para cálculo de SLA:", datetime.date.today())

# ==========================================
# PROCESSAMENTO E EXIBIÇÃO EM TELA
# ==========================================
if uploaded_file is not None:
    with st.spinner('Processando dados e montando o painel...'):
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
                
            # 2. Cálculos de SLA e Limpeza
            hoje = pd.to_datetime(data_base)
            df['DT Emissao'] = pd.to_datetime(df['DT Emissao'], errors='coerce')
            df['Days'] = (hoje - df['DT Emissao']).dt.days
            
            unique_scs = df.drop_duplicates(subset=['Numero da SC'])
            total_linhas = len(df) 
            total_sc_unicas = len(unique_scs)
            
            criticos_df = unique_scs[unique_scs['Days'] >= 20]
            backlog_critico = len(criticos_df)
            percentual_critico = (backlog_critico / total_sc_unicas * 100) if total_sc_unicas > 0 else 0
            
            # 3. Preparação dos Dados para o Gráfico
            cc_volume = df.groupby('C Custo').size().reset_index(name='Quantidade').sort_values(by='Quantidade', ascending=False)
            top3_cc = cc_volume.head(3)
            outros_val = cc_volume.iloc[3:]['Quantidade'].sum() if len(cc_volume) > 3 else 0
            
            chart_data = top3_cc.copy()
            if outros_val > 0:
                outros_df = pd.DataFrame({'C Custo': ['Outros'], 'Quantidade': [outros_val]})
                chart_data = pd.concat([chart_data, outros_df], ignore_index=True)
            
            # Formata os dados para o st.bar_chart nativo
            chart_data['C Custo'] = chart_data['C Custo'].astype(str)
            chart_data_plot = chart_data.set_index('C Custo')
            
            # 4. Preparação dos Dados para a Tabela
            top_critical = criticos_df.sort_values(by='Days', ascending=False)[['Numero da SC', 'C Custo', 'Days']].head(10)
            top_critical.columns = ['Nº da SC', 'Centro de Custo', 'Dias de Atraso']

            # ==========================================
            # RENDERIZAÇÃO NA TELA DO SITE
            # ==========================================
            st.divider() # Linha separadora
            st.subheader(f"📌 DADOS CONSOLIDADOS | {hoje.strftime('%d/%m/%Y')}")
            
            # --- CARDS DE INDICADORES (KPIs) ---
            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1:
                st.metric(label="Total de Requisições (Únicas)", value=total_sc_unicas, delta=f"{total_linhas} linhas/itens no total", delta_color="off")
            with kpi2:
                # Delta negativo em vermelho automático no Streamlit se configurado
                st.metric(label="Backlog Crítico (>= 20 dias)", value=backlog_critico, delta=f"Representa ~{percentual_critico:.1f}% do total", delta_color="inverse")
            with kpi3:
                alerta = "ALERTA ATIVO 🔴" if backlog_critico > 0 else "NORMAL 🟢"
                st.metric(label="Status de Atraso", value=alerta)

            st.divider()

            # --- GRÁFICO E TABELA LADO A LADO ---
            col_chart, col_table = st.columns(2)
            
            with col_chart:
                st.markdown("### 📊 Top 3 Maiores Pendências")
                st.markdown("Distribuição por Centro de Custo")
                # Gráfico nativo do Streamlit (Interativo, você pode passar o mouse em cima)
                st.bar_chart(chart_data_plot, use_container_width=True)

            with col_table:
                st.markdown("### ⚠️ Detalhamento de Itens Críticos")
                st.markdown("Top 10 Itens com SLA >= 20 dias")
                # Tabela nativa do Streamlit
                st.dataframe(top_critical, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"⚠️ Erro ao processar a planilha. \n\nDetalhe técnico: {e}")
