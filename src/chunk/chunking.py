import json
import os
import re
import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter


def processar_chunks(tamanho: int = 400, overlap: int = 80):
    """
    Funcao principal que le os dados brutos do paciente e da bula,
    extrai e formata o histórico clinico, realiza o chunking
    do texto da bula por tokens e salva o resultado estruturado em JSON.
    """
    # Caminhos de entrada e saída do projeto
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_path = os.path.join(base_dir, "data", "processed", "dados_paciente.json")
    output_path = os.path.join(base_dir, "data", "processed", "dados_paciente_chunk.json")

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em {input_path}")
        return

    # Extração das variaveis base
    bula = data["bulas"][0]
    target_med = bula["medicamento"]
    paciente = data["dados_pessoais"]
    patient_id = data["metadata"]["patient_id"]

    # Extrai as condições médicas e ordena por data
    condicoes = []
    for c in data.get("condicoes", []):
        disease = c.get("description_pt")
        start_date = c.get("start")
        if disease and start_date:
            condicoes.append(f"{start_date}: {disease}")
    condicoes = sorted(list(set(condicoes)))

    # Extrai o histórico de medicamentos e define o período de uso
    medicamentos = []
    for m in data.get("medicamentos", []):
        med_name = m.get("description_pt")
        start_date = m.get("start")
        end_date = m.get("stop")

        if med_name and start_date:
            t_start = start_date.split("T")[0]
            if end_date:
                t_end = end_date.split("T")[0]
                medicamentos.append(f"[{t_start} até {t_end}]: {med_name}")
            else:
                medicamentos.append(f"[{t_start} até Uso Contínuo]: {med_name}")
    medicamentos = sorted(list(set(medicamentos)))

    # Extrai o histórico de consultas realizadas pelo paciente
    consultas = []
    for c in data.get("consultas", []):
        start_date = c.get("start")
        reason = c.get("reasondescription_pt") or c.get("description_pt") or "Consulta Geral"
        if start_date:
            t_start = start_date.split("T")[0]
            consultas.append(f"{t_start}: {reason}")
    consultas = sorted(list(set(consultas)))

    # Extrai os procedimentos clínicos realizados
    procedimentos = []
    for p in data.get("procedimentos", []):
        proc_name = p.get("description_pt") or p.get("description")
        proc_date = p.get("start") or p.get("date")
        if proc_name and proc_date:
            t_date = proc_date.split("T")[0]
            procedimentos.append(f"{t_date}: {proc_name}")
    procedimentos = sorted(list(set(procedimentos)))

    # Extrai observações gerais, sinais vitais e exames laboratoriais
    observacoes = []
    obs_list = data.get("observacoes", [])
    for o in obs_list:
        obs_type = o.get("description_pt")
        value = o.get("value_pt")
        unit = (o.get("units") or "").replace("{score}", "pontos")
        obs_date = o.get("date")

        if obs_type and value and obs_date:
            t_date = obs_date.split("T")[0]
            if unit:
                observacoes.append(f"{t_date}: {obs_type} = {value} {unit}")
            else:
                observacoes.append(f"{t_date}: {obs_type} = {value}")
    observacoes = sorted(list(set(observacoes)))

    # Busca os registros mais recentes de Peso e Altura do paciente
    peso_atual = next((o["value_pt"] for o in reversed(obs_list) if o["description_pt"] == "Peso corporal"),
                      "Não registrado")
    altura_atual = next((o["value_pt"] for o in reversed(obs_list) if o["description_pt"] == "Altura do corpo"),
                        "Não registrado")

    # Inicializa o tokenizador do tiktoken para contar o tamanho do texto por tokens para LLM
    tokenizer = tiktoken.get_encoding("cl100k_base")

    # Configuracao do chunking, tamanho e overlap
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=tamanho,
        chunk_overlap=overlap,
        length_function=lambda text: len(tokenizer.encode(text)),
        separators=["\n\n", ". ", "\n", " "]
    )

    chunks_gerados = []
    bula_idx = 1

    # Percorre cada página da bula para aplicar a limpeza de texto e o fatiamento
    for p in bula.get("paginas", []):
        page_num = p["pagina"]
        page_text = p["texto"]

        # Limpeza: remove sequências longas de pontos e espaços duplicados
        cleaned_text = re.sub(r'\.{3,}', ' ', page_text)
        final_text = re.sub(r' +', ' ', cleaned_text).strip()

        if not final_text:
            continue

        # Divide o texto limpo da página nos chunks menores configurados
        page_chunks = splitter.split_text(final_text)

        # Monta a estrutura final de cada chunk com o histórico mapeado do paciente nos metadados
        for text_chunk in page_chunks:
            chunk_structure = {
                "chunk_id":(f"{patient_id}"
                            f"::bula"   
                            f"::chunk_{bula_idx:03d}"),
                "text": text_chunk.strip(),
                "metadata": {
                       "patient_id": patient_id,

                    "tipo_documento": "bula",

                    "fonte": "bula",

                    "medicamento_bula_alvo":
                        target_med,

                    "pagina_origem":
                        page_num,

                    "chunk_number":
                        bula_idx,
                    # "patient_id": patient_id,
                    # "paciente_nome": paciente["nome_completo"],
                    # "paciente_genero": paciente["gender"],
                    # "paciente_data_nascimento": paciente["birthdate"],
                    # "medicamento_bula_alvo": target_med,
                    # "paciente_historico_diagnosticos": condicoes,
                    # "paciente_medicamentos_historico": medicamentos,
                    # "paciente_historico_consultas": consultas,
                    # "paciente_historico_procedimentos": procedimentos,
                    # "paciente_historico_observacoes": observacoes,
                    # "paciente_ultimo_peso_kg": peso_atual,
                    # "paciente_ultima_altura_cm": altura_atual,
                    # "pagina_origem": page_num,
                    # "chunk_number": global_idx,
                    # "total_chunks": 0
                }
            }
            chunks_gerados.append(chunk_structure)
            bula_idx += 1
    secoes_prontuario = []

    # Dados pessoais
    dados_pessoais_texto = (
        "Dados do paciente:\n"
        f"Nome: {paciente.get('nome_completo', 'Não informado')}\n"
        f"Gênero: {paciente.get('gender', 'Não informado')}\n"
        f"Data de nascimento: {paciente.get('birthdate', 'Não informado')}"
    )

    secoes_prontuario.append(
        (
            "dados_pessoais",
            dados_pessoais_texto
        )
    )

    # Diagnósticos
    if condicoes:

        texto = (
            "Histórico de diagnósticos do paciente:\n"
            + "\n".join(condicoes)
        )

        secoes_prontuario.append(
            (
                "diagnosticos",
                texto
            )
        )

    # Cria um histórico de medicamentos utilizados pelo paciente, caso tenha.
    if medicamentos:

        texto = (
            "Histórico de medicamentos do paciente:\n"
            + "\n".join(medicamentos)
        )

        secoes_prontuario.append(
            (
                "medicamentos",
                texto
            )
        )

    # Cria um histórico de consultas realizadas pelo paciente, caso tenha.
    if consultas:

        texto = (
            "Histórico de consultas do paciente:\n"
            + "\n".join(consultas)
        )

        secoes_prontuario.append(
            (
                "consultas",
                texto
            )
        )

    # Cria um histórico de procedimentos realizados pelo pacientes, caso tenha
    if procedimentos:

        texto = (
            "Histórico de procedimentos do paciente:\n"
            + "\n".join(procedimentos)
        )

        secoes_prontuario.append(
            (
                "procedimentos",
                texto
            )
        )

    # Adiciona observações clínicas e exames laboratoriais
    if observacoes:

        texto = (
            "Histórico de observações clínicas "
            "e exames do paciente:\n"
            + "\n".join(observacoes)
        )

        secoes_prontuario.append(
            (
                "observacoes",
                texto
            )
        )

    # Dados atuais
    medidas_texto = (
        "Medidas mais recentes do paciente:\n"
        f"Último peso registrado: {peso_atual} kg\n"
        f"Última altura registrada: {altura_atual} cm"
    )

    secoes_prontuario.append(
        (
            "medidas",
            medidas_texto
        )
    )

   #Cria o chunking do prontuário do paciente, com base nas seções extraídas e estruturadas
    prontuario_idx = 1

    for categoria, texto_secao in secoes_prontuario:

        chunks_secao = splitter.split_text(
            texto_secao
        )

        for text_chunk in chunks_secao:

            chunk_structure = {

                "chunk_id": (
                    f"{patient_id}"
                    f"::prontuario"
                    f"::chunk_{prontuario_idx:03d}"
                ),

                "text": text_chunk.strip(),

                "metadata": {

                    "patient_id":
                        patient_id,

                    "tipo_documento":
                        "prontuario",

                    "fonte":
                        "prontuario_paciente",

                    "categoria_prontuario":
                        categoria,

                    "chunk_number":
                        prontuario_idx,
                }
            }

            chunks_gerados.append(
                chunk_structure
            )

            prontuario_idx += 1

    #Total de chunks gerados, partindo das informações do prontuário e da bula do paciente
    total_chunks = len(
        chunks_gerados
    )

    total_bula = sum(
        1
        for chunk in chunks_gerados
        if chunk["metadata"]["tipo_documento"]
        == "bula"
    )

    total_prontuario = sum(
        1
        for chunk in chunks_gerados
        if chunk["metadata"]["tipo_documento"]
        == "prontuario"
    )


    # Atualiza o total de chunks em todos os metadados gerados
    for chunk in chunks_gerados:
        chunk["metadata"]["total_chunks"] = total_chunks

    # Salva o arquivo final estruturado pronto para a base vetorial
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks_gerados, f, ensure_ascii=False, indent=2)
    print(f"Chunks da bula: "f"{total_bula}")

    print(f"Chunks do prontuário: "f"{total_prontuario}")

    print(f"Total de chunks: "f"{total_chunks}")
    print(f"Arquivo salvo em: {output_path}")


if __name__ == "__main__":
    processar_chunks()
