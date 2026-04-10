# rubrica_general.py

CRITERIOS = {
    "analisis_problema": {
        "nombre": "Análisis del problema",
        "descripcion": "Comprender la situación, identificar problema central y factores."
    },
    "decision_pedagogica": {
        "nombre": "Decisión pedagógica fundamentada",
        "descripcion": "Proponer acciones claras, implementables y pertinentes."
    },
    "fundamentacion": {
        "nombre": "Fundamentación pedagógica",
        "descripcion": "Sustentar con conceptos y enfoques pedagógicos."
    },
    "reflexion": {
        "nombre": "Nivel de reflexión sobre la práctica",
        "descripcion": "Analizar implicancias, justificar decisiones y mejorar."
    },
    "contexto": {
        "nombre": "Pertinencia contextual",
        "descripcion": "Ajustar decisiones al contexto real."
    }
}


NIVELES = {
    "Inicio": "Desempeño incipiente, descriptivo o sin sustento.",
    "En desarrollo": "Responde parcialmente, con limitaciones en profundidad o claridad.",
    "Logrado": "Respuesta adecuada, pertinente y fundamentada.",
    "Destacado": "Respuesta profunda, integrada, crítica y contextualizada."
}


RUBRICA_TEXTO = """
CRITERIOS DE EVALUACIÓN:

1. Análisis del problema:
- Inicio: Describe superficialmente la situación sin identificar el problema.
- En desarrollo: Identifica algunos elementos sin profundizar.
- Logrado: Analiza el problema con factores relevantes.
- Destacado: Analiza integralmente, estableciendo relaciones e implicancias.

2. Decisión pedagógica fundamentada:
- Inicio: No propone acciones o son vagas.
- En desarrollo: Propone acciones poco claras o incompletas.
- Logrado: Propone acciones claras y pertinentes.
- Destacado: Propone acciones estratégicas, contextualizadas y viables.

3. Fundamentación pedagógica:
- Inicio: No sustenta o lo hace incorrectamente.
- En desarrollo: Usa conceptos superficialmente.
- Logrado: Sustenta con conceptos pertinentes.
- Destacado: Integra referentes pedagógicos de forma sólida.

4. Nivel de reflexión:
- Inicio: Describe sin análisis.
- En desarrollo: Explica parcialmente.
- Logrado: Justifica decisiones pedagógicas.
- Destacado: Analiza implicancias y propone mejoras.

5. Pertinencia contextual:
- Inicio: No considera el contexto.
- En desarrollo: Considera el contexto de forma general.
- Logrado: Ajusta su propuesta al contexto.
- Destacado: Adapta estratégicamente al entorno.
"""