PRIORIDAD_CRITERIOS = [
    "analisis_problema",
    "decision_pedagogica",
    "fundamentacion",
    "reflexion",
    "contexto"
]


def detectar_brechas(evaluacion):

    brechas = []

    for criterio, nivel in evaluacion.items():

        if nivel in ["Inicio", "En desarrollo"]:
            brechas.append(criterio)

    return brechas


def priorizar_brechas(brechas):

    ordenadas = sorted(
        brechas,
        key=lambda x: PRIORIDAD_CRITERIOS.index(x)
        if x in PRIORIDAD_CRITERIOS else 999
    )

    return ordenadas


def seleccionar_brechas(brechas_priorizadas, intento):

    if intento == 1:
        return brechas_priorizadas[:2]

    if intento == 2:
        return brechas_priorizadas[:1]

    return brechas_priorizadas