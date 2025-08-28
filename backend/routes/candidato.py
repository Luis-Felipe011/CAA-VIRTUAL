from flask import Blueprint, request, jsonify
from repositories.usuarios import inserir_candidato
from services.get_token import get_uid_from_token
from services.database import get_connection

candidato_bp = Blueprint("candidato", __name__)

@candidato_bp.route("/candidato", methods=["POST", "OPTIONS"])
def criar_candidato():
    if request.method == "OPTIONS":
        return '', 200

    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    usuario_id = get_uid_from_token(token)
    if not usuario_id:
        return jsonify({"success": False, "error": "Usuário não autenticado"}), 401

    data = request.get_json()
    nome = data.get("nome")
    cpf = data.get("cpf")
    step = data.get("step")
    if not nome or not cpf:
        return jsonify({"success": False, "error": "Campos obrigatórios faltando"}), 400

    candidato_id = inserir_candidato(usuario_id, nome, cpf, step)
    if candidato_id:
        return jsonify({"success": True, "id": candidato_id})
    else:
        return jsonify({"success": False, "error": "Erro ao salvar candidato"}), 500
    
@candidato_bp.route("/familiar", methods=["POST"])
def criar_familiar():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    usuario_id = get_uid_from_token(token)
    if not usuario_id:
        return jsonify({"success": False, "error": "Usuário não autenticado"}), 401

    data = request.get_json()
    nome = data.get("nome")
    cpf = data.get("cpf")
    candidato_id = data.get("candidato_id")

    if not nome or not cpf or not candidato_id:
        return jsonify({"success": False, "error": "Campos obrigatórios faltando"}), 400

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO family (name, cpf, candidato_id) VALUES (%s, %s, %s) RETURNING id",
            (nome, cpf, candidato_id)
        )
        familiar_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "id": familiar_id})
    except Exception as e:
        print(f"Erro ao salvar familiar: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@candidato_bp.route("/checklist", methods=["GET"])
def get_checklist():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    usuario_id = get_uid_from_token(token)
    if not usuario_id:
        return jsonify({"success": False, "error": "Usuário não autenticado"}), 401

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM documentos")
        checklist = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"success": True, "checklist": checklist})
    except Exception as e:
        print(f"Erro ao obter checklist: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@candidato_bp.route("/candidato/step", methods=["PATCH", "OPTIONS"])
def atualizar_step():
    if request.method == "OPTIONS":
        from flask import make_response
        response = make_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "PATCH,OPTIONS"
        return response, 200
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    usuario_id = get_uid_from_token(token)
    if not usuario_id:
        return jsonify({"success": False, "error": "Usuário não autenticado"}), 401

    data = request.get_json()
    novo_step = data.get("step")
    candidato_id = data.get("candidato_id")  # pode ser None

    if not novo_step:
        return jsonify({"success": False, "error": "Campo 'step' obrigatório"}), 400

    try:
        conn = get_connection() 
        cur = conn.cursor()
        if candidato_id:
            cur.execute(
                "UPDATE candidate SET step = %s WHERE id = %s RETURNING id",
                (novo_step, candidato_id)
            )
        else:
            cur.execute(
                "UPDATE candidate SET step = %s WHERE id = %s RETURNING id",
                (novo_step, usuario_id)
            )
        candidato_id_returned = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "id": candidato_id_returned})
    except Exception as e:
        print(f"Erro ao atualizar step: {e}")
        return jsonify({"success": False, "error": str(e)}), 500