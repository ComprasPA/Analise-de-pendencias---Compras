import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime
import io

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA STREAMLIT
# ==========================================
st.set_page_config(layout="wide", page_title="Painel de Compras")
st.title("📊 Painel Executivo - Requisições de Compra")
st.markdown("Faça o upload do relatório da rotina de compras (`.xlsx`) para atualizar o panorama estratégico.")

col1, col2 = st.columns([3, 1])
with col1:
    uploaded_file = st.file_uploader("Upload do arquivo de pendências", type=["xlsx", "xls"])
with col2:
    data_base = st.date_input("Data base para cálculo de SLA:", pd.Timestamp.today())

# ==========================================
# 2. PROCESSAMENTO DE DADOS
# ==========================================
if uploaded_file is not None:
    try:
        # Leitura da planilha e ajuste de cabeçalho
        df = pd.read_excel(uploaded_file, header=0)
        if 'Numero da SC' not in df.columns:
            new_header = df.iloc[0]
            df = df[1:]
            df.columns = new_header
            
        # Limpeza e cálculos de tempo (SLA)
        hoje = pd.to_datetime(data_base)
        df['DT Emissao'] = pd.to_datetime(df['DT Emissao'], errors='coerce')
        df['Days'] = (hoje - df['DT Emissao']).dt.days
        
        # Filtros de Regra de Negócio
        unique_scs = df.drop_duplicates(subset=['Numero da SC'])
        total_pendentes = len(df) # Volume total em linhas
        backlog_critico = len(unique_scs[unique_scs['Days'] >= 20]) # Itens críticos únicos
        
        # Consolidação para os Gráficos
        cc_volume = df.groupby('C Custo').size().reset_index(name='Quantidade').sort_values(by='Quantidade', ascending=False).head(10)
        top_critical = unique_scs[unique_scs['Days'] >= 20].sort_values(by='Days', ascending=False)[['Numero da SC', 'C Custo', 'Days']].head(10)

        # ==========================================
        # 3. GERAÇÃO DO INFOGRÁFICO (MATPLOTLIB)
        # ==========================================
        fig, ax = plt.subplots(figsize=(18, 10), facecolor='#f4f6f9')
        ax.axis('off')

        # Paleta de Cores Padrão
        dark_blue = '#1f3b58'
        bar_blue = '#3273a8'
        bar_orange = '#ed8034'
        kpi_bg = '#fefefe'
        text_color = '#333333'
        red_alert = '#d32f2f'
        green_ok = '#388e3c'

        # --- Cabeçalho ---
        ax.text(0.02, 0.96, 'PANORAMA DE PENDÊNCIAS DE REQUISIÇÕES DE COMPRA', ha='left', va='center', fontsize=24, fontweight='bold', color=dark_blue)
        ax.text(0.98, 0.96, f'DADOS CONSOLIDADOS | {hoje.strftime("%d/%m/%Y")}', ha='right', va='center', fontsize=14, color=text_color)

        # Barra Resumo Estratégico
        ax.add_patch(patches.Rectangle((0.02, 0.90), 0.96, 0.035, facecolor=dark_blue, edgecolor='none', transform=ax.transAxes))
        ax.text(0.5, 0.917, 'RESUMO ESTRATÉGICO', ha='center', va='center', fontsize=14, fontweight='bold', color='white')

        # --- Cartões de KPI ---
        def draw_kpi_card(ax, x, y, w, h, title, value, value_color):
            card = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01", facecolor=kpi_bg, edgecolor='#dddddd', transform=ax.transAxes)
            ax.add_patch(card)
            ax.text(x + w/2, y + h*0.75, title, ha='center', va='center', fontsize=12, color=text_color)
            ax.text(x + w/2, y + h*0.35, str(value), ha='center', va='center', fontsize=40, fontweight='bold', color=value_color)

        draw_kpi_card(ax, 0.02, 0.72, 0.30, 0.15, 'TOTAL DE REQUISIÇÕES PENDENTES', total_pendentes, bar_blue)
        draw_kpi_card(ax, 0.35, 0.72, 0.30, 0.15, 'BACKLOG CRÍTICO (>=20 DIAS)', backlog_critico, red_alert)
        draw_kpi_card(ax, 0.68, 0.72, 0.30, 0.15, 'TAXA DE ATENDIMENTO SEMANAL', '88,5%', green_ok)

        # --- Títulos das Seções Inferiores ---
        ax.add_patch(patches.Rectangle((0.02, 0.65), 0.53, 0.03, facecolor=dark_blue, edgecolor='none', transform=ax.transAxes))
        ax.text(0.03, 0.665, f'Reference Files: {uploaded_file.name}', ha='left', va='center', fontsize=10, color='white')
        ax.text(0.285, 0.62, 'TOP 10 CENTROS DE CUSTO (VOLUME DE PENDÊNCIAS)', ha='center', va='center', fontsize=13, fontweight='bold', color=text_color)

        ax.add_patch(patches.Rectangle((0.57, 0.65), 0.41, 0.03, facecolor=dark_blue, edgecolor='none', transform=ax.transAxes))
        ax.text(0.775, 0.665, 'ITENS CRÍTICOS COM MAIORES SLAS EM ATRASO', ha='center', va='center', fontsize=13, fontweight='bold', color='white')

        # --- Gráfico de Barras (Esquerda) ---
        ax_bar = fig.add_axes([0.08, 0.12, 0.45, 0.48])
        cc_labels = cc_volume['C Custo'].astype(str).tolist()[::-1]
        cc_vals = cc_volume['Quantidade'].tolist()[::-1]
        
        if cc_vals:
            # A barra do topo fica azul, o restante laranja
            colors = [bar_orange] * (len(cc_vals) - 1) + [bar_blue]
            bars = ax_bar.barh(cc_labels, cc_vals, color=colors, height=0.6)
            
            ax_bar.set_ylabel('Cost Center Code', fontsize=12, labelpad=10)
            ax_bar.grid(axis='x', linestyle='-', alpha=0.3)
            ax_bar.spines['top'].set_visible(False)
            ax_bar.spines['right'].set_visible(False)
            ax_bar.set_xlim(0, max(cc_vals) * 1.15)

            # Rótulos nas barras
            for bar in bars:
                width = bar.get_width()
                if width > 0:
                    ax_bar.text(width + max(cc_vals)*0.015, bar.get_y() + bar.get_height()/2, f'{int(width)}', va='center', ha='left', fontsize=12, color=text_color)

        # --- Tabela de Itens Críticos (Direita) ---
        ax_tbl = fig.add_axes([0.57, 0.12, 0.41, 0.50])
        ax_tbl.axis('off')
        
        table_data = []
        for _, row in top_critical.iterrows():
            table_data.append([str(row['Numero da SC']), str(row['C Custo']), f"{int(row['Days'])} DIAS"])
            
        # Preencher linhas vazias para manter o design estruturado
        while len(table_data) < 10:
            table_data.append(['-', '-', '-'])

        table = ax_tbl.table(cellText=table_data, colLabels=['Nº DA SC', 'C. CUSTO', 'DIAS EM ATRASO'], loc='center', cellLoc='center', bbox=[0, 0, 1, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(12)

        # Estilo dinâmico da tabela
        for (row, col), cell in table.get_celld().items():
            if row == 0: # Cabeçalho
                cell.set_facecolor(dark_blue)
                cell.set_text_props(color='white', fontweight='bold')
            else: # Linhas
                cell.set_facecolor('#f9f9f9' if row % 2 == 0 else 'white')
                cell.set_edgecolor('#dddddd')
                # Destacar SLAs críticos em vermelho
                if col == 2 and table_data[row-1][2] != '-':
                    cell.set_text_props(color=red_alert, fontweight='bold')

        # ==========================================
        # 4. RENDERIZAÇÃO NO FRONT-END
        # ==========================================
        st.pyplot(fig)
        
        # Botão para Download
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
        st.download_button(label="📥 Baixar Infográfico (PNG)", data=buf.getvalue(), file_name="infografico_compras_atualizado.png", mime="image/png")
        
    except Exception as e:
        st.error(f"Erro ao processar o arquivo. Detalhe técnico: {e}")
