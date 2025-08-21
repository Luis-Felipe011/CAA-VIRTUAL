from flask import Blueprint, request, jsonify
from repositories.usuarios import inserir_candidato
from services.get_token import get_uid_from_token
from services.database import get_connection

documento_bp = Blueprint("documento", __name__)

@documento_bp.route("/documento/status", methods=["GET"])
def listar_status_documentos():
    candidato_id = request.args.get("candidato_id")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT file_path, status FROM document_status WHERE candidato_id = %s
    """, (candidato_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    # Retorna { file_path: status }
    return jsonify({row[0]: row[1] for row in rows})

@documento_bp.route("/documento/status", methods=["PATCH", "OPTIONS"])
def atualizar_status_documento():
    if request.method == "OPTIONS":
        from flask import make_response
        response = make_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "PATCH,OPTIONS"
        return response, 200

    data = request.get_json()
    candidato_id = data.get("candidato_id")
    file_path = data.get("file_path")
    status = data.get("status")
    justificativa = data.get("justificativa", "")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO document_status (candidato_id, file_path, status, justificativa, atualizado_em)
        VALUES (%s, %s, %s, %s, now())
        RETURNING id
    """, (candidato_id, file_path, status, justificativa))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"success": True})
def listar_status_documentos():
    candidato_id = request.args.get("candidato_id")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT file_path, status, justificativa FROM document_status WHERE candidato_id = %s
    """, (candidato_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    # Retorna { file_path: { status: ..., justificativa: ... } }
    return jsonify({row[0]: {"status": row[1], "justificativa": row[2]} for row in rows})