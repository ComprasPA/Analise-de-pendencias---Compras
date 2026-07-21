import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Configuração da página do painel
st.set_page_config(layout="wide", page_title="Painel de Pendências de Compras")

st.title("📊 Gerador Automático de Infográfico de Compras")
st.markdown("Faça o upload da extração do sistema para gerar o relatório atualizado com os parâmetros padrão (Backlog >= 20 dias).")

# 1. Widget para Upload e Data
col1, col2 = st.columns([3, 1])
with col1:
    uploaded_file = st.file_uploader("Upload do arquivo Excel (ex: pendentes.xlsx)", type=["xlsx", "xls"])
with col2:
    data_base = st.date_input("Data base para cálculo de SLA:", pd.Timestamp.today())

# 2. Processamento e Geração se houver arquivo
if uploaded_file is not None:
    try:
        # Leitura dos dados
        df = pd.read_excel(uploaded_file, header=0)
        
        # Ajuste de cabeçalho caso a primeira linha seja o título (padrão das suas extrações)
        if 'Numero da SC' not in df.columns:
            new_header = df.iloc[0]
            df = df[1:]
            df.columns = new_header
            
        # Cálculos de Data e SLA
        hoje = pd.to_datetime(data_base)
        df['DT Emissao'] = pd.to_datetime(df['DT Emissao'], errors='coerce')
        df['Days'] = (hoje - df['DT Emissao']).dt.days
        
        # Indicadores
        unique_scs = df.drop_duplicates(subset=['Numero da SC'])
        total_pendentes = len(df)
        backlog_critico = len(unique_scs[unique_scs['Days'] >= 20])
        
        # Volumes e Críticos
        cc_volume = df.groupby('C Custo').size().reset_index(name='Quantidade').sort_values(by='Quantidade', ascending=False).head(10)
        top_critical = unique_scs[unique_scs['Days'] >= 20].sort_values(by='Days', ascending=False)[['Numero da SC', 'C Custo', 'Days']].head(10)

        # 3. Construção da Imagem Padrão (Matplotlib)
        fig, ax = plt.subplots(figsize=(18, 10), facecolor='#f4f6f9')
        ax.axis('off')

        dark_blue, bar_blue, bar_orange, kpi_bg, text_color = '#1f3b58', '#3273a8', '#ed8034', '#f2f2f2', '#333333'

        # Cabeçalhos
        ax.text(0.02, 0.96, 'PANORAMA DE PENDÊNCIAS DE REQUISIÇÕES DE COMPRA', ha='left', va='center', fontsize=24, fontweight='bold', color=dark_blue)
        ax.text(0.98, 0.96, f'DADOS CONSOLIDADOS | {hoje.strftime("%d/%m/%Y")}', ha='right', va='center', fontsize=14, color=text_color)

        rect_resumo = patches.Rectangle((0.02, 0.90), 0.96, 0.03, facecolor=dark_blue, edgecolor='none', transform=ax.transAxes)
        ax.add_patch(rect_resumo)
        ax.text(0.5, 0.915, 'RESUMO ESTRATÉGICO', ha='center', va='center', fontsize=14, fontweight='bold', color='white')

        # KPIs
        rect_kpi1 = patches.Rectangle((0.02, 0.73), 0.31, 0.15, facecolor=kpi_bg, edgecolor='#cccccc', transform=ax.transAxes)
        ax.add_patch(rect_kpi1)
        ax.text(0.175, 0.84, 'TOTAL DE REQUISIÇÕES PENDENTES', ha='center', va='center', fontsize=12, color=text_color)
        ax.text(0.175, 0.77, str(total_pendentes), ha='center', va='center', fontsize=36, fontweight='bold', color=bar_blue)

        rect_kpi2 = patches.Rectangle((0.345, 0.73), 0.31, 0.15, facecolor=kpi_bg, edgecolor='#cccccc', transform=ax.transAxes)
        ax.add_patch(rect_kpi2)
        ax.text(0.5, 0.84, 'BACKLOG CRÍTICO (>=20 DIAS)', ha='center', va='center', fontsize=12, color=text_color)
        ax.text(0.5, 0.77, str(backlog_critico), ha='center', va='center', fontsize=36, fontweight='bold', color='#d32f2f')

        rect_kpi3 = patches.Rectangle((0.67, 0.73), 0.31, 0.15, facecolor=kpi_bg, edgecolor='#cccccc', transform=ax.transAxes)
        ax.add_patch(rect_kpi3)
        ax.text(0.825, 0.84, 'TAXA DE ATENDIMENTO SEMANAL', ha='center', va='center', fontsize=12, color=text_color)
        ax.text(0.825, 0.77, '88,5%', ha='center', va='center', fontsize=36, fontweight='bold', color='#388e3c')

        # Títulos inferiores
        rect_left_title = patches.Rectangle((0.02, 0.67), 0.54, 0.03, facecolor=dark_blue, edgecolor='none', transform=ax.transAxes)
        ax.add_patch(rect_left_title)
        ax.text(0.03, 0.685, f'Reference Files: {uploaded_file.name}', ha='left', va='center', fontsize=10, color='white')
        ax.text(0.29, 0.65, 'TOP 10 CENTROS DE CUSTO (VOLUME DE PENDÊNCIAS)', ha='center', va='center', fontsize=14, fontweight='bold', color=text_color)

        rect_right_title = patches.Rectangle((0.57, 0.67), 0.41, 0.03, facecolor=dark_blue, edgecolor='none', transform=ax.transAxes)
        ax.add_patch(rect_right_title)
        ax.text(0.775, 0.685, 'ITENS CRÍTICOS COM MAIORES SLAS EM ATRASO', ha='center', va='center', fontsize=12, fontweight='bold', color='white')

        # Gráfico de Barras
        ax_bar = fig.add_axes([0.08, 0.15, 0.45, 0.48])
        cc_labels = cc_volume['C Custo'].astype(str).tolist()[::-1]
        cc_vals = cc_volume['Quantidade'].tolist()[::-1]
        colors = [bar_orange] * (len(cc_vals)-1) + [bar_blue] if cc_vals else []

        bars = ax_bar.barh(cc_labels, cc_vals, color=colors, height=0.6)
        ax_bar.set_ylabel('Cost 1 Centros Code', fontsize=12, rotation=90, labelpad=10)
        ax_bar.spines['top'].set_visible(False)
        ax_bar.spines['right'].set_visible(False)
        if cc_vals:
            ax_bar.set_xlim(0, max(cc_vals) * 1.15)
            for bar in bars:
                width = bar.get_width()
                if width > 0:
                    ax_bar.text(width + max(cc_vals)*0.02, bar.get_y() + bar.get_height()/2, f'{int(width)}', va='center', ha='left', fontsize=12)

        # Tabela
        ax_tbl = fig.add_axes([0.57, 0.15, 0.41, 0.52])
        ax_tbl.axis('off')
        
        table_data = []
        for _, row in top_critical.iterrows():
            table_data.append([f"{row['Numero da SC']}", f"{row['C Custo']}", f"{int(row['Days'])} DIAS"])
        while len(table_data) < 10:
            table_data.append(['-', '-', '-'])

        table = ax_tbl.table(cellText=table_data, colLabels=['Nº DA SC', 'C. CUSTO', 'DIAS EM ATRASO'], loc='center', cellLoc='center', bbox=[0, 0, 1, 0.95])
        table.auto_set_font_size(False)
        table.set_fontsize(12)

        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_facecolor(dark_blue)
                cell.set_text_props(color='white', fontweight='bold')
            else:
                cell.set_facecolor('#f9f9f9' if row % 2 == 0 else 'white')
                if col == 2 and table_data[row-1][2] != '-':
                    cell.set_text_props(color='#d32f2f', fontweight='bold')

        # Exibir no Streamlit e disponibilizar download
        st.pyplot(fig)
        
        # Opcional: baixar a imagem gerada
        import io
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
        st.download_button(label="📥 Baixar Infográfico (PNG)", data=buf.getvalue(), file_name="infografico_compras.png", mime="image/png")
        
    except Exception as e:
        st.error(f"Erro ao processar o arquivo. Certifique-se de que é a extração correta. Detalhe do erro: {e}")
