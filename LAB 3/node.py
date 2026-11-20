from argparse import ArgumentParser
from uuid import uuid4
from flask import Flask, jsonify, request
from blockchain import Blockchain

import math

app = Flask(__name__)
node_identifier = str(uuid4()).replace("-", "")
blockchain = Blockchain()


@app.get("/chain")
def full_chain():
    return jsonify({
        "chain": blockchain.chain,
        "length": len(blockchain.chain),
    }), 200


MAX_AMOUNT = 1_000_000

@app.post("/transactions/new")
def new_transaction():
    values = request.get_json(silent=True)

    # 1. Sprawdzenie poprawności JSON-a i czy jest obiektem (słownikiem)
    if not isinstance(values, dict):
        return jsonify({"error": "Niepoprawny format danych: wymagany poprawny obiekt JSON"}), 400

    required = {"sender", "recipient", "amount"}
    provided = set(values.keys())

    # 2. Brakujące pola
    missing = required - provided
    if missing:
        return jsonify({"error": f"Brak wymaganych pól: {', '.join(sorted(missing))}"}), 400

    # 3. Nadmiarowe, nieoczekiwane pola
    extra = provided - required
    if extra:
        return jsonify({"error": f"Nieoczekiwane pola: {', '.join(sorted(extra))}"}), 400

    sender = values["sender"]
    recipient = values["recipient"]
    amount = values["amount"]

    # 4. Walidacja typów i limitów (w Pythonie bool dziedziczy po int!)
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        return jsonify({"error": "Kwota musi być liczbą"}), 400
    if not math.isfinite(amount) or amount <= 0:
        return jsonify({"error": "Kwota musi być skończoną liczbą dodatnią"}), 400
    if amount > MAX_AMOUNT:
        return jsonify({"error": f"Kwota przekracza dozwolony limit ({MAX_AMOUNT})"}), 400
    if sender == "0":
        return jsonify({"error": "Nie można utworzyć transakcji z adresu systemowego '0'"}), 400

    # 5. Walidacja biznesowa z blockchain.py (saldo, sender == recipient, puste stringi)
    try:
        index = blockchain.new_transaction(sender, recipient, amount)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"message": f"Transakcja zostanie dodana do bloku {index}"}), 201


@app.post("/mine")
def mine():
    block = blockchain.mine(node_identifier)
    return jsonify({
        "message": "Wydobyto nowy blok",
        "block": block,
        "hash": blockchain.hash(block),
    }), 200

@app.get("/transactions/pending")
def pending_transactions():
    return jsonify({
        "pending_transactions": blockchain.current_transactions,
        "count": len(blockchain.current_transactions),
    }), 200


@app.get("/block/<int:index>")
def get_block(index):
    if index < 1 or index > len(blockchain.chain):
        return jsonify({"error": f"Blok o indeksie {index} nie istnieje"}), 404

    block = blockchain.chain[index - 1]
    return jsonify({
        "block": block,
        "hash": blockchain.hash(block),
    }), 200

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", default=5000, type=int)
    args = parser.parse_args()
    app.run(host="127.0.0.1", port=args.port)