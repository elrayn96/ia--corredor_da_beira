
from tkinter import ttk

COLUNAS = (
    "ordem",
    "tipo",
    "origem",
    "destino",
    "tempo",
    "combustivel",
)

TITULOS = (
    "Ordem",
    "Tipo de acção",
    "Origem",
    "Destino",
    "Tempo",
    "Combustível",
)

METRICAS = (
    ("nos_gerados", "Nós gerados"),
    ("nos_expandidos", "Nós expandidos"),
    ("max_fronteira", "Máximo da fronteira"),
    ("nos_reexpandidos", "Nós reexpandidos"),
    ("comprimento_caminho", "Comprimento do caminho"),
    ("tempo_segundos", "Tempo de execução (s)"),
    ("memoria_pico_bytes", "Memória de pico (bytes)"),
)


def preparar_resultados(solucao, estatisticas):
    if solucao is None:
        return {
            "custo": "—",
            "numero_estados": "—",
            "numero_accoes": "—",
            "entregas": "—",
            "esperas": "—",
            "abastecimentos": "—",
            "percurso": "—",
            "estado_final": "Sem solução",
            "linhas": [],
            "metricas": preparar_metricas(estatisticas),
        }

    accoes = solucao.get_accoes()
    estados = solucao.get_estados()

    entregas = sum(
        accao.get_tipo() == "entregar"
        for accao in accoes
    )
    esperas = sum(
        accao.get_tipo() == "esperar"
        for accao in accoes
    )
    abastecimentos = sum(
        accao.get_tipo() == "abastecer"
        for accao in accoes
    )

    percurso = " → ".join(
        str(estado.get_localidade())
        for estado in estados
    )

    estado_final = estados[-1]

    descricao_final = (
        f"Localidade: {estado_final.get_localidade()} | "
        f"Tempo: {estado_final.get_tempo()} | "
        f"Combustível: {estado_final.get_combustivel()} | "
        f"Entregas concluídas: "
        f"{len(estado_final.get_entregas_concluidas())}"
    )

    linhas = []

    for indice, accao in enumerate(accoes):
        anterior = estados[indice]
        seguinte = estados[indice + 1]

        tipo = accao.get_tipo()
        origem = anterior.get_localidade()

        if tipo == "deslocar":
            destino = accao.get_parametro(
                "destino",
                seguinte.get_localidade()
            )
        elif tipo == "entregar":
            destino = accao.get_parametro(
                "supermercado",
                seguinte.get_localidade()
            )
        else:
            destino = "—"

        linhas.append((
            indice + 1,
            tipo,
            str(origem),
            str(destino),
            seguinte.get_tempo(),
            seguinte.get_combustivel(),
        ))

    return {
        "custo": solucao.get_custo_total(),
        "numero_estados": len(estados),
        "numero_accoes": len(accoes),
        "entregas": entregas,
        "esperas": esperas,
        "abastecimentos": abastecimentos,
        "percurso": percurso,
        "estado_final": descricao_final,
        "linhas": linhas,
        "metricas": preparar_metricas(estatisticas),
    }


def preparar_metricas(estatisticas):
    estatisticas = estatisticas or {}
    resultado = {}

    for chave, _ in METRICAS:
        valor = estatisticas.get(chave)

        if valor is None:
            resultado[chave] = "—"
        elif chave == "tempo_segundos":
            resultado[chave] = f"{valor:.6f}"
        else:
            resultado[chave] = str(valor)

    return resultado


class PainelResultados(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Cartao.TFrame")

        self.criar_componentes()
        self.limpar()

    def criar_componentes(self):
        self.resumo = ttk.LabelFrame(
            self,
            text="Resumo da solução", style="Cartao.TLabelframe"
        )
        self.resumo.pack(
            fill="x",
            padx=10,
            pady=5
        )

        self.label_custo = ttk.Label(self.resumo, style="Cartao.TLabel")
        self.label_estados = ttk.Label(self.resumo, style="Cartao.TLabel")
        self.label_accoes = ttk.Label(self.resumo, style="Cartao.TLabel")
        self.label_entregas = ttk.Label(self.resumo, style="Cartao.TLabel")
        self.label_esperas = ttk.Label(self.resumo, style="Cartao.TLabel")
        self.label_abastecimentos = ttk.Label(self.resumo, style="Cartao.TLabel")

        etiquetas_resumo = (
            self.label_custo,
            self.label_estados,
            self.label_accoes,
            self.label_entregas,
            self.label_esperas,
            self.label_abastecimentos,
        )

        for etiqueta in etiquetas_resumo:
            etiqueta.pack(
                anchor="w",
                padx=10,
                pady=2
            )

        self.metricas_frame = ttk.LabelFrame(
            self,
            text="◉  Estatísticas da busca", style="Cartao.TLabelframe"
        )
        self.metricas_frame.pack(
            fill="x",
            padx=10,
            pady=5
        )

        self.labels_metricas = {}

        for chave, titulo in METRICAS:
            etiqueta = ttk.Label(self.metricas_frame, style="Cartao.TLabel")
            etiqueta.pack(
                anchor="w",
                padx=10,
                pady=2
            )
            self.labels_metricas[chave] = etiqueta

        self.percurso_frame = ttk.LabelFrame(
            self,
            text="➜  Percurso", style="Cartao.TLabelframe"
        )
        self.percurso_frame.pack(
            fill="x",
            padx=10,
            pady=5
        )

        self.label_percurso = ttk.Label(
            self.percurso_frame,
            wraplength=850,
            justify="left", style="Cartao.TLabel"
        )
        self.label_percurso.pack(
            anchor="w",
            padx=10,
            pady=5
        )

        self.tabela_frame = ttk.LabelFrame(
            self,
            text="Percurso e acções", style="Cartao.TLabelframe"
        )
        self.tabela_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        )

        self.tabela = ttk.Treeview(
            self.tabela_frame,
            columns=COLUNAS,
            show="headings",
            height=8
        )

        for coluna, titulo in zip(COLUNAS, TITULOS):
            self.tabela.heading(
                coluna,
                text=titulo
            )
            self.tabela.column(
                coluna,
                width=120,
                minwidth=80,
                anchor="center"
            )

        barra_vertical = ttk.Scrollbar(
            self.tabela_frame,
            orient="vertical",
            command=self.tabela.yview
        )

        barra_horizontal = ttk.Scrollbar(
            self.tabela_frame,
            orient="horizontal",
            command=self.tabela.xview
        )

        self.tabela.configure(
            yscrollcommand=barra_vertical.set,
            xscrollcommand=barra_horizontal.set
        )

        self.tabela.grid(
            row=0,
            column=0,
            sticky="nsew"
        )
        barra_vertical.grid(
            row=0,
            column=1,
            sticky="ns"
        )
        barra_horizontal.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        self.tabela_frame.rowconfigure(
            0,
            weight=1
        )
        self.tabela_frame.columnconfigure(
            0,
            weight=1
        )

        self.estado_frame = ttk.LabelFrame(
            self,
            text="Estado final", style="Cartao.TLabelframe"
        )
        self.estado_frame.pack(
            fill="x",
            padx=10,
            pady=5
        )

        self.label_estado_final = ttk.Label(
            self.estado_frame,
            wraplength=850,
            justify="left", style="Cartao.TLabel"
        )
        self.label_estado_final.pack(
            anchor="w",
            padx=10,
            pady=5
        )

    def mostrar_resultados(self, solucao, estatisticas):
        dados = preparar_resultados(
            solucao,
            estatisticas
        )

        self.limpar()

        self.label_custo.config(
            text=f"Custo total: {dados['custo']}"
        )
        self.label_estados.config(
            text=f"Estados percorridos: {dados['numero_estados']}"
        )
        self.label_accoes.config(
            text=f"Acções: {dados['numero_accoes']}"
        )
        self.label_entregas.config(
            text=f"Entregas: {dados['entregas']}"
        )
        self.label_esperas.config(
            text=f"Esperas: {dados['esperas']}"
        )
        self.label_abastecimentos.config(
            text=f"Abastecimentos: {dados['abastecimentos']}"
        )

        self.label_percurso.config(
            text=dados["percurso"]
        )

        self.label_estado_final.config(
            text=dados["estado_final"]
        )

        for chave, titulo in METRICAS:
            valor = dados["metricas"][chave]
            self.labels_metricas[chave].config(
                text=f"{titulo}: {valor}"
            )

        for linha in dados["linhas"]:
            self.tabela.insert(
                "",
                "end",
                values=linha
            )

    def limpar(self):
        self.label_custo.config(
            text="Custo total: —"
        )
        self.label_estados.config(
            text="Estados percorridos: —"
        )
        self.label_accoes.config(
            text="Acções: —"
        )
        self.label_entregas.config(
            text="Entregas: —"
        )
        self.label_esperas.config(
            text="Esperas: —"
        )
        self.label_abastecimentos.config(
            text="Abastecimentos: —"
        )

        self.label_percurso.config(
            text="—"
        )

        self.label_estado_final.config(
            text="Estado final: —"
        )

        for chave, titulo in METRICAS:
            self.labels_metricas[chave].config(
                text=f"{titulo}: —"
            )

        for item in self.tabela.get_children():
            self.tabela.delete(item)
