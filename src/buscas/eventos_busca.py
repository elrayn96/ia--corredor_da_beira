TIPOS_EVENTO = (
    "inicio",
    "gerar",
    "expandir",
    "descartar",
    "reabrir",
    "objectivo"
)

CHAVES_EVENTO = (
    "tipo",
    "passo",
    "no_id",
    "pai_id",
    "estado",
    "accao",
    "profundidade",
    "g",
    "h",
    "f"
)

def emitir_evento (observador, evento):
    #Envia evento ao observador
    if observador is None:
        return
    if evento.get("tipo") not in TIPOS_EVENTO:
        raise ValueError(f"Tipo de Evento Inválido: {evento.get("tipo")!r}")
    em_falta = [chave for chave in CHAVES_EVENTO if chave not in evento]
    if em_falta:
        raise ValueError(f"Evento sem as chaves: {em_falta}")
    observador(evento)