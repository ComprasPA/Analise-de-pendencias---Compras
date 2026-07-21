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
st.title("📊 Gerador de Infográfico - Layout Atualizado")
st.markdown("Faça o upload do arquivo Excel para gerar o panorama com o novo design de cards.")

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
        # Leitura
        df = pd.read_excel(uploaded_file, header=0)
        if 'Numero da SC' not in df.columns:
            new_header = df.iloc[0]
            df = df[1:]
            df.columns = new_header
            
        # Limpeza e cálculos de tempo (SLA)
        hoje = pd.to_datetime(data_base)
        df['DT Emissao'] = pd.to_datetime(df['DT Emissao'], errors='coerce')
        df['Days'] = (hoje - df['DT Emissao']).dt.days
        
        # Indicadores Totais
        unique_scs = df.drop_duplicates(subset=['Numero da SC'])
        total_linhas = len(df) 
        total_sc_unicas = len(unique_scs)
        
        # Indicadores Críticos
        criticos_df = unique_scs[unique_scs['Days'] >= 20]
        backlog_critico = len(criticos_df)
        percentual_critico = (backlog_critico / total_sc_unicas * 100) if total_sc_unicas > 0 else 0
        
        # Volume por Centro de Custo (Top 3 + Outros)
        cc_volume = df.groupby('C Custo').size().reset_index(name='Quantidade').sort_values(by='Quantidade', ascending=False)
        top3_cc = cc_volume.head(3)
        outros_val = cc_volume.iloc[3:]['Quantidade'].sum() if len(cc_volume) > 3 else 0
        
        cc_labels = top3_cc['C Custo'].astype(str).tolist()
        cc_vals = top3_cc['Quantidade'].tolist()
        
        if outros_val > 0:
            cc_labels.append('Outros')
            cc_vals.append(outros_val)
            
        # Top 10 Itens Críticos para a Tabela
        top_critical = criticos_df.sort_values(by='Days', ascending=False)[['Numero da SC', 'C Custo', 'Days']].head(10)

        # ==========================================
        # 3. GERAÇÃO DO INFOGRÁFICO (MATPLOTLIB)
        # ==========================================
        # Fundo cinza azulado claro da imagem de referência
        fig, ax = plt.subplots(figsize=(18, 10), facecolor='#e9eef2')
        ax.axis('off')

        # Paleta de Cores do Novo Design
        text_dark = '#1a202c'
        text_gray = '#4a5568'
        card_bg = 'white'
        border_color = '#cbd5e0'
        blue_highlight = '#2b6cb0'
        red_highlight = '#e53e3e'
        table_header = '#457b9d'

        # --- Cabeçalho ---
        ax.text(0.02, 0.95, 'PANORAMA DE REQUISIÇÕES DE COMPRA PENDENTES', ha='left', va='center', fontsize=26, fontweight='bold', color=text_dark)
        ax.text(0.98, 0.965, f'DADOS CONSOLIDADOS | {hoje.strftime("%d DE %B DE %Y").upper()}', ha='right', va='center', fontsize=12, color=text_dark)
        ax.text(0.98, 0.935, f'FONTE: {uploaded_file.name}', ha='right', va='center', fontsize=10, color=text_gray)
        
        # Linha separadora do cabeçalho
        ax.plot([0.02, 0.98], [0.91, 0.91], color=border_color, lw=2, transform=ax.transAxes)

        # --- Função Auxiliar para Desenhar os Cards ---
        def draw_card(x, y, w, h, edge_color=border_color, left_strip_color=None):
            # Card principal
            card = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01", facecolor=card_bg, edgecolor=edge_color, transform=ax.transAxes, zorder=1)
            ax.add_patch(card)
            # Faixa colorida lateral (opcional)
            if left_strip_color:
                strip = patches.FancyBboxPatch((x, y), 0.005, h, boxstyle="round,pad=0.01", facecolor=left_strip_color, edgecolor='none', transform=ax.transAxes, zorder=2)
                ax.add_patch(strip)

        # ---------------------------------------------------------
        # CARD 1: TOTAL (Topo Esquerda)
        # ---------------------------------------------------------
        draw_card(0.02, 0.70, 0.46, 0.18, left_strip_color=blue_highlight)
        ax.text(0.05, 0.83, 'TOTAL DE REQUISIÇÕES PENDENTES', ha='left', va='center', fontsize=16, color=text_dark)
        
        # Números grandes separados por barra vertical
        ax.text(0.12, 0.75, str(total_sc_unicas), ha='center', va='center', fontsize=48, fontweight='bold', color=text_dark)
        ax.plot([0.22, 0.22], [0.72, 0.78], color=border_color, lw=2, transform=ax.transAxes, zorder=3)
        ax.text(0.32, 0.75, str(total_linhas), ha='center', va='center', fontsize=48, fontweight='bold', color=text_dark)

        # ---------------------------------------------------------
        # CARD 2: CRÍTICO (Topo Direita)
        # ---------------------------------------------------------
        draw_card(0.51, 0.70, 0.47, 0.18, left_strip_color=red_highlight)
        ax.text(0.54, 0.83, 'BACKLOG CRÍTICO (>= 20 dias)', ha='left', va='center', fontsize=16, color=text_dark)
        
        ax.text(0.57, 0.75, str(backlog_critico), ha='center', va='center', fontsize=48, fontweight='bold', color=text_dark)
        ax.text(0.75, 0.73, f'PERCENTUAL DO TOTAL: ~{percentual_critico:.1f}%', ha='center', va='center', fontsize=14, color=text_dark)
        ax.text(0.93, 0.73, 'ALERTA', ha='center', va='center', fontsize=14, fontweight='bold', color=red_highlight)

        # ---------------------------------------------------------
        # CARD 3: GRÁFICO (Base Esquerda)
        # ---------------------------------------------------------
        draw_card(0.02, 0.05, 0.46, 0.61)
        ax.text(0.25, 0.61, 'DISTRIBUIÇÃO POR CENTRO DE CUSTO', ha='center', va='center', fontsize=16, fontweight='bold', color=text_dark)
        ax.text(0.25, 0.58, 'TOP 3 MAIORES PENDÊNCIAS', ha='center', va='center', fontsize=14, color=text_gray)

        ax_bar = fig.add_axes([0.10, 0.10, 0.35, 0.43])
        ax_bar.set_facecolor(card_bg)
        
        # Preparar dados do gráfico (inverter para plotar de cima para baixo)
        bar_labels = cc_labels[::-1]
        bar_vals = cc_vals[::-1]
        bar_colors = ['#f68741', '#f0a04b', '#48b59e', '#4585bb'] # Cores simulando a imagem: Outros, 3º, 2º, 1º
        
        # Ajuste de cores baseado na quantidade de itens (se tiver menos de 4)
        bar_colors = bar_colors[-len(bar_vals):]

        bars = ax_bar.barh(bar_labels, bar_vals, color=bar_colors, height=0.6)
        
        ax_bar.set_ylabel('CENTRO DE CUSTO', fontsize=12, fontweight='bold')
        ax_bar.set_xlabel('QUANTIDADE DE REQUISIÇÕES', fontsize=12)
        ax_bar.spines['top'].set_visible(False)
        ax_bar.spines['right'].set_visible(False)
        ax_bar.spines['left'].set_color(border_color)
        ax_bar.spines['bottom'].set_color(border_color)
        ax_bar.grid(axis='x', linestyle=':', alpha=0.5)

        if bar_vals:
            ax_bar.set_xlim(0, max(bar_vals) * 1.2)
            for bar in bars:
                width = bar.get_width()
                if width > 0:
                    ax_bar.text(width + max(bar_vals)*0.02, bar.get_y() + bar.get_height()/2, f'{int(width)}', va='center', ha='left', fontsize=14, fontweight='bold', color=text_dark)

        # ---------------------------------------------------------
        # CARD 4: TABELA (Base Direita)
        # ---------------------------------------------------------
        draw_card(0.51, 0.05, 0.47, 0.61)
        ax.text(0.745, 0.61, 'DETALHAMENTO DE ITENS CRÍTICOS (>= 20 dias)', ha='center', va='center', fontsize=16, fontweight='bold', color=text_dark)

        ax_tbl = fig.add_axes([0.53, 0.08, 0.43, 0.50])
        ax_tbl.axis('off')
        
        table_data = []
        for _, row in top_critical.iterrows():
            table_data.append([str(row['Numero da SC']), str(row['C Custo']), f"{int(row['Days'])} dias"])
            
        # Preencher linhas para manter tamanho consistente (10 linhas)
        while len(table_data) < 10:
            table_data.append(['-', '-', '-'])

        table = ax_tbl.table(cellText=table_data, colLabels=['Nº DA SC', 'CENTRO DE CUSTO', 'DIAS DE ATRASO'], loc='center', cellLoc='center', bbox=[0, 0, 1, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(13)

        # Estilo dinâmico da tabela para bater com a imagem
        for (row, col), cell in table.get_celld().items():
            if row == 0: 
                cell.set_facecolor(table_header)
                cell.set_text_props(color='white', fontweight='bold')
                cell.set_edgecolor('white')
            else: 
                # Linhas alternadas: branco e cinza ultra claro
                cell.set_facecolor('#f4f7f9' if row % 2 == 0 else 'white')
                cell.set_edgecolor(border_color)
                cell.set_text_props(color=text_dark)

        # ==========================================
        # 4. RENDERIZAÇÃO NO FRONT-END
        # ==========================================
        st.pyplot(fig)
        
        # Botão para Download
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
        st.download_button(label="📥 Baixar Infográfico (PNG)", data=buf.getvalue(), file_name="infografico_painel_atualizado.png", mime="image/png")
        
    except Exception as e:
        st.error(f"Erro ao processar o arquivo. Detalhe técnico: {e}")
