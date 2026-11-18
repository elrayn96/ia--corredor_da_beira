# Conformidade com o enunciado — Grupo 01

Este documento liga os requisitos obrigatórios aos componentes que os
implementam. Não substitui o relatório; serve para revisão e reprodução.

## Arquitectura

- `src/contrato_busca.py`: classe abstracta `Problema`, classe `No`, função
  `caminho` e adaptadores para os nomes históricos do projecto.
- `src/problema.py`: domínio da cadeia de frio, mantendo os métodos antigos
  usados pela interface e acrescentando o contrato formal.
- `src/estado.py`: estado formalmente imutável e hashable.
- `src/buscas/`: algoritmos genéricos, sem regras da cadeia de frio.

## Algoritmos

Estão disponíveis BFS, DFS com limite configurável, IDS, UCS, Gulosa, A* e A*
Ponderado. A implementação conserva LDS como funcionalidade adicional. O IDS
regista `nos_reexpandidos`; o UCS usa `heapq` e descarta entradas obsoletas.

## Instâncias e experiências

A semente obrigatória é `202601` (`2026 × 100 + 1`). Um único gerador é
inicializado com esse valor e avança para criar dez instâncias distintas por
nível em `dados/instancias_experimentais/`; todos os JSONs conservam o campo
`semente: 202601`. Cada instância mantém as sete
entregas e as quinze localidades; o tamanho cresce pelo número de alternativas
rodoviárias. O nível pequeno usa um corredor controlado com uma ligação
simulada explicitamente identificada no JSON.

Executar a bateria oficial:

```bash
python -m experiencias.bateria --limite 60 --quantidade-por-nivel 10
```

Cada resultado é guardado num checkpoint atómico. Uma nova execução retoma
automaticamente checkpoints com a mesma assinatura de instâncias e o mesmo
limite temporal; `--reiniciar` força uma campanha integral nova.

São produzidos:

- `resultados_experimentais/resultados.csv`;
- `resultados_experimentais/graficos/nos_expandidos_vs_dimensao.png`;
- `resultados_experimentais/graficos/tempo_vs_dimensao.png`;
- `resultados_experimentais/graficos/custo_vs_optimo.png`.

Cada execução é isolada e limitada a 60 segundos e 2 GB em sistemas que
disponibilizam `resource.RLIMIT_AS`. No Windows, a memória é medida com
`tracemalloc` e qualquer valor acima do limite é marcado como falha.

## Interface e controlo da execução

- A interface permite seleccionar directamente o nível Pequena, Média ou
  Grande e um dos dez casos desse nível.
- A busca corre num processo separado do Tkinter, mantendo menus, separadores e
  o botão **Terminar algoritmo** responsivos.
- Cancelamento manual e limite de tempo são registados como motivos distintos.
- Quando não existe solução completa, o painel Resultados apresenta o último
  estado explorado, além das métricas recolhidas até à interrupção.
- O separador **ASCII** apresenta cada estado e acção da solução numa sequência
  monoespaçada; o mapa e a árvore gráfica permanecem disponíveis.

## Exemplo: menor distância não é menor tempo

Na rede base:

| Critério | Percurso | Distância | Tempo |
|---|---|---:|---:|
| Menor distância | Beira–Dondo–Nhamatanda–Inchope–Chimoio–Catandica | 460 km | 398 min |
| Menor tempo | Beira–Dondo–Nhamatanda–Gorongosa–Muxunguè–Catandica | 480 km | 386 min |

O segundo percurso tem mais 20 km, mas é 12 minutos mais rápido devido às
velocidades associadas ao estado do piso.

## A* Ponderado

O CSV contém execuções com `w = 1.25, 1.5, 2, 3`, o custo óptimo de referência,
a razão `custo/custo_optimo` e o factor de ramificação efectivo `b_efetivo`.
Para uma heurística admissível, a análise verifica se a razão respeita o limite
teórico `custo/custo_optimo <= w` quando uma solução é encontrada.

## Testes

```bash
python -m pytest -q
python -m ruff check src main.py experiencias testes
```

`testes/test_conformidade_enunciado.py` cobre o contrato abstracto, `No`,
`caminho`, imutabilidade do estado, limite da DFS, reexpansões do IDS, igualdade
de custo entre A* e UCS, cadeia de frio, espera nocturna, geração das trinta
instâncias, factor de ramificação e o exemplo distância/tempo.

Uma selecção de quinze testes adequada à demonstração está documentada em
`docs/GUIA_DEMONSTRACAO_TESTES.md`.
