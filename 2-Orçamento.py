import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder
from PIL import Image
import plotly.graph_objects as go
import locale
from io import BytesIO
import os
import time
# Importar a biblioteca para os ícones
from streamlit_option_menu import option_menu
from openpyxl import load_workbook


# Cores
VERDE_PETROBRAS = "#00a651"
AMARELO_PETROBRAS = "#ffd200"


# Configuração de localidade
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Configuração da página
st.set_page_config(
    page_title="Ferramenta de Orçamentação",  # Título da aba
    page_icon="petrobras_icone.png",          # Caminho para o novo ícone
    layout="wide"                            # Outras configurações
)

# Fazer Orçamento
def orcamento():

   # Obtém o diretório atual do script
diretorio_atual = os.path.dirname(__file__)
# Define o caminho relativo para o arquivo Excel
caminho_base_bens = os.path.join(diretorio_atual, 'Base de Bens Inteira - Copia.xlsx')

# Carrega o arquivo Excel
df = pd.read_excel(caminho_base_bens)

    # Iniciar sessão com a base de bens para melhora de performance
    if 'base_bens' not in st.session_state:
        st.session_state.base_bens = pd.read_excel(caminho_base_bens)

    # Função para exibir o cabeçalho e logo
    def display_header():
        logo_image = Image.open("petro-logo.png")
        st.image(logo_image, width=350)

    # Função para carregar dados a partir do upload
    def load_uploaded_data(uploaded_file):
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith((".xls", ".xlsx")):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Formato de arquivo não suportado. Use apenas arquivos CSV ou Excel.")
            return None
        return df
    
    # Função para gerar o arquivo Excel
    def criar_excel():
        with BytesIO() as excel_buffer:
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                dados_orc.to_excel(writer, sheet_name="Informações Gerais", index=False)
                premissas.to_excel(writer, sheet_name='Premissas', index=False)
                itens.to_excel(writer, sheet_name="Itens", index=False)
                subitens.to_excel(writer, sheet_name="Referências", index=False)
                categorias.to_excel(writer, sheet_name="Categorias", index=False)
            
            # Retornar o arquivo Excel como bytes
            excel_buffer.seek(0)
            return excel_buffer.getvalue()
        

    # Função para reiniciar a sessão
    def reset_session():
        for key in list(st.session_state.keys()):
            del st.session_state[key]


    # Função para exibir a tabela com os dados e aplicar filtros
    def display_filtered_data(data, search_column, search_query):
        if search_query:
            data = data[data[search_column].astype(str).str.contains(search_query, case=False, na=False)]
        gb = GridOptionsBuilder.from_dataframe(data)
        gb.configure_pagination(paginationPageSize=100)
        gb.configure_default_column(editable=True)
        grid_options = gb.build()
        AgGrid(data, gridOptions=grid_options, height=2200, fit_columns_on_grid_load=False)

    

    # Tela de Revisões do Orçamento
    def display_input_budget(dados_orc):
        uploaded_file_name = uploaded_file.name
        uploaded_file_name = os.path.splitext(uploaded_file_name)[0]
        st.subheader(f"Orçamento : {uploaded_file_name}")
        dados_orc = pd.read_excel(uploaded_file, sheet_name='Informações Gerais')
        premissas = pd.read_excel(uploaded_file, sheet_name='Premissas')
        itens = pd.read_excel(uploaded_file, sheet_name='Itens')
        subitens = pd.read_excel(uploaded_file, sheet_name='Referências')
        categorias = pd.read_excel(uploaded_file, sheet_name='Categorias')
        if 'dados_orc' not in st.session_state:
            st.session_state.dados_orc = dados_orc

        general_information = st.radio("Selecione a opção:", ['Detalhes', 'Editar', 'Nova Revisão'], horizontal=True)
        if dados_orc['Data Base'].notna().any():    # Colocar coluna Data Base no formato string yyyy-mm-dd
            dados_orc['Data Base'] = pd.to_datetime(dados_orc['Data Base'], errors='coerce').dt.strftime('%d-%m-%Y')

        if general_information == 'Detalhes':
            #dados_reset = dados_orc.reset_index(drop=True)
            st.dataframe(st.session_state.dados_orc, hide_index=True)
        
        if general_information == 'Nova Revisão':
            st.write(f'### {uploaded_file_name}')
            col1, col2 = st.columns(2)
            with col1:
                revisao_existente = dados_orc['Revisão'].unique()
                col_revisao = st.selectbox('Revisão:', ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J'])
                rev_duplicado = col_revisao in revisao_existente
                if rev_duplicado:
                    st.error("Revisão já foi utilizada neste orçamento, favor verificar.")
            with col2:
                col_cliente = st.text_input('Cliente:')
            col6, col7 = st.columns(2)
            with col6:
                col_dem_tec = st.text_input('Demandante Técnico:')
            with col7:
                col_data_base = st.date_input('Data Base:', format='DD/MM/YYYY')
                col_data_base = col_data_base.strftime('%d-%m-%Y')
            col8, col9 = st.columns(2)
            with col8:
                col_moeda = st.selectbox('Moeda:', ['BRL', 'EUR', 'USD'])
            with col9:
                new_data = {'Pedido': uploaded_file_name,
                            'Revisão': col_revisao,
                            'Cliente': col_cliente,
                            'Demandante Técnico': col_dem_tec,
                            'Data Base': col_data_base,
                            'Moeda': col_moeda}
            if st.button('Inserir Informações Gerais'):
                new_row = pd.DataFrame([new_data])
                dados_orc = pd.concat([dados_orc, new_row], ignore_index=True)
                st.success("Item adicionado com sucesso!")                           
                st.dataframe(dados_orc, hide_index=True)

        # Botão excel_buffer = BytesIO()
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            st.session_state.dados_orc.to_excel(writer, index=False, sheet_name='Informações Gerais')
            premissas.to_excel(writer, index=False, sheet_name='Premissas')
            itens.to_excel(writer, index=False, sheet_name='Itens')
            subitens.to_excel(writer, index=False, sheet_name='Referências')
            categorias.to_excel(writer, index=False, sheet_name='Categorias')

    # Definir o ponteiro do arquivo para o início
        st.download_button(
            label= 'Salvar Alterações no Excel',
            data= excel_buffer,
            file_name= uploaded_file.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


    def moeda_orcamento():
        moeda = st.text_input('', st.session_state.dados_orc['Moeda'].iloc[-1])
        st.session_state.dados_orc['Moeda'].iloc[-1] = moeda

    def formatar_valores(valor):
        return f"{valor:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")


    # Função para realizar CRUD na seção "Orçamento"
    def display_crud_in_header(itens):
        #st.write("### Gerenciamento de Dados")
        dados_orc = pd.read_excel(uploaded_file, sheet_name='Informações Gerais')
        premissas = pd.read_excel(uploaded_file, sheet_name='Premissas')
        itens = pd.read_excel(uploaded_file, sheet_name='Itens')
        subitens = pd.read_excel(uploaded_file, sheet_name='Referências')
        categorias = pd.read_excel(uploaded_file, sheet_name='Categorias')
        if 'dados_orc' not in st.session_state:
            st.session_state.dados_orc = dados_orc
        if 'itens' not in st.session_state:
            st.session_state.itens = itens  # Inicializa a lista de itens no estado da sessão
        if 'subitens' not in st.session_state:
            st.session_state.subitens = subitens   # Inicializa a lista de subitens no estado da sessão
        if 'categoria' not in st.session_state:
            st.session_state.categoria = categorias #pd.DataFrame(itens['Categoria'].unique(), columns=['Categoria'])  # Inicializa a lista de categorias no estado da sessão
        #st.session_state.categoria

        
        st.write("### Itens do Orçamento")


        # Caixa st.dialog para confirmar exclusão da Categoria selecionada
        @st.dialog("Deletar", width='small')
        def delete_category(categoria):
            st.warning(f"Ao deletar a categoria {categoria}, todos os itens inseridos na mesma categoria serão deletados.")
            st.write('Deseja continuar?')
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                # Botão para continuar com a exclusão da categoria
                if st.button("Continuar"):
                    st.session_state.categoria = st.session_state.categoria[st.session_state.categoria['Categoria'] != categoria]
                    # Deleta também os itens que foram inseridos na categoria deletada.
                    st.session_state.itens = st.session_state.itens[st.session_state.itens['Categoria'] != categoria]
                    st.write("Deletado! :white_check_mark:")
                    time.sleep(1)
                    st.rerun()
            with col2:
                # Botão para cancelar a exclusão da categoria e voltar para a página anterior
                if st.button("Voltar"):
                    st.rerun()

        # Caixa st.dialog para confirmar duplicata da Categoria selecionada
        @st.dialog("Duplicar", width='small')
        def duplicate_category(categoria):
            name_duplicate =  f"{categoria} Duplicata"
            # Fórmula para verificar se a categoria já foi duplicada.
            rep_categoria = (st.session_state.categoria['Categoria'] == name_duplicate).sum()
            # Se sim, retorna erro e não permite duplicar a categoria.
            if rep_categoria > 0:
                st.error(f"Esta categoria já foi duplicada, para duplica-lá novamente, edite o nome da categoria {name_duplicate}.")
                if st.button("Voltar", key='duplicate_error'):
                    st.rerun()
            # Se não, permite duplicar a categoria.
            else:
                st.warning(f"Ao duplicar a categoria {categoria}, todos os itens inseridos na mesma categoria também serão duplicados.")
                st.write('Deseja continuar?')
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    # Botão para continuar com a exclusão da categoria
                    if st.button("Continuar", key='duplicate'):
                        duplicate = {'Categoria': name_duplicate}
                        max_id = st.session_state.itens['ID'].max()
                        st.session_state.categoria = pd.concat([st.session_state.categoria, pd.DataFrame([duplicate])], ignore_index=True)
                        # Deleta também os itens que foram inseridos na categoria deletada.
                        #st.session_state.itens = st.session_state.itens[st.session_state.itens['Categoria'] != categoria]
                        itens_cat_duplicate = st.session_state.itens[st.session_state.itens['Categoria'] == categoria]# = name_duplicate
                        itens_duplicate = itens_cat_duplicate.copy()
                        itens_duplicate['Categoria'] = name_duplicate
                        itens_duplicate['ID'] = range(max_id + 1, max_id + len(itens_cat_duplicate) + 1)
                        st.session_state.itens = pd.concat([st.session_state.itens, itens_duplicate], ignore_index=True)
                        st.write("Duplicado! :white_check_mark:")
                        time.sleep(1)
                        st.rerun()
                with col2:
                    # Botão para cancelar a exclusão da categoria e voltar para a página anterior
                    if st.button("Voltar", key='not_duplicate'):
                        st.rerun()
            
        # Caixa st.dialog para confirmar edição da Categoria selecionada para outra categoria existente
        @st.dialog("Editar", width='small')
        def edit_category(antiga_categoria, nova_categoria):
            st.warning(f"Categoria {nova_categoria} já exite! Se continuar os itens da Categoria {antiga_categoria} irão para a categoria {nova_categoria}.")
            st.write('Deseja continuar?')
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("Continuar", key='edit_category'):
                    st.session_state.categoria = st.session_state.categoria[st.session_state.categoria['Categoria'] != antiga_categoria]
                    st.session_state.itens.loc[st.session_state.itens['Categoria'] == antiga_categoria, 'Categoria'] = nova_categoria
                    st.write("Editado! :white_check_mark:")
                    time.sleep(1)
                    st.rerun()
            with col2:
                if st.button("Voltar", key='not_edit_category'):
                    st.rerun()

        # Botão st.pupover "Categorias" dos itens do orçamento
        with st.popover("Categoria"):
            if st.session_state.itens.empty:
                category = st.radio('', ['Nova Categoria', 'Editar', 'Deletar'], horizontal=True)
            else:
                category = st.radio('', ['Nova Categoria', 'Editar', 'Deletar', 'Duplicar'], horizontal=True)

            # Inserir nova categoria
            if category == 'Nova Categoria':
                nome_categoria = st.text_input("Nome da Categoria")
                rep_categoria = (st.session_state.categoria['Categoria'] == nome_categoria).sum()
                if st.button("Adicionar"):
                    if rep_categoria > 0:
                        st.error(f"Categoria {nome_categoria} já existe, favor inserir nova categoria.")
                    else:
                        col_categoria = {'Categoria': nome_categoria}
                        st.session_state.categoria = pd.concat([st.session_state.categoria, pd.DataFrame([col_categoria])], ignore_index=True)
                        st.success(f"Categoria {nome_categoria} adicionada com sucesso!")

            # Editar categoria já existente
            elif category == 'Editar':
                col_categoria = st.selectbox("Selecione a Categoria para Editar", st.session_state.categoria['Categoria'])
                col_categoria_edit = st.text_input("Novo Nome da Categoria", value=col_categoria)
                rep_categoria = (st.session_state.categoria['Categoria'] == col_categoria_edit).sum()
                if st.button("Editar"):
                    if rep_categoria > 0:
                        edit_category(col_categoria, col_categoria_edit)
                    else:
                        st.session_state.categoria.loc[st.session_state.categoria['Categoria'] == col_categoria, 'Categoria'] = col_categoria_edit
                        # Edita as categorias dos itens que já foram inseridos
                        st.session_state.itens.loc[st.session_state.itens['Categoria'] == col_categoria, 'Categoria'] = col_categoria_edit
                        st.success(f"Categoria {col_categoria} alterada para {col_categoria_edit}!")

            # Deletar categoria existente
            elif category == 'Deletar':
                col_categoria = st.selectbox("Selecione a Categoria para Deletar", st.session_state.categoria['Categoria'])
                if st.button("Deletar"):
                    delete_category(col_categoria)
                    #st.success("Categoria deletada com sucesso!")

            # Duplicar categoria existente
            elif category == 'Duplicar':
                col_categoria = st.selectbox("Selecione a Categoria para Deletar", st.session_state.categoria['Categoria'])
                if st.button("Duplicar"):
                    duplicate_category(col_categoria)

        #st.dataframe(st.session_state.categoria)

        # Caixa (st.form) para inserir um novo item no orçamento.
        with st.form(key='my_form'):
            col1, col2 = st.columns(2)
            with col1:
                col11, col12 = st.columns(2)
                with col11:
                    if st.session_state.itens['ID'].notna().any():
                        col_id = st.number_input("Insira ID", value=st.session_state.itens['ID'].max() + 1, format='%d')
                    else:
                        col_id = st.number_input("Insira ID", min_value=1)
                with col12:
                    col_Ndemandante = st.text_input("Insira N° do Demandante")
            with col2:
                col_descricao = st.text_input("Insira Descrição do Produto")
            if  st.session_state.categoria.empty:
                st.warning("Nenhuma categoria disponível. Adicione uma categoria antes de inserir um item.")
            else:
                col_categoria = st.selectbox("Selecione a Categoria:", st.session_state.categoria['Categoria'].unique())

            if st.session_state.categoria.empty:
                submit_button = st.form_submit_button(label="Inserir", disabled=True)
            else:
                # Adicionar um botão para inserir o novo item
                submit_button = st.form_submit_button(label="Inserir")
                # Adicionar novo Item ao orçamento se alguma categoria for selecionada
            if submit_button and col_categoria != "":
                # Criar uma nova linha com os dados inseridos
                new_line = {"ID": col_id,  "N° Demandante": col_Ndemandante,"Data Base": st.session_state.dados_orc["Data Base"].iloc[-1],
                            "Moeda Orçada": st.session_state.dados_orc["Moeda"].iloc[-1], "Descrição": col_descricao, "Categoria": col_categoria}
                # Adicionar a nova linha ao DataFrame se o ID não existir no DataFrame.
                if col_id in st.session_state.itens['ID'].values:
                    st.error("Este ID já existe em outro item deste orçamento, favor verificar.")
                else:
                    st.session_state.itens = pd.concat([st.session_state.itens, pd.DataFrame([new_line])], ignore_index=True)
                    st.success(f"Item {col_descricao} inserido a categoria {col_categoria} com sucesso!")

        
        # Caso as colunas Valor Orçado e Referências estiverem vazias, preencher com 0
        st.session_state.itens['Valor Orçado'] = st.session_state.itens['Valor Orçado'].fillna(0)
        st.session_state.itens['Referências'] = st.session_state.itens['Referências'].fillna(0)
        
        # Mostrar o DataFrame de itens do orçamento
        st.session_state.itens['Data Atualização'] = pd.to_datetime(st.session_state.itens['Data Atualização']).dt.date
        #st.dataframe(st.session_state.itens, hide_index=True)
        
        # Filtrar categoria e Item desejado
        col3, col4 = st.columns(2)
        # Filtro Categoria
        with col3:
            sel_category = st.selectbox("Selecione a Categoria:", st.session_state.itens['Categoria'].unique())
        # Filtro Item de acordo com categoria selecionada
        with col4:
            write_descripition = st.text_input("Buscar Descrição do Item:", key="search_item")
        
        choose_category = st.session_state.itens[st.session_state.itens['Categoria'] == sel_category]
        choose_descripition = choose_category[choose_category['Descrição'].str.contains(write_descripition, case=False, na=False)]
        
        # Mostrar um os dados dos itens filtrados com opção de expandir
        for index, row in choose_descripition.iterrows():
            @st.dialog(f"Inserir Referências - Item{row['ID']}: {row['Descrição']}", width='large')
            def ref(row):
                col1, col2 = st.columns(2)
                # Filtro de data
                with col1:
                    date_start = st.date_input("Data Inicial", min_value=st.session_state.base_bens['DATA REFERÊNCIA'].min(), key=f"date_start_{row['ID']}", 
                                                format='DD/MM/YYYY')#st.session_state.base_bens['DATA REFERÊNCIA'].min()
                
                # Escolha coluna com valor atualizado
                with col2:
                    date_end = st.date_input("Data Final", min_value=st.session_state.base_bens['DATA REFERÊNCIA'].min(), key=f"date_end_{row['ID']}",
                                            format='DD/MM/YYYY')
                # Conversão coluna DATA REFERÊNCIA' para data
                st.session_state.base_bens['DATA REFERÊNCIA'] = pd.to_datetime(st.session_state.base_bens['DATA REFERÊNCIA']).dt.date
                st.session_state.base_bens['Ultima Data Paridade'] = pd.to_datetime(st.session_state.base_bens['Ultima Data Paridade']).dt.date
                # Filtro de data no dataframe
                df = st.session_state.base_bens[(st.session_state.base_bens['DATA REFERÊNCIA'] >= date_start) & (st.session_state.base_bens['DATA REFERÊNCIA'] <= date_end)]

                col3, col4 = st.columns(2)
                # Filtro de classificação
                with col3:
                    r_classification = st.multiselect("Classificação", df['CLASSIFICACAO'].unique(), default=[])
                # Filtro de classificação no dataframe
                if r_classification:
                    df = df[df['CLASSIFICACAO'].isin(r_classification)]
                else:
                    df = df
                
                # Filtro de subclassificação
                with col4:
                    r_subclassification = st.multiselect("Subclassificação", df['SUBCLASSIFICACAO'].unique(), default=[])
                if r_subclassification:
                    df = df[df['SUBCLASSIFICACAO'].isin(r_subclassification)]
                else:
                    df = df
                
                col5, col6 = st.columns(2)
                # Selecionar uma coluna para o filtro
                with col5:
                    r_sel_col =  st.selectbox("Selecione uma coluna para o filtro", df.columns)
                # Digitar  texto para filtrar coluna selecionada
                with col6:
                    r_text_col_sel = st.text_input(f"Digite para filtrar {r_sel_col}")
                # Aplicar filtro digitado no dataframe
                df = df[df[r_sel_col].str.contains(r_text_col_sel, case=False, na=False)]

                # Filtro para escrever Descrição
                r_descricao = st.text_input("Filtrar Descrição:")
                df = df[df["DESCRIÇÃO"].str.contains(r_descricao, case=False, na=False)]

                # Criando o dataframe df_format para visulização dos números formatados
                df_format = pd.DataFrame(df)

                # Selecionando as colunas do tipo float
                colunas_float = df_format.select_dtypes(include=['float']).columns

                # Aplicando a formatação a todas as colunas do tipo float
                for coluna in colunas_float:
                    df_format[coluna] = df_format[coluna].apply(formatar_valores)

                st.dataframe(df_format, hide_index=True)
                df.insert(0, 'ID Item', row['ID'])
                df.insert(0, 'ID Subitem', range(1, len(df) + 1))
                #df.columns = list(df.columns[:-1]) + ['Valor Líquido Atualizado']

                # Coluna para selecionar as referências
                df['Selecionar'] = True
                
                # Botão para inserir referências
                if st.button('Inserir', key=f'inputed_ref{row['ID']}'):
                    st.session_state.subitens = pd.concat([st.session_state.subitens, df], ignore_index=True)
                    qtd_subitens = (st.session_state.subitens['ID Item'] == row['ID']).sum()
                    st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Referências'] = qtd_subitens
                    st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Data Atualização'] = df['Ultima Data Paridade'].iloc[0]
                    st.session_state.subitens['DATA REFERÊNCIA'] = pd.to_datetime(st.session_state.subitens['DATA REFERÊNCIA']).dt.date
                    st.success("Referências inseridas com sucesso!")
                    time.sleep(2)
                    st.rerun()

                
                        
            # st.dialog para visualizar valores e métricas das referências do item
            @st.dialog(f"Referências - Item{row['ID']}: {row['Descrição']}", width='large')
            def analysis(row):
                # Tabela de referências do item atual
                df_ref = st.session_state.subitens.loc[st.session_state.subitens['ID Item'] == row['ID']]
                df_ref['Ultima Data Paridade'] = pd.to_datetime(df_ref['Ultima Data Paridade']).dt.date

                # Coluna de Valor Atualizado da Moeda de Premissa que aparecerá no orçamento    
                if st.session_state.dados_orc["Moeda"].iloc[-1] == "USD":
                    df_ref['Valor Líquido Atualizado'] =  df_ref['Valor Atualizado Dolar']
                elif st.session_state.dados_orc["Moeda"].iloc[-1] == "EUR":
                    df_ref['Valor Líquido Atualizado'] =  df_ref['Valor Atualizado Euro']
                elif st.session_state.dados_orc["Moeda"].iloc[-1] == "BRL":
                    df_ref['Valor Líquido Atualizado'] =  df_ref['Valor Atualizado Real']
                # Retirando de forma provisória as colunas Valor Atualizado Dolar, Valor Atualizado Euro e Valor Atualizado Real
                df_ref.drop(columns=['Valor Atualizado Dolar', 'Valor Atualizado Euro', 'Valor Atualizado Real'], inplace=True)
                
                col_min1, col_min2 = st.columns(2)
                with col_min1:
                    # Filtro de Valor Líquido Atualizado minimo 
                    vlr_ref_min = st.number_input('Escolha valor minímo das referências', df_ref['Valor Líquido Atualizado'].min() - 1,
                    key=f'vlr_min_ref{row["ID"]}')
                # Formatando o valor mínimo das referências para exibição
                valor_min = f"{vlr_ref_min:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
                with col_min2:
                    st.text_input('Valor mínimo das referências', value=valor_min, disabled=True)
                
                col_max1, col_max2 = st.columns(2)
                with col_max1:
                    # Filtro de Valor Líquido Atualizado máximo
                    vlr_ref_max = st.number_input('Escolha valor máximo das referências', value=df_ref['Valor Líquido Atualizado'].max(),
                    max_value=df_ref['Valor Líquido Atualizado'].max() + 1, key=f'vlr_max_ref{row["ID"]}')
                # Formatando o valor máximo das referências para exibição
                valor_max = f"{vlr_ref_max:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
                with col_max2:
                    st.text_input('Valor máximo das referências', value=valor_max, disabled=True)
                
                # Aplicando filtros nas referencias do item atual
                df = df_ref[(df_ref['Valor Líquido Atualizado'] >= vlr_ref_min) & (df_ref['Valor Líquido Atualizado'] <= vlr_ref_max)]
                
                # Criando o dataframe df_format para visulização dos números formatados
                df_format = pd.DataFrame(df)

                # Selecionando as colunas do tipo float
                colunas_float = df_format.select_dtypes(include=['float']).columns

                # Aplicando a formatação a todas as colunas do tipo float
                for coluna in colunas_float:
                    df_format[coluna] = df_format[coluna].apply(formatar_valores)

                #colunas_moeda = df_format.select_dtypes(include=['string']).columns
                df_sel = st.data_editor(df_format, hide_index=True, 
                                        disabled=['ID Item','ID Subitem','CONTRATO - ITEM',	'FORNECEDOR', 'DATA REFERÊNCIA', 
                                        'DESCRIÇÃO', 'NM',	'Und Medida', 'CLASSIFICACAO', 'SUBCLASSIFICACAO', 'FÓRMULA ATUALIZAÇÃO', 
                                        'VALOR LÍQUIDO REFERÊNCIA', 'MOEDA REFERÊNCIA', 'Ultima Data Paridade',	'Valor Líquido Atualizado'])
                df_in = df[df_sel['Selecionar'] == True]
                
                colunm_value = df_in['Valor Líquido Atualizado']#.dropna()

                # Cálculos estatísticos do Valor Líquido Atualizado destas referências
                mean = colunm_value.mean()
                median = colunm_value.median()
                q1 = colunm_value.quantile(0.25)
                q3 = colunm_value.quantile(0.75)
                min_val = colunm_value.min()
                max_val = colunm_value.max()
                std_dev = colunm_value.std()
                coef_var = (std_dev / mean) * 100
                iqr = q3 - q1  # Intervalo interquartil
                lower_bound = q1 - 1.5 * iqr  # Limite inferior
                upper_bound = q3 + 1.5 * iqr  # Limite superior
                # Exibe as métricas estatísticas em um dataframe
                stats_df = pd.DataFrame({
                            "Métrica": ["Média", "Mediana", "Q1", "Q3", "Mínimo", "Máximo", "Desvio Padrão",
                                        "Coeficiente de Variação (%)", "IQR", "Limite Inferior (IQR)", "Limite Superior (IQR)"],
                            "Valor": [mean, median, q1, q3, min_val, max_val, std_dev, coef_var, iqr, lower_bound, upper_bound]
                            })
                st.write("### Métricas Estatísticas:")

                # Criando o dataframe df_format para visulização dos números formatados
                stats_dfformat = pd.DataFrame(stats_df)

                # Selecionando as colunas do tipo float
                colunas_float = stats_dfformat.select_dtypes(include=['float']).columns

                # Aplicando a formatação a todas as colunas do tipo float
                for coluna in colunas_float:
                    stats_dfformat[coluna] = stats_dfformat[coluna].apply(formatar_valores)

                # Exibindo o dataframe com as métricas estatísticas
                st.dataframe(stats_dfformat, hide_index=True, width=350)

                # Gráfico de Boxplot
                fig_box = go.Figure(data=[go.Box(
                        y=colunm_value,
                        name='Valor Líquido Atualizado',
                        boxpoints="all",
                        jitter=0.3,
                        pointpos=-1.8,
                        marker=dict(color="blue"),
                        line=dict(color="black"),
                        boxmean="sd"  # Exibe a média e o desvio padrão no boxplot
                        )])
                fig_box.update_layout(
                        title="Boxplot:",
                        yaxis_title='Valor Líquido Atualizado',
                        width=800,  # Ajusta a largura do gráfico
                        height=400   # Ajusta a altura do gráfico
                        )
                st.plotly_chart(fig_box, use_container_width=False)

                # Selecionar métrica para visualizar no gráfico de disperção
                metric = st.selectbox("Métrica Estatística:",  options= stats_df['Métrica'].tolist(), key=f"selectbox_{row['ID']}")
                vlr_orc = stats_df[stats_df['Métrica'] == metric]['Valor'].iloc[0]# * par_ref

                # Criação do gráfico de dispersão
                fig = go.Figure()
                # Adicionando a dispersão (valores em relação às datas)
                fig.add_trace(go.Scatter(
                    x=df_in['DATA REFERÊNCIA'],
                    y=df_in['Valor Líquido Atualizado'],
                    mode='markers',
                    name='Valores',
                    marker=dict(color='green', size=10)
                    ))
                fig.add_trace(go.Scatter(
                    x=df_in['DATA REFERÊNCIA'],
                    y=[vlr_orc] * len(df_in),  # Linha constante com o valor da métrica
                    mode='lines',
                    name=f'{metric}',
                    line=dict(color='black', dash='dash')  # Estilo da linha (pontilhada)
                    ))
                # Adicionando anotação para o valor da métrica na linha
                fig.add_annotation(
                    x=df_in['DATA REFERÊNCIA'],#[1],  # Posição no eixo X (primeiro ponto)
                    y=vlr_orc,  # Posição no eixo Y (valor da métrica)
                    text=f"{metric}: {vlr_orc:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", "."),  # Texto exibido
                    showarrow=True,  # Exibir uma seta apontando para o valor
                    arrowhead=2,  # Estilo da seta
                    ax=550,  # Distância da anotação em relação ao ponto X
                    ay=-20,  # Distância da anotação em relação ao ponto Y
                    font=dict(size=12, color="white"),  # Estilo da fonte
                    bgcolor="black",  # Cor de fundo da anotação
                    opacity=0.7  # Opacidade da anotação
                    )

                # Definindo o layout
                fig.update_layout(
                    title="Gráfico de Dispersão com Métricas",
                    xaxis_title="Data da Referência",
                    yaxis_title="Valor Líquido Atualizado",
                    template="plotly_dark"  # Tema do gráfico (opcional)
                    )
                # Exibindo o gráfico no Streamlit
                st.plotly_chart(fig, use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                        col11, col12 = st.columns(2)
                        with col11:
                            # Botão para editar as referências
                            if st.button('Validar Referências', key=f'button_validated_{row["ID"]}'):
                                # Mesclar tabelas df_ref(que vem com todas as refeRências do item) com df_in(que contém apenas referências selecionadas).
                                df = pd.merge(df_ref, df_in, how='left', on=['ID Item','ID Subitem',
                                'CONTRATO - ITEM', 'FORNECEDOR', 'DATA REFERÊNCIA', 'DESCRIÇÃO', 'NM', 'Und Medida', 'CLASSIFICACAO', 
                                'SUBCLASSIFICACAO', 'FÓRMULA ATUALIZAÇÃO', 'VALOR LÍQUIDO REFERÊNCIA', 'MOEDA REFERÊNCIA', 
                                'Ultima Data Paridade', 'Valor Líquido Atualizado'], indicator=True)
                                df = df.drop(columns=['Selecionar_x', 'Selecionar_y'])
                                # Criar a coluna 'Selecionar' com base na coluna '_merge'
                                df['Selecionar'] = df['_merge'].apply(lambda x: True if x == 'both' else False)
                                df = df.drop(columns=['_merge'])
                                # Manter a coluna de DATA REFERÊNCIA no formato de data padrão da ferramenta
                                df['DATA REFERÊNCIA'] = pd.to_datetime(df['DATA REFERÊNCIA']).dt.date
                                # Como as referências irão para o orçamento
                                st.session_state.subitens.loc[st.session_state.subitens['ID Item'] == row['ID'], ['ID Item','ID Subitem',
                                'CONTRATO - ITEM',	'FORNECEDOR', 'DATA REFERÊNCIA', 'DESCRIÇÃO', 'NM',	'Und Medida', 'CLASSIFICACAO', 
                                'SUBCLASSIFICACAO', 'FÓRMULA ATUALIZAÇÃO', 'VALOR LÍQUIDO REFERÊNCIA', 'MOEDA REFERÊNCIA', 
                                'Ultima Data Paridade', 'Valor Líquido Atualizado', 'Selecionar']] = df.values
                                ref_0 = df[df['Selecionar'] == True].iloc[0]
                                data_paridade = ref_0['Ultima Data Paridade']
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Data Atualização'] = data_paridade
                                qtd_subitens = (df['Selecionar'] == True).sum()
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Referências'] = qtd_subitens
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Métrica Utilizada'] = metric
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Valor Orçado'] = vlr_orc
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Fator'] = 1.00
                                time.sleep(2)
                                st.write("Validado! :white_check_mark:")
                                time.sleep(1)
                                st.rerun()
                        with col12:
                            if st.button("Voltar", key=f"back_button{row['ID']}"):
                                st.rerun()

            # st.dialog para deletar itens e suas referências
            @st.dialog(f"Item{row['ID']} - {row['Descrição']}", width='large')
            def delete_item(row):
                st.warning("Ao deletar o item, todas as suas referências serão deletadas. Tem certeza que deseja continuar?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Deletar"):
                        st.session_state.itens = st.session_state.itens[st.session_state.itens['ID'] != row['ID']]
                        st.session_state.subitens = st.session_state.subitens[st.session_state.subitens['ID Item'] != row['ID']]
                        time.sleep(2)
                        st.write(f"Item {row['ID']} Deletado!")
                        time.sleep(1)
                        st.rerun()

            @st.dialog(f"Duplicar Item{row['ID']} - {row['Descrição']}", width='small')
            def duplicate_item(row):
                category_duplicate = st.selectbox("Escolha categoria para o item duplicado:", 
                                                    st.session_state.categoria['Categoria'].unique(), 
                                                    key= f'duplicate_item_in_category{row['ID']}')
                new_id = st.session_state.itens['ID'].max() + 1
                if st.button('Duplicar apenas Item', key=f'duplicate_only_item{row['ID']}'):
                    item_duplicate = {
                                        'ID': new_id,
                                        'N° Demandante': row['N° Demandante'],
                                        'Data Base': row['Data Base'],
                                        'Descrição': f"{row['Descrição']} Duplicado",
                                        'Valor Orçado': row['Valor Orçado'],
                                        'Moeda Orçada': row['Moeda Orçada'],
                                        'Referências': 0,
                                        'Métrica Utilizada': row['Métrica Utilizada'],
                                        'Fator': row['Fator'],
                                        'Und Medida': row['Und Medida'],
                                        'Quantidade': row['Quantidade'],
                                        'Classificação': row['Classificação'],
                                        'Subclassificação': row['Subclassificação'],
                                        'Data Atualização': row['Data Atualização'],
                                        'Categoria': category_duplicate
                                    }
                    st.session_state.itens = pd.concat([st.session_state.itens, 
                                                        pd.DataFrame([item_duplicate])], ignore_index=True)
                    st.success("Item duplicado com sucesso!")
                    time.sleep(3)
                    st.rerun()



            # st.expander para itens sem referências inseridas.
            if row['Referências'] == 0:
                with st.expander(f":red[Item {row['ID']} - {row['Descrição']} - Valor Orçado: {row['Valor Orçado']:,.2f} com {row['Referências']} referências]".replace(",", "ABCDTEMP").replace(".", ",").replace("ABCDTEMP", ".")):
                    if st.button('Inserir Referências', key=f'input_ref{row['ID']}'):
                        ref(row)
                        
                    # Editar item sem referência inserida
                    col1, col2 = st.columns(2)
                    with col1:
                        st.number_input("ID", value=int(row['ID']), disabled=True)
                    with col2:
                        st.date_input("Data Base", value=row['Data Base'], key=f"inputed_db{row['ID']}", disabled=True)
                    
                    if row['Moeda Orçada'] != st.session_state.dados_orc['Moeda'].iloc[-1]:
                        col_moe = st.text_input('Moeda Orçada', value=row['Moeda Orçada'], key=f"inputed_moe{row['ID']}")
                        st.warning("A moeda do item não corresponde à moeda do orçamento. Por favor, verifique os valores.")
                        
                    else:
                        col3, col4 = st.columns(2)
                        with col3:
                            col_moe = st.text_input('Moeda Orçada', value=row['Moeda Orçada'], key=f"inputed_mo{row['ID']}", disabled=True)
                        with col4:
                            st.number_input('Referências', value=int(row['Referências']), key=f"inputed_ref1{row['ID']}", disabled=True)
                    col5, col6 = st.columns(2)
                    with col5:
                        col_ndem = st.text_input("N° Demandante", row['N° Demandante'], key=f"inputed_ndem{row['ID']}")
                    with col6:
                        col_desc = st.text_input("Descrição", row['Descrição'], key=f"inputed_desc{row['ID']}")
                    col7, col8 = st.columns(2)
                    with col7:
                        col_vlr_orc = st.number_input("Valor Orçado", value=float(row['Valor Orçado']), step=0.01, key=f"inputed_vlr_orc{row['ID']}")
                    with col8:
                        col_dat_atu = st.date_input("Data Atualização", key=f"inputed_dat_atu{row['ID']}", format='DD/MM/YYYY')
                    col9, col10 = st.columns(2)
                    with col9:
                        col_met_uti = st.text_input("Métrica Utilizada", row['Métrica Utilizada'], key=f"inputed_met_uti{row['ID']}")
                    with col10:
                        col_par_ref = st.number_input("Fator", value=float(1), step=0.10, key=f"inputed_par_ref{row['ID']}")
                    col11, col12 = st.columns(2)
                    with col11:
                        col_und_med = st.text_input("Und Medida", row['Und Medida'], key=f"inputed_und_med{row['ID']}")
                    with col12:
                        col_qtd = st.number_input("Quantidade", value=float(1), step=1.00, key=f"inputed_qtd{row['ID']}")
                    col13, col14 = st.columns(2)
                    with col13:
                        col_cla = st.text_input("Classificação", row['Classificação'], key=f"inputed_cla{row['ID']}")
                    with col14:
                        col_scla = st.text_input("Subclassificação", row['Subclassificação'], key=f"inputed_scla{row['ID']}")

                    # Botão de atualização do item
                    col15, col16 = st.columns(2)
                    with col15:
                        col151, col152, col153 = st.columns(3)
                        with col151:
                            if st.button("Atualizar", key=f"update_button1{row['ID']}", use_container_width=True):
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Moeda Orçada'] = col_moe
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'N° Demandante'] = col_ndem
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Descrição'] = col_desc
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Valor Orçado'] = col_vlr_orc
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Data Atualização'] = col_dat_atu
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Métrica Utilizada'] = col_met_uti
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Fator'] = col_par_ref
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Und Medida'] = col_und_med
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Quantidade'] = col_qtd
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Classificação'] = col_cla
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Subclassificação'] = col_scla
                                time.sleep(3)
                                st.write(f":green[Item {row['ID']} atualizado!]", use_column_width=True)
                                time.sleep(1)
                                st.rerun()
                        with col152:
                            if st.button("Deletar", key=f'delete_item1{row['ID']}', use_container_width=True):
                                delete_item(row)
                        with col153:
                            if st.button("Duplicar", key=f'duplicate_item1{row['ID']}', use_container_width=True):
                                duplicate_item(row)
            
            # st.expander para itens com referências inseridas.
            else:
                with st.expander(f"Item {row['ID']} - {row['Descrição']} - Valor Orçado: {row['Valor Orçado']:,.2f} com {row['Referências']} referências".replace(",", "ABCDTEMP").replace(".", ",").replace("ABCDTEMP", ".")):
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button('Analise valores referenciais', key=f"analysis_button{row['ID']}"):
                            analysis(row)
                    with col2:
                        if st.button("Inserir mais referências", key=f"add_ref_button{row['ID']}"):
                            ref(row)
                    
                    # Métricas estatístiscas para autometizar text_input de métricas e Valor Orçado
                    df_ref = st.session_state.subitens.loc[st.session_state.subitens['ID Item'] == row['ID']]
                    df_ref = df_ref.loc[df_ref['Selecionar'] == True]

                    # Coluna de Valor Atualizado da Moeda de Premissa que aparecerá no orçamento    
                    if st.session_state.dados_orc["Moeda"].iloc[-1] == "USD":
                        df_ref['Valor Líquido Atualizado'] =  df_ref['Valor Atualizado Dolar']
                    elif st.session_state.dados_orc["Moeda"].iloc[-1] == "EUR":
                        df_ref['Valor Líquido Atualizado'] =  df_ref['Valor Atualizado Euro']
                    elif st.session_state.dados_orc["Moeda"].iloc[-1] == "BRL":
                        df_ref['Valor Líquido Atualizado'] =  df_ref['Valor Atualizado Real']
                    colunm_value = df_ref['Valor Líquido Atualizado']#.dropna()

                    # Cálculos estatísticos do Valor Líquido Atualizado destas referências
                    mean = colunm_value.mean()
                    median = colunm_value.median()
                    q1 = colunm_value.quantile(0.25)
                    q3 = colunm_value.quantile(0.75)
                    min_val = colunm_value.min()
                    max_val = colunm_value.max()
                    std_dev = colunm_value.std()
                    coef_var = (std_dev / mean) * 100
                    iqr = q3 - q1  # Intervalo interquartil
                    lower_bound = q1 - 1.5 * iqr  # Limite inferior
                    upper_bound = q3 + 1.5 * iqr  # Limite superior

                    # Exibe as métricas estatísticas em um dataframe
                    stats_df = pd.DataFrame({
                                "Métrica": ["Média", "Mediana", "Q1", "Q3", "Mínimo", "Máximo", "Desvio Padrão",
                                            "Coeficiente de Variação (%)", "IQR", "Limite Inferior (IQR)", "Limite Superior (IQR)"],
                                "Valor": [mean, median, q1, q3, min_val, max_val, std_dev, coef_var, iqr, lower_bound, upper_bound]
                                })
                    
                    # Coluna Fator se estiver vazio, fica igual a 1
                    st.session_state.itens['Fator'] = st.session_state.itens['Fator'].fillna(1)

                    # Editar item com referência inserida
                    col1, col2 = st.columns(2)
                    with col1:
                        st.number_input("ID", value=int(row['ID']), disabled=True)
                    with col2:
                        st.date_input("Data Base", value=row['Data Base'], key=f"inputed_db{row['ID']}", disabled=True)
                    col3, col4 = st.columns(2)
                    with col3:
                        st.text_input('Moeda Orçada', value=row['Moeda Orçada'], key=f"inputed_mo{row['ID']}", disabled=True)
                    with col4:
                        st.number_input('Referências', value=int(row['Referências']), key=f"inputed_n_ref{row['ID']}", disabled=True)
                    col5, col6 = st.columns(2)
                    with col5:
                        col_ndem = st.text_input("N° Demandante", row['N° Demandante'], key=f"inputed_ndem{row['ID']}")
                    with col6:
                        col_desc = st.text_input("Descrição", row['Descrição'], key=f"inputed_desc{row['ID']}")
                    if row['Moeda Orçada'] != st.session_state.dados_orc['Moeda'].iloc[-1]:
                        st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Moeda Orçada'] = st.session_state.dados_orc['Moeda'].iloc[-1]
                        if row['Métrica Utilizada'] in stats_df['Métrica'].values:
                            col_met_uti =  row['Métrica Utilizada']
                            vlr_orc = stats_df[stats_df['Métrica'] == col_met_uti]['Valor'].iloc[0]
                            col_par_ref = float(row['Fator'])
                            col_vlr_orc = float(vlr_orc * col_par_ref)
                            st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Valor Orçado'] = col_vlr_orc
                            st.rerun()
                        else:
                            st.rerun()
                    else:
                        col9, col10 = st.columns(2)
                        with col9:
                            if row['Métrica Utilizada'] in stats_df['Métrica'].values:
                                # Indice da métrica utilizada, para deixá-la padrão.
                                index_met_uti =  stats_df[stats_df['Métrica'] == row['Métrica Utilizada']].index[0]
                                index_met_uti = int(index_met_uti)
                                # Selecionar Métrica Utilizada, mantendo a atual como padrão.
                                col_met_uti = st.selectbox("Métrica Utilizada", stats_df['Métrica'].tolist(), index=index_met_uti,
                                                            key=f"inputed_met_uti{row['ID']}")
                            else:
                                col_met_uti = st.selectbox("Métrica Utilizada", stats_df['Métrica'].tolist(),
                                                            key=f"inputed_met_utili{row['ID']}")
                            vlr_orc = stats_df[stats_df['Métrica'] == col_met_uti]['Valor'].iloc[0]
                            
                        with col10:
                            col_par_ref = st.number_input("Fator", value=float(row['Fator']), step=0.10, key=f"inputed_par_ref{row['ID']}")
                        col_vlr_orc = vlr_orc * col_par_ref
                        st.text_input("Valor Orçado", value=f"{col_vlr_orc:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", "."), 
                                                        key=f"inputed_vlr_orc{row['ID']}", disabled=True)
                    col11, col12 = st.columns(2)
                    with col11:
                        col_und_med = st.text_input("Und Medida", row['Und Medida'], key=f"inputed_und_med{row['ID']}")
                    with col12:
                        col_qtd = st.number_input("Quantidade", value=float(1), step=1.00, key=f"inputed_qtd{row['ID']}")
                    col13, col14 = st.columns(2)
                    with col13:
                        col_cla = st.text_input("Classificação", row['Classificação'], key=f"inputed_cla{row['ID']}")
                    with col14:
                        col_scla = st.text_input("Subclassificação", row['Subclassificação'], key=f"inputed_scla{row['ID']}")

                    # Botões para Atualizar/Duplicar/Deletar item.
                    col7, col8 = st.columns(2)
                    with col7:
                        col71, col72, col73 = st.columns(3)
                        with col71:
                            if st.button("Atualizar", key=f"update_button{row['ID']}", use_container_width=True):
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Descrição'] = col_desc
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'N° Demandante'] = col_ndem
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Valor Orçado'] = col_vlr_orc
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Métrica Utilizada'] = col_met_uti
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Fator'] = col_par_ref
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Und Medida'] = col_und_med
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Quantidade'] = col_qtd
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Classificação'] = col_cla
                                st.session_state.itens.loc[st.session_state.itens['ID'] == row['ID'], 'Subclassificação'] = col_scla
                                time.sleep(3)
                                st.write(f":green[Item {row['ID']} atualizado!]", use_column_width=True)
                                time.sleep(2)
                                st.rerun()
                        with col72:
                            if st.button("Deletar", key=f'delete_item{row['ID']}', use_container_width=True):
                                delete_item(row)


                        with col73:
                            with st.popover("Duplicar", use_container_width=True):
                                category_duplicate = st.selectbox("Escolha categoria para o item duplicado:", 
                                                                    st.session_state.categoria['Categoria'].unique(), 
                                                                    key= f'duplicate_item_in_category{row['ID']}')
                                new_id = st.session_state.itens['ID'].max() + 1
                                qtd_ref_bruto = (st.session_state.subitens['ID Item'] == row['ID']).sum()
                                if st.button("Duplicar Item e Referências", key=f'duplicate_item&references{row['ID']}'):
                                    item_duplicate = {
                                        'ID': new_id,
                                        'N° Demandante': row['N° Demandante'],
                                        'Data Base': row['Data Base'],
                                        'Descrição': f"{row['Descrição']} Duplicado",
                                        'Valor Orçado': row['Valor Orçado'],
                                        'Moeda Orçada': row['Moeda Orçada'],
                                        'Referências': qtd_ref_bruto,
                                        'Métrica Utilizada': row['Métrica Utilizada'],
                                        'Fator': row['Fator'],
                                        'Und Medida': row['Und Medida'],
                                        'Quantidade': row['Quantidade'],
                                        'Classificação': row['Classificação'],
                                        'Subclassificação': row['Subclassificação'],
                                        'Data Atualização': row['Data Atualização'],
                                        'Categoria': category_duplicate
                                    }
                                    st.session_state.itens = pd.concat([st.session_state.itens, 
                                                                        pd.DataFrame([item_duplicate])], ignore_index=True)
                                    df_ref = st.session_state.subitens[st.session_state.subitens['ID Item'] == row['ID']]
                                    df_ref['ID Item'] = new_id
                                    df_ref['Selecionar'] = True
                                    st.session_state.subitens = pd.concat([st.session_state.subitens, df_ref], 
                                                                            ignore_index=True)
                                    time.sleep(2)
                                    st.success("Item e suas referências duplicados com sucesso!")
                                    time.sleep(2)
                                    st.rerun()
                                if st.button('Duplicar apenas Item', key=f'duplicate_only_item{row['ID']}'):
                                    item_duplicate = {
                                        'ID': new_id,
                                        'N° Demandante': row['N° Demandante'],
                                        'Data Base': row['Data Base'],
                                        'Descrição': f"{row['Descrição']} Duplicado",
                                        'Valor Orçado': row['Valor Orçado'],
                                        'Moeda Orçada': row['Moeda Orçada'],
                                        'Referências': 0,
                                        'Métrica Utilizada': row['Métrica Utilizada'],
                                        'Fator': row['Fator'],
                                        'Und Medida': row['Und Medida'],
                                        'Quantidade': row['Quantidade'],
                                        'Classificação': row['Classificação'],
                                        'Subclassificação': row['Subclassificação'],
                                        'Data Atualização': row['Data Atualização'],
                                        'Categoria': category_duplicate
                                    }
                                    st.session_state.itens = pd.concat([st.session_state.itens, 
                                                                        pd.DataFrame([item_duplicate])], ignore_index=True)
                                    st.success("Item duplicado com sucesso!")
                                    time.sleep(3)
                                    st.rerun()
                    


        
        # Botão excel_buffer = BytesIO()
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            st.session_state.dados_orc.to_excel(writer, index=False, sheet_name='Informações Gerais')
            premissas.to_excel(writer, index=False, sheet_name='Premissas')
            st.session_state.itens.to_excel(writer, index=False, sheet_name='Itens')
            st.session_state.subitens.to_excel(writer, index=False, sheet_name='Referências')
            st.session_state.categoria.to_excel(writer, index=False, sheet_name='Categorias')

    # Definir o ponteiro do arquivo para o início
        excel_buffer.seek(0)
        st.download_button(
            label= 'Salvar Alterações no Excel',
            data= excel_buffer,
            file_name= uploaded_file.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )  
    
    def consolidated():
        st.write("### Resultado do Orçamento")
        dados_orc = pd.read_excel(uploaded_file, sheet_name='Informações Gerais')
        premissas = pd.read_excel(uploaded_file, sheet_name='Premissas')
        itens = pd.read_excel(uploaded_file, sheet_name='Itens')
        subitens = pd.read_excel(uploaded_file, sheet_name='Referências')
        categorias = pd.read_excel(uploaded_file, sheet_name='Categorias')
        if 'itens' not in st.session_state:
            st.session_state.itens = itens  # Inicializa a lista de itens no estado da sessão
        if 'subitens' not in st.session_state:
            st.session_state.subitens = subitens  # Inicializa a lista de subitens no estado da sessão
        tabela_orp = pd.DataFrame(columns= ['Item', 'Requisição de Compra',	'Item RC', 'NM', 'NCM',	'Centro',	'UF Centro',
                                            'Database', 'Descrição', 'Tipo de Insumo', 'Unidade de Medida',	'Quantidade',
                                            'Fator', 'Tributação', 'Fator de Tributação', 'Sobressalentes',	'Valor Unitário',
                                            'Valor Total',	'Observação', 'Utilização Material', 'Alíquota PIS', 'Alíquota COFINS',
                                            'Alíquota ICMS', 'Alíquota ICMS-DIFAL',	'Base de Cálculo do ICMS', 'Alíquota IPI'])
        consolidado = pd.DataFrame(columns= ['Item', 'NCM', 'Database', 'Descrição', 'Unidade de Medida', 'Quantidade', 'Fator',
                                            'Tributação', 'Valor Unitário', 'Valor Total'])
        consolidado['Item'] = st.session_state.itens['ID']
        consolidado['Database'] = st.session_state.itens['Data Base']
        consolidado['Descrição'] = st.session_state.itens['Descrição']
        consolidado['Unidade de Medida'] = st.session_state.itens['Und Medida']
        consolidado['Fator'] = st.session_state.itens['Fator']
        consolidado['Quantidade'] = st.session_state.itens['Quantidade']
        consolidado['Valor Unitário'] = st.session_state.itens['Valor Orçado']
        consolidado['Valor Total'] = consolidado['Quantidade'] * consolidado['Valor Unitário']
        
        consolidado = st.data_editor(consolidado, hide_index=True, use_container_width=True, column_config={
            # Inserir coluna de Tributação ('BENS' ou 'NADA')
            'Tributação': st.column_config.SelectboxColumn(
                options=('BENS', 'NADA'),
                help="Tributação do item",
                width="small",
                required=True,
            )
        }, disabled=['Item', 'Database', 'Descrição', 'Unidade de Medida', 'Fator', 'Valor Unitário', 'Valor Total'])
        tabela_orp = pd.concat([tabela_orp, consolidado], ignore_index=True)

        # Função para salvar o DataFrame em um arquivo Excel
        def to_excel(tabela_orp):
            # Cria um buffer em memória para salvar o arquivo
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                tabela_orp.to_excel(writer, index=False)
            output.seek(0)
            return output

        # Criando o botão de download
        excel_data = to_excel(tabela_orp)

        st.download_button(
            label= 'Gerar Planilha ORP',
            data= excel_data,
            file_name= 'Tabela ORP.xlsx',
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )  

    # Função para realizar análises estatísticas
    def statistical_analysis(data, column):
        st.write("### Análises Estatísticas")

        # Seleciona os dados da coluna e remove valores ausentes
        analysis_data = data[column].dropna()

        # Filtro de valor máximo e mínimo da referência
        min_filter = st.number_input("Defina o valor mínimo da referência para a análise:", value=float(analysis_data.min()))
        max_filter = st.number_input("Defina o valor máximo da referência para a análise:", value=float(analysis_data.max()))
        filtered_data = analysis_data[(analysis_data >= min_filter) & (analysis_data <= max_filter)]

        # Implementar exclusão justificada de referências via tabela alternativa
        st.write("#### Exclusão Justificada de Referências")
        excluded_references = []

        # Exibe os dados filtrados
        st.write("#### Dados para Análise")
        data_display = filtered_data.reset_index()
        to_exclude = st.multiselect(
            "Selecione os índices para exclusão:",
            options=data_display.index.tolist(),
            format_func=lambda idx: f"Índice: {data_display.at[idx, 'index']} | Valor: {data_display.at[idx, column]}"
        )

        for idx in to_exclude:
            value = data_display.at[idx, column]
            original_index = data_display.at[idx, 'index']
            reason = st.text_input(f"Justifique a exclusão do valor {value} (índice original {original_index}):", key=f"exclusion_{original_index}")
            if reason:
                excluded_references.append((original_index, value, reason))

        if excluded_references:
            st.write("#### Valores Excluídos")
            st.dataframe(pd.DataFrame(excluded_references, columns=["Índice Original", "Valor", "Justificativa"]))

            # Remove os valores excluídos manualmente
            excluded_indices = [item[0] for item in excluded_references]
            filtered_data = filtered_data[~filtered_data.index.isin(excluded_indices)]

        # Calcula as métricas estatísticas
        mean = filtered_data.mean()
        median = filtered_data.median()
        q1 = filtered_data.quantile(0.25)
        q3 = filtered_data.quantile(0.75)
        min_val = filtered_data.min()
        max_val = filtered_data.max()
        std_dev = filtered_data.std()
        coef_var = (std_dev / mean) * 100
        iqr = q3 - q1  # Intervalo interquartil
        lower_bound = q1 - 1.5 * iqr  # Limite inferior
        upper_bound = q3 + 1.5 * iqr  # Limite superior

        # Exibe as métricas estatísticas
        stats_df = pd.DataFrame({
            "Métrica": ["Média", "Mediana", "Q1", "Q3", "Mínimo", "Máximo", "Desvio Padrão",
                        "Coeficiente de Variação (%)", "IQR", "Limite Inferior (IQR)", "Limite Superior (IQR)"],
            "Valor": [mean, median, q1, q3, min_val, max_val, std_dev, coef_var, iqr, lower_bound, upper_bound]
        })

        st.write("#### Métricas para a coluna selecionada:")
        st.dataframe(stats_df.set_index("Métrica"), height=400, width=600)


        # Gráfico de Boxplot
        st.write("#### Boxplot")
        fig_box = go.Figure(data=[go.Box(
            y=filtered_data,
            name=column,
            boxpoints="all",
            jitter=0.3,
            pointpos=-1.8,
            marker=dict(color="blue"),
            line=dict(color="black"),
            boxmean="sd"  # Exibe a média e o desvio padrão no boxplot
        )])
        fig_box.update_layout(
            title="Boxplot",
            yaxis_title=column,
            width=800,  # Ajusta a largura do gráfico
            height=400   # Ajusta a altura do gráfico
        )
        st.plotly_chart(fig_box, use_container_width=False)

        # Gráfico de Dispersão com Identificação de Outliers
        st.write("### Gráfico de Dispersão com Outliers")
        x_column = st.selectbox(
            "Selecione a coluna para o eixo X (incluindo datas):",
            data.columns.tolist(),
            key=f"scatter_x_{column}"
        )
        y_column = st.selectbox(
            "Selecione a coluna para o eixo Y (numérica):",
            [column],
            key=f"scatter_y_{column}"
        )

        if x_column and y_column:
            # Garante que os índices estejam alinhados e aplica o filtro de exclusão
            aligned_data = data[[x_column, y_column]].dropna()
            aligned_data = aligned_data[aligned_data[y_column].isin(filtered_data)]

            # Atualiza os índices para alinhamento
            analysis_data_aligned = aligned_data[y_column]
            x_data_aligned = aligned_data[x_column]

            # Recalcula outliers com os dados alinhados e filtrados
            outliers = analysis_data_aligned[
                (analysis_data_aligned < lower_bound) | (
                    analysis_data_aligned > upper_bound)
            ]

            fig_scatter = go.Figure()

            # Adiciona os pontos de dispersão
            fig_scatter.add_trace(go.Scatter(
                x=x_data_aligned,
                y=analysis_data_aligned,
                mode='markers',
                name="Dados"
            ))

            # Adiciona as linhas de limite do IQR
            fig_scatter.add_shape(
                type="line",
                x0=x_data_aligned.min(),
                x1=x_data_aligned.max(),
                y0=lower_bound,
                y1=lower_bound,
                line=dict(color="red", dash="dash"),
                name="Limite Inferior"
            )
            fig_scatter.add_shape(
                type="line",
                x0=x_data_aligned.min(),
                x1=x_data_aligned.max(),
                y0=upper_bound,
                y1=upper_bound,
                line=dict(color="red", dash="dash"),
                name="Limite Superior"
            )

            # Adiciona os outliers ao gráfico
            fig_scatter.add_trace(go.Scatter(
                x=x_data_aligned[analysis_data_aligned.index.isin(
                    outliers.index)],
                y=outliers,
                mode='markers',
                marker=dict(color='red', size=10, symbol='circle'),
                name="Outliers"
            ))

            # Configuração do layout do gráfico
            fig_scatter.update_layout(
                title="Gráfico de Dispersão com Outliers",
                xaxis_title=x_column,
                yaxis_title=y_column,
                showlegend=True
            )
            st.plotly_chart(fig_scatter, use_container_width=True)



    # Definir filtros da Base de Referências
    def filtro_base_referencias(df):
        col1, col2 = st.columns(2)
        # Filtro de data
        with col1:
            col11, col12 = st.columns(2)
            with col11:
                date_start = st.date_input("Data Inicial", value=df['DATA REFERÊNCIA'].min())
            with col12:
                date_end = st.date_input("Data Final", value=df['DATA REFERÊNCIA'].max())
        # Conversão coluna DATA REFERÊNCIA' e 'Ultima Data Paridade' para data.
        df['DATA REFERÊNCIA'] = pd.to_datetime(df['DATA REFERÊNCIA']).dt.date
        df['Ultima Data Paridade'] = pd.to_datetime(df['Ultima Data Paridade']).dt.date
        # Filtro de data no dataframe
        df = df[(df['DATA REFERÊNCIA'] >= date_start) & (df['DATA REFERÊNCIA'] <= date_end)]
        
        # Escolha coluna com valor atualizado
        with col2:
            r_col_moeda_atu = st.selectbox('Selecione moeda com valor atualizado', df.columns[-3:])
        # Filtro de moeda com valor atualizado no dataframe
        r_moeda_vlr_atu = list(df.columns[:-3]) + [r_col_moeda_atu]
        df = df[r_moeda_vlr_atu]

        col3, col4 = st.columns(2)
        # Filtro de classificação
        with col3:
            r_classification = st.multiselect("Classificação", df['CLASSIFICACAO'].unique(), default=[])
        # Filtro de classificação no dataframe
        if r_classification:
            df = df[df['CLASSIFICACAO'].isin(r_classification)]
        else:
            df = df
        
        # Filtro de subclassificação
        with col4:
            r_subclassification = st.multiselect("Subclassificação", df['SUBCLASSIFICACAO'].unique(), default=[])
        if r_subclassification:
            df = df[df['SUBCLASSIFICACAO'].isin(r_subclassification)]
        else:
            df = df
        
        col5, col6 = st.columns(2)
        # Selecionar uma coluna para o filtro
        with col5:
            r_sel_col =  st.selectbox("Selecione uma coluna para o filtro", df.columns)
        # Digitar  texto para filtrar coluna selecionada
        with col6:
            r_text_col_sel = st.text_input(f"Digite para filtrar {r_sel_col}")
        # Aplicar filtro digitado no dataframe
        df = df[df[r_sel_col].str.contains(r_text_col_sel, case=False, na=False)]

        # Filtro para escrever Descrição
        r_descricao = st.text_input("Filtrar Descrição:")
        df = df[df["DESCRIÇÃO"].str.contains(r_descricao, case=False, na=False)]

        # Tabela da base de referências, seguindo filtros aplicados.
        st.dataframe(df, hide_index=True)


    # Adicionar logotipo na barra lateral
    # Certifique-se de que o caminho para a imagem está correto
    logo_image = Image.open("petrobras_logo_branco.png")
    st.sidebar.image(logo_image, use_container_width=True)

    # Barra lateral com botões de navegação
    buttons = ["Novo Orçamento", "Revisões", "Premissas", "Itens", "Base de Dados", "Analises", "Consolidado"]
    with st.sidebar:  # Garante que o menu com ícones fique na barra lateral
        selected_screen = option_menu(
            menu_title="Menu",  # Título do menu
            options=buttons,  # Usa a lista original de opções
            icons=["file-plus", "arrow-repeat", "list-task", "list",
                    "database", "bar-chart-line", "clipboard-check"],  # Ícones para cada opção
            menu_icon="menu-button",  # Ícone genérico para o menu
            default_index=0,  # Primeira opção selecionada por padrão
        )
    
    

    if selected_screen == 'Novo Orçamento':
        st.write('### Insira o Nome do Orçamento')
        # Definir os dados (apenas as colunas)
        dados_orc = pd.DataFrame(columns=["Pedido", "Revisão", #"Cliente", "Demandante Técnico", 
                                        #"Programa", "Área", "Título", "Referência", 
                                        "Data Base", "Moeda", "Orçamentista", 
                                        "Verificador", "Aprovador", "Principais Mudanças"])
        premissas = pd.DataFrame(columns= ['Premissas'])
        itens = pd.DataFrame(columns=["ID", 'N° Demandante', "Data Base", "Descrição", "Valor Orçado", "Moeda Orçada",
                                        'Referências', "Métrica Utilizada", "Fator", "Und Medida", 
                                        "Quantidade", "Classificação", "Subclassificação", "Data Atualização", "Categoria"])
        subitens = pd.DataFrame(columns=["ID Item", "ID Subitem", 'CONTRATO - ITEM',	'FORNECEDOR', 'DATA REFERÊNCIA', 'DESCRIÇÃO', 'NM',	
                                        'Und Medida', 'CLASSIFICACAO', 'SUBCLASSIFICACAO', 'FÓRMULA ATUALIZAÇÃO',	'VALOR LÍQUIDO REFERÊNCIA',
                                        'MOEDA REFERÊNCIA', 'Ultima Data Paridade', 'Valor Líquido Atualizado',	'Valor Atualizado Dolar', 
                                        'Valor Atualizado Euro', 'Valor Atualizado Real', 'Selecionar'])
        categorias = pd.DataFrame(columns=["Categoria"])
        new_orc = st.text_input('Pedido:')
        if new_orc != "":
            col1, col2, col3 = st.columns(3)
            with col1:
                col_revisao = st.text_input('Revisão:', value=0, disabled=True)
            with col2:
                col_data_orc = st.date_input('Data Base:', format='DD/MM/YYYY')
            with col3:
                col_moeda = st.selectbox('Moeda:', ['BRL', 'USD', 'EUR'])
            
            header = {"Pedido": new_orc, "Revisão": col_revisao, "Data Base": col_data_orc.strftime('%Y-%m-%d'), 
                        "Moeda": col_moeda, "Orçamentista": "", "Verificador": "", "Aprovador": "", "Principais Mudanças": ""}
            dados_orc = pd.concat([dados_orc, pd.DataFrame([header])], ignore_index=True)
            
            excel_data = criar_excel()
            st.download_button(
                    label="Gerar Orçamento",
                    data=excel_data,
                    file_name=f"{new_orc}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    # SEÇÃO DE ANALISES
    elif selected_screen == "Analises":
        st.write("### Análise de Dados")

        # Função de fábrica para inicializar o estado da sessão
        def initialize_session_state():
            return {
                "uploaded_file": None,
                "selected_column": None,
                "data": None
            }

        # Inicializa a sessão de estado para armazenar informações
        st.session_state.setdefault("analises_state", initialize_session_state())

        def load_uploaded_data(uploaded_file):
            """Função para carregar dados do arquivo anexado."""
            try:
                if uploaded_file.name.endswith(".csv"):
                    return pd.read_csv(uploaded_file)
                elif uploaded_file.name.endswith(".xlsx"):
                    return pd.read_excel(uploaded_file)
                else:
                    st.error("Formato de arquivo não suportado.")
                    return None
            except Exception as e:
                st.error(f"Erro ao carregar o arquivo: {e}")
                return None

        def validate_data(data):
            """Função para validar a estrutura dos dados."""
            if data is None or data.empty:
                st.error("Os dados estão vazios ou inválidos.")
                return None

            if not isinstance(data, pd.DataFrame):
                st.error("Os dados carregados não são um DataFrame válido.")
                return None

            return data

        # Botão para anexar planilha
        uploaded_file = st.file_uploader("Anexe a planilha para análise:", type=["csv", "xlsx"], key="analises_file_uploader")

        # Verifica se um novo arquivo foi carregado
        if uploaded_file is not None:
            # Atualiza o estado com o novo arquivo
            st.session_state["analises_state"]["uploaded_file"] = uploaded_file

            # Carrega os dados da planilha anexada
            data = load_uploaded_data(uploaded_file)

            # Valida os dados carregados
            data = validate_data(data)

            # Salva os dados no estado se válidos
            if data is not None:
                st.session_state["analises_state"]["data"] = data
        
        else:
            st.info("Por favor, anexe uma planilha para continuar.")
        
        # Recupera os dados do estado
        data = validate_data(st.session_state["analises_state"].get("data"))

        if data is not None:
            # Exibe os dados da planilha
            st.write("### Planilha Anexada:")
            st.dataframe(data)

            # Coluna para análise estatística
            numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_columns:
                column = st.selectbox(
                    "Selecione a coluna numérica para análise estatística:",
                    numeric_columns,
                    index=numeric_columns.index(st.session_state["analises_state"].get("selected_column")) if st.session_state["analises_state"].get("selected_column") in numeric_columns else 0
                )

                # Atualiza a coluna selecionada no estado
                st.session_state["analises_state"]["selected_column"] = column

                if column:
                    # Chama a função de análise estatística
                    statistical_analysis(data, column)
            else:
                st.warning("Nenhuma coluna numérica disponível para análise.")

    elif selected_screen == "Base de Dados":
        filtro_base_referencias(st.session_state.base_bens)
    else:
        @st.dialog("Alterar Moeda", width='small')
        def moeda_alterate():
            moeda = st.selectbox('Escolha a moeda', ['BRL', 'USD', 'EUR'])
            if st.button('Alterar'):
                st.session_state.dados_orc['Moeda'].iloc[-1] = moeda
                st.success('Moeda alterada com sucesso!')
                time.sleep(2)
                st.rerun()
        # Upload do arquivo de dados
        st.sidebar.write("### Upload de Dados")
        uploaded_file = st.sidebar.file_uploader("Faça o upload de um arquivo CSV ou Excel", type=["csv", "xls", "xlsx"], key='file_uploader')

        # Verifica se o arquivo foi carregado
        if uploaded_file is not None:
            
            col1, col2 = st.columns(2)
            with col1:
                col11, col12, col13 = st.columns(3)
                with col11:
                    # Botão para ressetar a sessão
                    if st.button('Resetar sessão'):
                        reset_session()
                with col12:
                    # Botão para alterar a moeda do orçamento
                    if st.button('Alterar Moeda'):
                        moeda_alterate()

            
            df = load_uploaded_data(uploaded_file)
            if df is not None:
                if df.columns[0] != 'Pedido':
                    st.error('Formato de documento não suportado, favor inserir outro orçamento.')
                st.write(f"## Você está na seção: {selected_screen}")
                if selected_screen == "Revisões":
                    display_input_budget(df)
                elif selected_screen == "Base de Dados":
                    search_columns = df.columns.tolist()
                    search_option = st.sidebar.selectbox("Pesquisar por:", search_columns)
                    search_query = st.sidebar.text_input("Digite o termo de busca")
                    display_filtered_data(df, search_option, search_query)
                elif selected_screen == "Itens":
                    display_crud_in_header(df)
                elif selected_screen == 'Consolidado':
                    consolidated()
                else:
                    st.write(f"Conteúdo fictício para a seção: {selected_screen}")
        else:
            st.info("Por favor, faça o upload de um orçamento gerado.")


orcamento()
