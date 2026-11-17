# Cadeia de Frio no Corredor da Beira

**Projecto P1 — Inteligência Artificial I | Universidade Eduardo Mondlane (UEM) | 2026**  
**Grupo 01 — Laboral**

> Aplicação de Inteligência Artificial para planificação e comparação de rotas de distribuição de produtos refrigerados no Corredor da Beira, em Moçambique.

## Índice

1. [Visão geral](#visão-geral)
2. [Objectivos](#objectivos)
3. [Âmbito e regras do problema](#âmbito-e-regras-do-problema)
4. [Modelação como problema de procura](#modelação-como-problema-de-procura)
5. [Algoritmos e heurísticas](#algoritmos-e-heurísticas)
6. [Funcionalidades da aplicação](#funcionalidades-da-aplicação)
7. [Tecnologias](#tecnologias)
8. [Instalação e configuração](#instalação-e-configuração)
9. [Execução](#execução)
10. [Estrutura do repositório](#estrutura-do-repositório)
11. [Experiências e avaliação](#experiências-e-avaliação)
12. [Testes e qualidade](#testes-e-qualidade)
13. [Equipa e responsabilidades](#equipa-e-responsabilidades)
14. [Colaboração e branches](#colaboração-e-branches)
15. [Limitações e notas](#limitações-e-notas)

## Visão geral

O transporte de produtos perecíveis exige o cumprimento simultâneo de restrições de tempo, combustível, acessibilidade rodoviária, horários de recepção e conservação térmica. Este projecto estuda o problema de distribuição de produtos refrigerados a supermercados localizados no **Corredor da Beira**, utilizando algoritmos clássicos de procura em espaços de estados.

O sistema recebe uma rede rodoviária e uma instância de distribuição, procura sequências válidas de deslocações e operações logísticas, e apresenta o percurso, os custos, as estatísticas e a evolução da procura. O propósito é **minimizar o tempo total de execução da missão**, respeitando todas as restrições.

O projecto é académico: os dados representam um cenário de estudo e não constituem um serviço operacional de navegação ou gestão logística em tempo real.

## Objectivos

### Objectivo geral

Modelar e resolver um problema de distribuição com cadeia de frio através de algoritmos de procura informada e não informada, comparando o seu desempenho e a qualidade das soluções.

### Objectivos específicos

- Representar localidades e estradas como um grafo com distâncias e qualidade do piso.
- Modelar estados, acções, transições, custos, objectivo e restrições.
- Implementar algoritmos de procura sem recorrer a bibliotecas que resolvam automaticamente o problema.
- Desenvolver e analisar heurísticas, incluindo admissibilidade e consistência.
- Gerar instâncias reproduzíveis de diferentes dimensões.
- Medir tempo, memória, nós gerados e expandidos, fronteira e custo da solução.
- Visualizar a rede, a rota seleccionada e a expansão da árvore de procura.
- Comparar algoritmos e produzir resultados experimentais reprodutíveis.

## Âmbito e regras do problema

O cenário base considera:

| Elemento | Regra |
| --- | --- |
| Origem e destino final | Beira |
| Partida | 05:00 |
| Entregas obrigatórias | 7 supermercados distintos |
| Duração de cada entrega | 30 minutos |
| Limite da cadeia de frio | 14 horas |
| Capacidade do depósito | 300 litros |
| Consumo | 0,35 litros/km |
| Postos de abastecimento | Beira, Inchope e Chimoio |
| Tempo de abastecimento | 20 minutos |
| Restrição de circulação | Proibido circular entre 22:00 e 05:00 |
| Rede | Pelo menos 15 localidades |

A velocidade depende da qualidade do piso:

| Piso | Velocidade |
| --- | ---: |
| 1 | 40 km/h |
| 2 | 55 km/h |
| 3 | 70 km/h |
| 4 | 80 km/h |
| 5 | 90 km/h |

Cada supermercado possui uma janela de atendimento. A solução deve realizar todas as entregas dentro das janelas permitidas e regressar à Beira. A procura pode considerar deslocação, entrega, abastecimento e espera, sempre de acordo com as regras de validade do estado.

**Função objectivo:** minimizar o custo total em minutos, incluindo deslocações, entregas, abastecimentos e esperas.

## Modelação como problema de procura

O espaço de estados descreve a situação logística em cada instante. Um estado contém, conceptualmente:

- `localidade`: posição actual do camião;
- `entregas_concluidas`: conjunto de supermercados já atendidos;
- `tempo`: minutos decorridos desde a partida;
- `combustivel`: quantidade de combustível disponível.

As acções possíveis são `deslocar`, `entregar`, `abastecer` e `esperar`. A aplicação do modelo de transição produz um novo estado e o respectivo custo temporal.

O teste de objectivo verifica se **todos os sete supermercados foram atendidos** e se o camião **regressou à Beira**. A validade de cada sucessor depende das regras de combustível, horários, circulação e cadeia de frio.

O domínio é implementado em módulos próprios (`src/estado.py`, `src/accao.py`, `src/problema.py` e `src/solucao.py`), separados dos algoritmos genéricos de procura.

## Algoritmos e heurísticas

### Procura não informada

- **LDS** — procura em profundidade limitada (*Limited Depth Search*).
- **BFS** — procura em largura (*Breadth-First Search*).
- **DFS** — procura em profundidade (*Depth-First Search*), com controlo de ciclos e limite configurável quando aplicável.
- **IDS** — aprofundamento iterativo (*Iterative Deepening Search*), incluindo contabilização de reexpansões.
- **UCS** — procura de custo uniforme (*Uniform-Cost Search*).

### Procura informada

- **Procura gulosa** (*Greedy Best-First Search*).
- **A\*** — utiliza `f(n) = g(n) + h(n)`.
- **A\* ponderada** — utiliza `f(n) = g(n) + w × h(n)`; pesos experimentais: **1,25; 1,5; 2; 3**.

### Heurísticas

- **`h0`**: heurística nula, `h(n) = 0`.
- **`h1`**: limite inferior baseado nas menores distâncias rodoviárias entre a posição actual, uma entrega pendente e a Beira, convertidas em tempo à velocidade máxima.
- **`h2`**: estimativa baseada numa árvore geradora mínima (*Minimum Spanning Tree*, MST) sobre os pontos ainda relevantes para a missão.

As heurísticas não substituem a verificação das restrições. O relatório analisa a sua admissibilidade e consistência, com demonstrações ou contra-exemplos conforme aplicável. A implementação dos algoritmos é própria; não se utiliza `networkx.shortest_path` nem outro resolvedor de procura pronto.

## Funcionalidades da aplicação

A interface gráfica desktop permite:

1. Seleccionar ou gerar uma instância de distribuição.
2. Escolher o algoritmo e os parâmetros aplicáveis. A heurística só é apresentada aos algoritmos informados. Definir o tempo máximo em segundos ou optar por uma busca sem limite temporal.
3. Executar a procura, acompanhar contagens de geração/expansão, visualizar a localidade em exploração no mapa e cancelar cooperativamente a operação.
4. Consultar o mapa rodoviário e destacar a rota encontrada.
5. Inspeccionar, passo a passo, as acções da solução e os estados sucessivos.
6. Visualizar uma **árvore de procura interactiva**, com sequência de expansões, fronteira e valores `g`, `h` e `f`, quando disponíveis.
7. Avançar e recuar por expansão completa (o nó pai e os filhos gerados no mesmo passo), reproduzir ou pausar, utilizar zoom com a roda do rato e mover a árvore por arrasto.
8. Consultar custo total, nós gerados e expandidos, fronteira máxima, duração e memória de pico.
9. Comparar algoritmos e consultar gráficos e resultados experimentais.

O mapa de estradas e a árvore de procura são visualizações diferentes: o primeiro mostra a rede física e o percurso; a segunda mostra como o algoritmo explorou o espaço de estados.

## Tecnologias

| Tecnologia | Utilização |
| --- | --- |
| Python 3 | Linguagem principal |
| Tkinter / `ttk` | Interface gráfica desktop |
| Matplotlib | Mapa, árvore de procura e gráficos |
| JSON | Rede, parâmetros e instâncias |
| CSV | Resultados experimentais |
| `heapq`, `collections` e outras bibliotecas padrão | Estruturas de dados para os algoritmos |
| `time.perf_counter` | Medição do tempo |
| `tracemalloc` | Medição da memória de pico |
| pytest | Testes automatizados |
| Ruff | Análise estática e estilo |
| Git e GitHub | Versionamento e revisão colaborativa |

**Não são utilizadas** Qt, PySide6, PySimpleGUI ou NetworkX como base da interface ou como resolvedores de caminhos.

## Instalação e configuração

### Pré-requisitos

- Python 3.11 ou superior, com `pip` e suporte a Tkinter. Recomenda-se Python 3.12 para reproduzir o ambiente da integração contínua.
- Git.
- Ambiente gráfico para executar a interface.

> Em algumas distribuições Linux, Tkinter precisa de ser instalado pelo gestor de pacotes do sistema (por exemplo, `sudo apt install python3-tk`).

### 1. Clonar o repositório

```bash
git clone https://github.com/elrayn96/ia--corredor_da_beira.git
cd ia--corredor_da_beira
```

### 2. Criar um ambiente virtual

**Windows / PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependências

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pytest ruff
```

`tkinter` faz parte da distribuição Python quando instalado com suporte a Tcl/Tk e não é normalmente instalado por `pip`.

### 4. Verificar o ambiente

```bash
python --version
python -m pytest -v
python -m ruff check src main.py experiencias
```

## Execução

### Abrir a aplicação gráfica

A partir da raiz do repositório:

```bash
python main.py
```

Na janela principal, seleccionar uma instância, escolher o algoritmo e, se aplicável, a heurística, o peso ou o limite. Em seguida, iniciar a procura. Os separadores da aplicação apresentam a rede rodoviária, a solução, a árvore de procura e as comparações.

### Gerar uma instância

```bash
python -m src.gerador
```

O gerador utiliza uma semente para permitir a reprodução das instâncias. A semente de referência do **Grupo 01** é `202601` (`2026 × 100 + 1`).

### Executar experiências

```bash
python -m experiencias.executar
```

Os resultados são organizados em CSV e gráficos. As opções exactas de execução em lote, quando disponíveis, podem ser consultadas na ajuda do respectivo módulo.

## Estrutura do repositório

A árvore seguinte descreve a **organização-alvo da versão final**, incluindo os componentes da interface e da integração. Alguns ficheiros são produzidos nas etapas de desenvolvimento e podem não existir em branches anteriores.

```text
ia--corredor_da_beira/
├── .github/
│   └── workflows/
│       └── ci.yml                    # Integração contínua
├── dados/
│   ├── localidades.json             # Localidades da rede
│   ├── estradas.json                # Instâncias geradas
│   └── instancias_testes/           # Instâncias de validação
|       └──teste.json 
├── docs/
│   ├── contratos_interface.md       # Contratos entre componentes
│   ├── relatorio/                   # Relatório académico
│   └── prompts/                     # Registos de apoio documental
├── experiencias/
│   ├── executar.py                  # Execução em lote e medições
│   ├── resultados.py                # Consolidação e gráficos
│   └── resultados/                  # CSV e gráficos produzidos
├── src/
│   ├── __init__.py
│   ├── accao.py                      # Acções válidas
│   ├── estado.py                     # Representação do estado
│   ├── problema.py                   # Regras, objectivo e sucessores
│   ├── solucao.py                    # Solução e custo total
│   ├── gerador.py                    # Geração e conversão de instâncias
│   ├── buscas/
│   │   ├── __init__.py
│   │   ├── nao_informadas.py         # BFS, DFS, IDS e UCS
│   │   ├── informadas.py             # Gulosa, A* e A* ponderada
│   │   └── eventos_busca.py          # Contrato dos eventos de procura
│   ├── heuristicas/
│   │   ├── __init__.py
│   │   ├── distancia.py              # h0 e h1
│   │   └── mst.py                    # h2
│   ├── servicos/
│   │   ├── __init__.py
│   │   ├── executar_busca.py         # Orquestração da execução
│   │   └── validar_solucao.py        # Verificação da solução
│   └── interface/
│       ├── __init__.py
│       ├── janela_principal.py       # Janela e navegação
│       ├── painel_configuracao.py    # Parâmetros de execução
│       ├── mapa_rodoviario.py        # Visualização da rede e rota
│       ├── painel_resultados.py      # Passos e estatísticas
│       ├── arvore_busca.py           # Expansões interactivas
│       └── painel_comparacao.py      # Comparação de algoritmos
├── testes/
│   ├── test_accao.py
│   ├── test_estado.py
│   ├── test_problema.py
│   ├── test_solucao.py
│   ├── test_heuristicas.py
│   ├── test_informadas.py
│   ├── test_servicos.py
│   ├── test_eventos_busca.py
│   ├── test_mapa_rodoviario.py
│   ├── test_painel_resultados.py
│   └── test_experiencias.py
├── tests/
│   └── test_gerador.py              # Testes existentes do gerador
├── main.py                          # Ponto de entrada da aplicação
├── requirements.txt                 # Dependências Python
└── README.md                        # Este documento
```

Os módulos auxiliares legados (`src/custos.py`, `src/transicoes.py` e `src/buscas/weight_astar.py`) podem permanecer no repositório durante a consolidação, desde que não criem implementações duplicadas ou divergentes.

## Experiências e avaliação

O protocolo experimental prevê **três níveis de dimensão** (pequeno, médio e grande), com **dez instâncias aleatórias por nível**, geradas com sementes reproduzíveis. Cada execução está sujeita aos limites definidos no enunciado: **60 segundos e 2 GB de memória**.

Para cada combinação de algoritmo e instância, recolhem-se:

| Métrica | Significado |
| --- | --- |
| `custo_total` | Tempo total da solução, em minutos |
| Comprimento do caminho | Número de acções da solução |
| Nós gerados | Estados/nós criados durante a procura |
| Nós expandidos | Nós cujos sucessores foram explorados |
| Fronteira máxima | Maior dimensão da estrutura de nós pendentes |
| Tempo | Duração medida com `time.perf_counter()` |
| Memória de pico | Valor medido com `tracemalloc` |
| Reexpansões | Métrica adicional relevante para IDS |

As análises incluem três gráficos principais: **nós expandidos × dimensão** (escala logarítmica), **tempo × dimensão** e **custo encontrado × custo óptimo de referência**. O relatório também discute o **factor de ramificação efectivo (`b*`)**, a qualidade das heurísticas e o compromisso entre custo e recursos computacionais.

A existência de uma instância gerada não garante, por si só, que ela possua solução: o gerador e o processo de validação devem assegurar instâncias utilizáveis para as experiências.

## Testes e qualidade

Executar toda a bateria de testes:

```bash
python -m pytest -v
```

Verificar estilo e problemas detectáveis estaticamente:

```bash
python -m ruff check src main.py experiencias
```

Os testes abrangem o domínio, o gerador, as heurísticas, os algoritmos, os serviços e os contratos dos componentes. Testes de interface devem evitar depender de um monitor gráfico em ambientes de CI sem servidor de visualização.

A integração contínua é configurada em `.github/workflows/ci.yml`. Experiências demoradas devem ser executadas separadamente da bateria rápida de validação de Pull Requests.

## Equipa e responsabilidades

**Universidade Eduardo Mondlane — Grupo 01, Laboral (2026)**

| Integrante | Responsabilidade principal | Contribuições |
| --- | --- | --- |
| **Armando** | Coordenação, domínio e integração | Modelação do problema, estados e regras, serviços de execução e validação, janela principal, integração de módulos, documentação e revisão de PRs |
| **Elias** | Procura informada e visualização da exploração | Gulosa, A*, A* ponderada, eventos de procura, árvore interactiva, métricas e testes associados |
| **Naeem** | Heurísticas e avaliação experimental | Heurísticas e análise de propriedades, protocolo experimental, métricas, gráficos e painel de comparação |
| **Adila** | Dados, geração e mapa | Rede rodoviária, localidades, instâncias, painel de configuração, mapa interactivo e destaque do percurso |
| **Lúcia** | Procura não informada e apresentação da solução | BFS, DFS, IDS, UCS, painel de resultados, passos da solução, eventos de procura e testes associados |

A atribuição indica **responsabilidade principal**, não exclusividade de contribuição. Alterações a contratos partilhados devem ser discutidas com o grupo.

### Resumo das tarefas por integrante

**Armando:** define o modelo e as regras do domínio, coordena a arquitectura, prepara os contratos entre módulos, integra a interface e os algoritmos, verifica soluções e mantém o fluxo de revisão.

**Elias:** implementa e aperfeiçoa as procuras informadas, fornece eventos estruturados de expansão e desenvolve a visualização interactiva da árvore de procura.

**Naeem:** desenvolve e avalia heurísticas, organiza as experiências reproduzíveis, recolhe métricas e apresenta comparações quantitativas entre algoritmos.

**Adila:** mantém os dados geográficos e rodoviários, gera instâncias de teste e desenvolve os controlos de configuração e a visualização do mapa e da rota.

**Lúcia:** implementa as procuras não informadas, regista estatísticas e eventos compatíveis com o visualizador e apresenta os resultados e a sequência de acções.

## Colaboração e branches

O desenvolvimento utiliza branches temáticas e Pull Requests sujeitos a revisão. Na fase de implementação da interface, a branch de integração é:

```text
interface/interface-integracao
```

Branches de trabalho:

```text
interface/mapa-configuracao          # Adila
interface/arvore-eventos             # Elias
interface/comparacao-experiencias    # Naeem
interface/resultados-nao-informadas  # Lúcia
```

Todos os colaboradores criam a sua branch **a partir de `interface/interface-integracao`**, e não directamente de `main`. Os Pull Requests da fase de interface devem ter **`interface/interface-integracao` como branch de destino**. Após revisão, testes e integração, a branch de integração poderá ser submetida a `main`.

Exemplo de criação de branch:

```bash
git fetch origin
git switch -c interface/mapa-configuracao origin/interface/interface-integracao
```

Convenções do código: **AO90**, identificadores em **`snake_case`**, `accao`/`accoes` e `custo_total`. Os componentes da interface devem respeitar os contratos documentados em `docs/contratos_interface.md`.

## Limitações e notas

- O sistema utiliza uma rede e instâncias de estudo; não incorpora tráfego ou condições meteorológicas em tempo real.
- A solução de menor custo depende do modelo, da validade dos dados e das garantias do algoritmo e da heurística utilizados.
- Algoritmos de procura não informada e procura gulosa não garantem necessariamente o menor custo temporal neste domínio.
- A* ponderada pode trocar optimalidade por desempenho, dependendo do peso e das condições aplicáveis.
- A documentação descreve a **arquitectura final prevista**. Ao utilizar uma branch intermédia, confirmar a presença dos módulos, opções de execução e resultados correspondentes.

---

**Projecto académico — Inteligência Artificial I · Universidade Eduardo Mondlane · 2026**


## Submissão ao docente (18 de Novembro de 2026)

A entrega do Grupo 01 é efectuada por **um único elemento**, até **quarta-feira, 18 de Novembro de 2026, às 23h59**, através do Assignment disponibilizado no Vula. Devem ser submetidos:

1. **Relatório em PDF**, com identificação clara de todos os membros. O ficheiro-fonte Word está em `docs/relatorio/IA_RELATORIO_GRUPO_01_LAB.docx`.
2. **Vídeo de apresentação e demonstração**, preferencialmente em MP4, substituindo a defesa presencial.
3. **Link de acesso ao sistema** ou **link do repositório/pacote do projecto**, incluindo a base de dados do cenário (`dados/`).

Se o vídeo ou os ficheiros ultrapassarem os limites do Vula, podem ser partilhados por Google Drive, desde que o docente disponha das permissões de acesso. Antes do prazo, o grupo deve confirmar a integridade de todos os ficheiros e a acessibilidade dos links.

### Utilização dos controlos gráficos

- **Gerar nova instância** cria e selecciona automaticamente um JSON; a ficha verde apresenta a instância activa. A indicação de viabilidade não substitui uma busca que confirme uma solução.
- **Tempo máximo (s)** determina o limite cooperativo de execução. A opção **Sem limite de tempo** desactiva o prazo, mas não torna a busca ilimitada em memória.
- **Executar busca / Cancelar busca** partilham o mesmo botão. Os parâmetros são bloqueados durante uma execução; os separadores mantêm-se acessíveis para consulta.
- **Árvore de busca:** os controlos situam-se acima do desenho. Um avanço revela a expansão de um nó com os filhos correspondentes. A roda do rato amplia/reduz a vista, o arrasto move-a e o botão de ajuste repõe o enquadramento.
- **Mapa:** durante uma busca, um anel assinala a localidade do último estado expandido; este sinal não deve ser confundido com a rota da solução, apresentada apenas quando é encontrada e validada.

### Limitações verificadas

A geração de instâncias assegura consistência estrutural, mas **não garante uma solução viável** para todas as sementes. A procura pode ser interrompida por limite de tempo e a árvore limita os eventos retidos para controlar a memória. O desempenho depende da instância, do algoritmo e do computador; não se deve interpretar uma execução interrompida como prova de inexistência de solução.
