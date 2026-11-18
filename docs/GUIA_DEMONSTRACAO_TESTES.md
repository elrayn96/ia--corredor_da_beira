# Guia curto para demonstrar os testes

Os testes automatizados encontram-se na pasta `testes/`. Para mostrar a
quantidade total e executar todos:

```bash
python -m pytest --collect-only -q
python -m pytest -v
```

O projecto possui mais do que os quinze testes exigidos. Para uma demonstração
curta no vídeo, estes quinze casos cobrem directamente os requisitos centrais:

1. `testes/test_problema.py::test_estado_inicial`
2. `testes/test_problema.py::test_deslocacao_para_dondo`
3. `testes/test_problema.py::test_sem_combustivel_para_deslocar`
4. `testes/test_nao_informadas.py::test_bfs_encontra_menor_numero_acoes`
5. `testes/test_nao_informadas.py::test_dfs_encontra_solucao`
6. `testes/test_nao_informadas.py::test_ucs_encontra_menor_custo`
7. `testes/test_nao_informadas.py::test_ids_encontra_solucao`
8. `testes/test_nao_informadas.py::test_sem_solucao`
9. `testes/test_informadas.py::test_a_star_h0_encontra_optimo`
10. `testes/test_informadas.py::test_gulosa_encontra_solucao_mas_nao_optima`
11. `testes/test_informadas.py::test_ponderada_respeita_limite_teorico`
12. `testes/test_conformidade_enunciado.py::test_a_star_e_ucs_devolvem_o_mesmo_custo`
13. `testes/test_heuristicas.py::test_admissibilidade_em_todos_os_estados_do_exemplo`
14. `testes/test_experiencias.py::test_bateria_define_limite_de_memoria_de_dois_gib`
15. `testes/test_painel_ascii.py::test_ascii_mostra_estados_accoes_e_dados_operacionais`

Para executar apenas este conjunto, pode-se copiar os identificadores acima
para o comando `python -m pytest -v`. No vídeo, é mais simples executar toda a
pasta e depois abrir dois ou três ficheiros para explicar o que é validado.
