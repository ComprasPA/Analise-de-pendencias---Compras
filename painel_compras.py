import streamlit as st
import datetime

# 1. CONFIGURAÇÃO BÁSICA (Única coisa que carrega no início)
st.set_page_config(layout="wide", page_title="Painel de Compras")

# ==========================================
# INTERFACE DO USUÁRIO
# ==========================================
st.title("📊 Gerador de Infográfico - Layout Atualizado")
st.markdown("Faça o upload do arquivo Excel e clique no botão para gerar o panorama.")

col1, col2 = st.columns([3, 1])
with col1:
    uploaded_file = st.file_uploader("Upload do arquivo de pendências", type=["xlsx", "xls"])
with col2:
    data_base = st.date_input("Data base para cálculo de SLA:", datetime.date.today())

# ==========================================
# CONTROLE DO BOTÃO
# ==========================================
if 'gerar_grafico' not in st.session_state:
    st.session_state['gerar_grafico'] = False

if st.button("🚀 Gerar Infográfico", type="primary"):
    if uploaded_file is not None:
        st.session_state['gerar_grafico'] = True
    else:
        st.warning("⚠️ Por favor, faça o upload do arquivo antes de gerar o infográfico.")

if uploaded_file is None:
    st.session_state['gerar_grafico'] = False

# ==========================================
# PROCESSAMENTO DE DADOS (Só roda ao clicar)
# ==========================================
if st.session_state['gerar_grafico'] and uploaded_file is not None:
    with st.spinner('Processando dados e gerando infográfico...'):
        try:
            # Importações "atrasadas" para não quebrar o site na inicialização
            import pandas as pd
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
            import io
            from PIL import Image
            
            # Destrava limite de imagem
            Image.MAX_IMAGE_PIXELS = None

            # Leitura do Arquivo
            df = pd.read_excel(uploaded_file, header=0)
            if 'Numero da SC' not in df.columns:
                new_header = df.iloc[0]
                df = df[1:]
                df.columns = new_header
                
            hoje = pd.to_datetime(data_base)
            df['DT Emissao'] = pd.to_datetime(df['DT Emissao'], errors='coerce')
            df['Days'] = (hoje - df['DT Emissao']).dt.days
            
            unique_scs = df.drop_duplicates(subset=['Numero da SC'])
            total_linhas = len(df) 
            total_sc_unicas = len(unique_scs)
            
            criticos_df = unique_scs[unique_scs['Days'] >= 20]
            backlog_critico = len(criticos_df)
            percentual_critico = (backlog_critico / total_sc_unicas * 100) if total_sc_unicas > 0 else 0
            
            cc_volume = df.groupby('C Custo').size().reset_index(name='Quantidade').sort_values(by='Quantidade', ascending=False)
            top3_cc = cc_volume.head(3)
            outros_val = cc_volume.iloc[3:]['Quantidade'].sum() if len(cc_volume) > 3 else 0
            
            cc_labels = top3_cc['C Custo'].astype(str).tolist()
            cc_vals = top3_cc['Quantidade'].tolist()
            
            if outros_val > 0:
                cc_labels.append('Outros')
                cc_vals.append(outros_val)
                
            top_critical = criticos_df.sort_values(by='Days', ascending=False)[['Numero da SC', 'C Custo', 'Days']].head(10)

            # ==========================================
            # GERAÇÃO DO INFOGRÁFICO
            # ==========================================
            fig, ax = plt.subplots(figsize=(18, 10), facecolor='#e9eef2')
            ax.axis('off')

            text_dark, text_gray, card_bg, border_color = '#1a202c', '#4a5568', 'white', '#cbd5e0'
            blue_highlight, red_highlight, table_header = '#2b6cb0', '#e53e3e', '#457b9d'

            ax.text(0.02, 0.95, 'PANORAMA DE REQUISIÇÕES DE COMPRA PENDENTES', ha='left', va='center', fontsize=26, fontweight='bold', color=text_dark)
            ax.text(0.98, 0.965, f'DADOS CONSOLIDADOS | {hoje.strftime("%d DE %B DE %Y").upper()}', ha='right', va='center', fontsize=12, color=text_dark)
            ax.text(0.98, 0.935, f'FONTE: {uploaded_file.name}', ha='right', va='center', fontsize=10, color=text_gray)
            ax.plot([0.02, 0.98], [0.91, 0.91], color=border_color, lw=2, transform=ax.transAxes)

            def draw_card(x, y, w, h, edge_color=border_color, left_strip_color=None):
                card = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01", facecolor=card_bg, edgecolor=edge_color, transform=ax.transAxes, zorder=1)
                ax.add_patch(card)
                if left_strip_color:
                    strip = patches.FancyBboxPatch((x, y), 0.005, h, boxstyle="round,pad=0.01", facecolor=left_strip_color, edgecolor='none', transform=ax.transAxes, zorder=2)
                    ax.add_patch(strip)

            # CARDS SUPERIORES
            draw_card(0.02, 0.70, 0.46, 0.18, left_strip_color=blue_highlight)
            ax.text(0.05, 0.83, 'TOTAL DE REQUISIÇÕES PENDENTES', ha='left', va='center', fontsize=16, color=text_dark)
            ax.text(0.12, 0.75, str(total_sc_unicas), ha='center', va='center', fontsize=48, fontweight='bold', color=text_dark)
            ax.plot([0.22, 0.22], [0.72, 0.78], color=border_color, lw=2, transform=ax.transAxes, zorder=3)
            ax.text(0.32, 0.75, str(total_linhas), ha='center', va='center', fontsize=48, fontweight='bold', color=text_dark)

            draw_card(0.51, 0.70, 0.47, 0.18, left_strip_color=red_highlight)
            ax.text(0.54, 0.83, 'BACKLOG CRÍTICO (>= 20 dias)', ha='left', va='center', fontsize=16, color=text_dark)
            ax.text(0.57, 0.75, str(backlog_critico), ha='center', va='center', fontsize=48, fontweight='bold', color=text_dark)
            ax.text(0.75, 0.73, f'PERCENTUAL DO TOTAL: ~{percentual_critico:.1f}%', ha='center', va='center', fontsize=14, color=text_dark)
            ax.text(0.93, 0.73, 'ALERTA', ha='center', va='center', fontsize=14, fontweight='bold', color=red_highlight)

            # GRÁFICO LATERAL
            draw_card(0.02, 0.05, 0.46, 0.61)
            ax.text(0.25, 0.61, 'DISTRIBUIÇÃO POR CENTRO DE CUSTO', ha='center', va='center', fontsize=16, fontweight='bold', color=text_dark)
            ax.text(0.25, 0.58, 'TOP 3 MAIORES PENDÊNCIAS', ha='center', va='center', fontsize=14, color=text_gray)

            ax_bar = fig.add_axes([0.10, 0.10, 0.35, 0.43])
            ax_bar.set_facecolor(card_bg)
            
            bar_labels = cc_labels[::-1]
            bar_vals = cc_vals[::-1]
            bar_colors = ['#f68741', '#f0a04b', '#48b59e', '#4585bb'] 
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

            # TABELA
            draw_card(0.51, 0.05, 0.47, 0.61)
            ax.text(0.745, 0.61, 'DETALHAMENTO DE ITENS CRÍTICOS (>= 20 dias)', ha='center', va='center', fontsize=16, fontweight='bold', color=text_dark)

            ax_tbl = fig.add_axes([0.53, 0.08, 0.43, 0.50])
            ax_tbl.axis('off')
            
            table_data = []
            for _, row in top_critical.iterrows():
                table_data.append([str(row['Numero da SC']), str(row['C Custo']), f"{int(row['Days'])} dias"])
                
            while len(table_data) < 10:
                table_data.append(['-', '-', '-'])

            table = ax_tbl.table(cellText=table_data, colLabels=['Nº DA SC', 'CENTRO DE CUSTO', 'DIAS DE ATRASO'], loc='center', cellLoc='center', bbox=[0, 0, 1, 1])
            table.auto_set_font_size(False)
            table.set_fontsize(13)

            for (row, col), cell in table.get_celld().items():
                if row == 0: 
                    cell.set_facecolor(table_header)
                    cell.set_text_props(color='white', fontweight='bold')
                    cell.set_edgecolor('white')
                else: 
                    cell.set_facecolor('#f4f7f9' if row % 2 == 0 else 'white')
                    cell.set_edgecolor(border_color)
                    cell.set_text_props(color=text_dark)

            st.pyplot(fig)
            
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=200)
            st.download_button(label="📥 Baixar Infográfico (PNG)", data=buf.getvalue(), file_name="infografico_painel_atualizado.png", mime="image/png")
            
        except ImportError as e:
            st.error(f"⚠️ Erro de Instalação: O servidor não conseguiu encontrar as bibliotecas.\n\nDetalhe: {e}")
            st.warning("Verifique se o seu arquivo `requirements.txt` no GitHub está com este exato conteúdo (tudo minúsculo):\n\n`streamlit`\n`pandas`\n`matplotlib`\n`openpyxl`\n`pillow`")
        except Exception as e:
            st.error(f"⚠️ Erro ao processar a planilha. Detalhe técnico: {e}")
