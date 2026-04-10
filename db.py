import psycopg2
import os


def get_conn():

    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )


def guardar_evaluacion(
    curid,
    feedback_id,
    id_user_moodle,
    user_id,
    documento_identidad,
    intento,
    pregunta_id,
    pregunta,
    respuesta,
    similarity_score,
    nivel_estimado,
    gpt_evaluacion,
    fecha_respuesta
):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO evaluaciones_feedback
        (curid, feedback_id, id_user_moodle, user_id, documento_identidad,
         intento, pregunta_id, pregunta, respuesta,
         similarity_score, nivel_estimado, gpt_evaluacion,
         fecha_respuesta)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        curid,
        feedback_id,
        id_user_moodle,
        user_id,
        documento_identidad,
        intento,
        pregunta_id,
        pregunta,
        respuesta,
        similarity_score,
        nivel_estimado,
        gpt_evaluacion,
        fecha_respuesta
    ))

    conn.commit()
    cur.close()
    conn.close()

def obtener_evaluacion_existente(curid, quizid, user_id, intento, pregunta_id):

    conn = get_conn()
    cursor = conn.cursor()

    query = """
    SELECT respuesta
    FROM evaluaciones_feedback
    WHERE curid = %s
    AND feedback_id = %s
    AND user_id = %s
    AND intento = %s
    AND pregunta_id = %s
    """

    cursor.execute(query, (curid, quizid, user_id, intento, pregunta_id))

    row = cursor.fetchone()

    conn.close()

    if row:
        return row[0]

    return None