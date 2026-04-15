import os
import json
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

from motor_reglas import detectar_brechas, priorizar_brechas, seleccionar_brechas
from rubrica_general import RUBRICA_TEXTO
from casos import CASOS_FEEDBACK
from dotenv import load_dotenv

load_dotenv()

#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-4.1-mini"

from openai import AzureOpenAI
import os

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint="https://Minedu-IA.openai.azure.com"
)

embedder = SentenceTransformer("all-MiniLM-L6-v2")


def similitud(respuesta, expected):

    if not expected:
        return 0

    emb = embedder.encode([respuesta, expected])

    sim = cosine_similarity([emb[0]], [emb[1]])[0][0]

    return float(sim)


def map_level(sim):

    if sim < 0.30:
        return "Insuficiente"

    if sim < 0.55:
        return "En proceso"

    if sim < 0.75:
        return "Satisfactorio"

    return "Destacado"


def analizar_criterios(pregunta, respuesta):

    prompt = f"""
Analiza la respuesta según criterios:

analisis_problema
decision_pedagogica
fundamentacion
reflexion
contexto

Devuelve JSON:

{{
"analisis_problema":"",
"decision_pedagogica":"",
"fundamentacion":"",
"reflexion":"",
"contexto":""
}}

Pregunta:
{pregunta}

Respuesta:
{respuesta}
"""

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Evaluador pedagógico MINEDU"},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return json.loads(completion.choices[0].message.content)


def generar_feedback(pregunta, respuesta, brechas, intento, nombre_usuario):

    if intento == 1:
        print('Dando retro a intento 1')
        prompt = f"""
Eres formador del MINEDU especializado en acompañamiento pedagógico a docentes.

Dirígete directamente al participante llamado {nombre_usuario}, usando un tono cercano, respetuoso y profesional. Intenta usar su nombre para dirigirte.

Analiza la respuesta del participante considerando las siguientes brechas identificadas:
{brechas}

Debes elaborar una retroalimentación pedagógica que internamente considere:

- una valoración inicial del esfuerzo o aspectos logrados,
- una explicación conceptual que ayude a comprender mejor el tema,
- orientaciones claras para mejorar la respuesta,
- y una pregunta que invite a profundizar la reflexión.

Sin embargo, para la presentación mantén la estructura sin mostrar los titulos de los elementos.

IMPORTANTE:
- Menciona el nombre "{nombre_usuario}" de forma natural al inicio o dentro del texto.
- Evita repetir el nombre en exceso.
- Mantén un tono humano, como conversación formativa.

Pregunta del caso:
{pregunta}

Respuesta del participante:
{respuesta}

Genera una retroalimentación clara, respetuosa y personalizada.
"""

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Evaluador pedagógico"},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return completion.choices[0].message.content

def generar_feedback_segundo_intento(
    pregunta,
    respuesta_anterior,
    respuesta_actual,
    brechas_intento1,
    nombre_usuario
):
    print('Dando retro a intento 2')
    prompt = f"""
Eres formador del MINEDU especializado en acompañamiento pedagógico a docentes.

Esta es la SEGUNDA interacción con el participante.

Primero revisa la respuesta del intento 1 y las brechas detectadas.
Luego analiza la nueva respuesta del intento 2.

Dirígete directamente al participante llamado {nombre_usuario}.

Pregunta del caso:
{pregunta}

Respuesta del intento 1:
{respuesta_anterior}

Brechas identificadas en el intento 1:
{brechas_intento1}

Nueva respuesta del participante (intento 2):
{respuesta_actual}

TAREA PEDAGÓGICA:

1. Identifica si el participante logró mejorar los aspectos señalados.
2. Reconoce explícitamente los avances logrados.
3. Señala si aún quedan aspectos por fortalecer.
4. Ofrece una orientación final para consolidar el aprendizaje.

REGLAS:

- Mantén una retroalimentación pedagógica y respetuosa.
- Usa obligatoriamente el nombre del usuario para la retroalimentación
- NO menciones "brechas" explícitamente.
- NO menciones "intento 1" ni "intento 2".
- Escribe como un formador que acompaña el aprendizaje.

La retroalimentación debe mantener esta lógica interna:

• reconocimiento de mejora  
• valoración del nivel alcanzado  
• orientación final para consolidar el aprendizaje

Pero **sin mostrar los títulos**.

Genera un texto fluido y natural.
"""

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Formador pedagógico experto MINEDU"},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return completion.choices[0].message.content

def evaluar_respuesta(pregunta, respuesta, pregunta_id, intento, feedback_id):

    caso = CASOS_FEEDBACK.get(str(feedback_id), "")
    print('----------------------------caso----------------')
    print(caso)
    prompt = f"""
Eres evaluador experto del Programa Formación de Formadores del MINEDU.

CASO PEDAGÓGICO:
{caso}

RÚBRICA OFICIAL:
{RUBRICA_TEXTO}

PREGUNTA:
{pregunta}

RESPUESTA DEL PARTICIPANTE:
{respuesta}

TAREA:

1. Evalúa la respuesta en los 5 criterios.
2. Identifica el nivel global alcanzado:
   Inicio / En desarrollo / Logrado / Destacado

3. Detecta las principales brechas (máximo 2).
4. Genera retroalimentación formativa.

REGLAS:

- NO menciones niveles en la retroalimentación.
- NO muestres criterios explícitamente.
- Enfócate en mejora pedagógica.
- Escribe como formador.

SALIDA:

Nivel: (Inicio / En desarrollo / Logrado / Destacado)

Retroalimentación:
- Valoración inicial
- Fundamentación conceptual
- Orientaciones de mejora
- Pregunta de profundización
"""

    completion = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "Evaluador pedagógico experto MINEDU"},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    texto = completion.choices[0].message.content

    # Extraer nivel automáticamente
    nivel = "No identificado"

    for n in ["Inicio", "En desarrollo", "Logrado", "Destacado"]:
        if n.lower() in texto.lower():
            nivel = n
            break

    return {
        "similarity_score": None,
        "nivel_estimado": nivel,
        "brechas": texto,        
    }