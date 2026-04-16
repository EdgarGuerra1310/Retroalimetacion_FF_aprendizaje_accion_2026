from flask import Flask, request, render_template
import requests
import time
import re
from bs4 import BeautifulSoup

from evaluador_ia import evaluar_respuesta
from evaluador_ia import generar_feedback, generar_feedback_segundo_intento
from db import guardar_evaluacion, obtener_evaluacion_existente
from collections import defaultdict
import os
from dotenv import load_dotenv

load_dotenv()

MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")
MOODLE_DOMAIN = os.getenv("MOODLE_DOMAIN")

app = Flask(__name__)


# ---------------------------------------------------
# TRAER INTENTOS DEL QUIZ
# ---------------------------------------------------
def respuesta_invalida(respuesta):

    if not respuesta:
        return True

    texto = respuesta.strip().lower()

    # Muy corta
    if len(texto) < 5:
        return True

    # Respuestas típicas vacías
    respuestas_basura = ["ok", "si", "sí", "no", "nose", "no se", "nada"]
    if texto in respuestas_basura:
        return True

    # Solo símbolos
    if re.fullmatch(r"[\W_]+", texto):
        return True

    # 🔥 NUEVO: repetición de un solo carácter
    if len(set(texto)) == 1 and len(texto) > 3:
        return True

    # Detectar texto tipo "asdfasdf", "qwerty"
    letras = re.sub(r"[^a-z]", "", texto)
    if len(letras) > 8:
        vocales = sum(1 for c in letras if c in "aeiou")
        ratio = vocales / len(letras)

        if ratio < 0.2:
            return True

    return False

def feedback_reconduccion(nombre_usuario):

    return f"""
{nombre_usuario}, parece que tu respuesta aún no desarrolla una idea clara sobre la situación planteada.

Te animo a volver a leer el caso con atención y responder considerando:

- ¿Qué está ocurriendo en la situación?
- ¿Qué decisión pedagógica tomarías?
- ¿Por qué sería pertinente en ese contexto?

Intenta expresar tu idea con mayor claridad y detalle para poder acompañarte mejor en tu proceso de aprendizaje.
"""


def get_attempts(quizid, userid):

    url = f"{MOODLE_DOMAIN}/webservice/rest/server.php"

    params = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": "mod_quiz_get_user_attempts",
        "quizid": quizid,
        "userid": userid,
        "status": "all",
        "moodlewsrestformat": "json"
    }

    return requests.get(url, params=params).json()


# ---------------------------------------------------
# TRAER PREGUNTAS DEL INTENTO
# ---------------------------------------------------

def get_attempt_review(attemptid):

    url = f"{MOODLE_DOMAIN}/webservice/rest/server.php"

    params = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": "mod_quiz_get_attempt_review",
        "attemptid": attemptid,
        "page": -1,
        "moodlewsrestformat": "json"
    }

    return requests.get(url, params=params).json()


# ---------------------------------------------------
# LIMPIAR HTML
# ---------------------------------------------------

def limpiar_html(texto):

    if not texto:
        return ""

    soup = BeautifulSoup(texto, "html.parser")
    return soup.get_text(" ", strip=True)


# ---------------------------------------------------
# EXTRAER RESPUESTA DEL ESTUDIANTE
# ---------------------------------------------------

def extraer_respuesta_estudiante(html):

    soup = BeautifulSoup(html, "html.parser")
    texto = soup.get_text(" ", strip=True)

    respuesta = ""

    match = re.search(r"Guardada:\s*(.+?)\s*Respuesta", texto)

    if match:
        respuesta = match.group(1).strip()

    elif "Guardada:" in texto:
        respuesta = texto.split("Guardada:")[-1].strip()

    # limpiar textos basura de moodle
    basura = [
        "Respuesta guardada",
        "Intento finalizado",
        "Finalizado"
    ]

    for b in basura:
        if b in respuesta:
            respuesta = respuesta.split(b)[0].strip()

    return respuesta


    
# ---------------------------------------------------
# RUTA PRINCIPAL
# ---------------------------------------------------
@app.route("/feedback/")
def feedback_loader():

    return render_template("loader.html")

#@app.route("/feedback/")
#def feedback_view():
@app.route("/procesar_feedback")
def feedback_view():
    id_user_moodle = request.args.get("id_user")
    quizid = request.args.get("feedbackid")
    nombre_usuario = request.args.get("nombre_usuario")
    caso = request.args.get("caso")

    curid = request.args.get("curid")
    user_id = request.args.get("user_id")
    documento_identidad = request.args.get("documento_identidad")

    userid = id_user_moodle

    # --------------------------------------------
    # Obtener intentos
    # --------------------------------------------

    data_attempts = get_attempts(quizid, userid)

    attempts = data_attempts.get("attempts", [])

    results = []
    respuestas_por_pregunta = {}
    brechas_por_pregunta = {}

    # --------------------------------------------
    # RECORRER INTENTOS
    # --------------------------------------------

    for attempt in attempts:

        attempt_id = attempt["id"]
        intento_num = attempt["attempt"]

        ts = attempt.get("timemodified", 0)

        fecha = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))

        review = get_attempt_review(attempt_id)

        questions = review.get("questions", [])

        for q in questions:

            pregunta_id = str(q.get("slot"))
            numero = q.get("number")

            html = q.get("html", "")

            soup = BeautifulSoup(html, "html.parser")

            # --------------------------------------------
            # EXTRAER PREGUNTA
            # --------------------------------------------

            enunciado_div = soup.find("div", class_="qtext")

            if enunciado_div:
                pregunta = limpiar_html(str(enunciado_div))
            else:
                pregunta = limpiar_html(html)

            # --------------------------------------------
            # EXTRAER RESPUESTA
            # --------------------------------------------

            respuesta = extraer_respuesta_estudiante(html)
            
            if respuesta_invalida(respuesta):

                print("Respuesta inválida detectada")

                feedback_texto = feedback_reconduccion(nombre_usuario)

                results.append({
                    "intento": intento_num,
                    "pregunta": pregunta,
                    "respuesta": respuesta,
                    "feedback": feedback_texto
                })

                continue  # 🔥 IMPORTANTE: salta todo lo demás

            print("----------- RESPUESTA MOODLE -----------")
            print("Pregunta:", numero)
            print("Respuesta:", respuesta)
            print("Longitud:", len(respuesta))
            print("----------------------------------------")

            # --------------------------------------------
            # EVALUAR RESPUESTA
            # --------------------------------------------

            # --------------------------------------------
            # VERIFICAR SI YA EXISTE RETRO
            # --------------------------------------------

            feedback_guardado = obtener_evaluacion_existente(
                curid,
                quizid,
                user_id,
                intento_num,
                pregunta_id
            )

            if feedback_guardado:

                print("Retro ya existe en BD, no se genera nueva")

                feedback_texto = feedback_guardado

            else:

                # --------------------------------------------
                # EVALUAR RESPUESTA
                # --------------------------------------------

                eval_result = evaluar_respuesta(
                    pregunta,
                    respuesta,
                    pregunta_id,
                    intento_num,
                    quizid
                )

                # --------------------------------------------
                # GENERAR RETRO
                # --------------------------------------------

                if intento_num == 1:

                    feedback_texto = generar_feedback(
                        pregunta,
                        respuesta,
                        eval_result.get("brechas", ""),
                        intento_num,
                        nombre_usuario
                    )

                    respuestas_por_pregunta[pregunta_id] = respuesta
                    brechas_por_pregunta[pregunta_id] = eval_result.get("brechas", "")

                else:

                    respuesta_anterior = respuestas_por_pregunta.get(pregunta_id, "")
                    brechas_anteriores = brechas_por_pregunta.get(pregunta_id, "")

                    feedback_texto = generar_feedback_segundo_intento(
                        pregunta,
                        respuesta_anterior,
                        respuesta,
                        brechas_anteriores,
                        nombre_usuario
                    )

                # --------------------------------------------
                # GUARDAR EN BD
                # --------------------------------------------

                guardar_evaluacion(
                    curid,
                    quizid,
                    id_user_moodle,
                    user_id,
                    documento_identidad,
                    intento_num,
                    pregunta_id,
                    pregunta,
                    respuesta,
                    eval_result.get("similarity_score"),
                    eval_result.get("nivel_estimado"),
                    feedback_texto,
                    fecha
                )

                                               
            results.append({
                "intento": intento_num,
                "pregunta": pregunta,
                "respuesta": respuesta,
                "feedback": feedback_texto
            })

    # --------------------------------------------
    # RENDER HTML
    # --------------------------------------------

    resultados_por_intento = defaultdict(list)

    for r in results:
        resultados_por_intento[r["intento"]].append(r)


    mapa_casos = {
                    "1": {
                        "izq": "https://campusvirtual-sifods.minedu.gob.pe/mod/quiz/view.php?id=197300",
                        "der": "https://campusvirtual-sifods.minedu.gob.pe/mod/quiz/view.php?id=197301"
                    },
                    "2": {
                        "izq": "https://campusvirtual-sifods.minedu.gob.pe/mod/quiz/view.php?id=197301",
                        "der": "https://campusvirtual-sifods.minedu.gob.pe/mod/quiz/view.php?id=197302"
                    },
                    "3": {
                        "izq": "https://campusvirtual-sifods.minedu.gob.pe/mod/quiz/view.php?id=197302",
                        "der": "https://campusvirtual-sifods.minedu.gob.pe/mod/quiz/view.php?id=197021"
                    },
                    "4": {
                        "izq": "https://campusvirtual-sifods.minedu.gob.pe/mod/quiz/view.php?id=197021",
                        "der": "https://campusvirtual-sifods.minedu.gob.pe/mod/quiz/view.php?id=195317"
                    }
                }

    links = mapa_casos.get(caso, {"izq": "#", "der": "#"})
        
    return render_template(
        "feedback.html",
        usuario=nombre_usuario,
        resultados=resultados_por_intento,
        link_izq=links["izq"],
        link_der=links["der"]
    )


# ---------------------------------------------------
# RUN
# ---------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3002)