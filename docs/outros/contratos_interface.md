# Contratos da interface gráfica — Marco 2

## Stack

- Python 3.12
- Tkinter e ttk para a interface desktop
- Matplotlib para mapa, árvore de busca e gráficos
- Bibliotecas padrão do Python para comunicação entre módulos

## Convenções

- Identificadores em `snake_case`.
- Utilizar `accao` e `accoes`, nunca `acao` ou `acoes`.
- Preservar as interfaces públicas dos módulos existentes.
- Não implementar novamente os algoritmos dentro da interface.

## Contratos públicos dos componentes

**Configuração — Adila**

`obter_configuracao() -> dict`

Chaves acordadas: `instancia`, `algoritmo`, `heuristica`, `peso`, `limite`, `limite_maximo`.

**Mapa rodoviário — Adila**

- `mostrar_rede(rede)`
- `destacar_percurso(estados, accoes)`
- `limpar_percurso()`

**Resultados — Lúcia**

- `mostrar_resultados(solucao, estatisticas)`
- `limpar_resultados()`

**Árvore de busca — Elias**

- `carregar_eventos(eventos)`
- `mostrar_passo(indice)`
- `reiniciar_visualizacao()`

Cada evento deverá identificar, quando aplicável: `tipo`, `no_id`, `pai_id`, `estado`, `accao`, `profundidade`, `g`, `h` e `f`.

**Comparação — Naeem**

- `mostrar_comparacao(resultados)`
- `limpar_comparacao()`

**Serviço de execução — Armando**

`executar_busca(configuracao, observador=None)`

Deverá devolver um dicionário com as chaves:

- `solucao`
- `estatisticas`
- `eventos`
- `estado_execucao`

## Integração

Os componentes devem aceitar dados reais ou dados de exemplo sem depender directamente de `main.py`.

Nenhum membro deve alterar `main.py` ou `src/interface/janela_principal.py` sem coordenação prévia com Armando.

## Git

Branch-base: `interface/interface-integracao`.

Todos os membros devem criar as suas branches a partir da branch-base actualizada e abrir Pull Requests com destino a `interface/interface-integracao`, nunca directamente a `main`.