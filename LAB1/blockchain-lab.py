import hashlib
import json
from time import time

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = {
            "index": 1,
            "timestamp": 0,
            "transactions": [],
            "nonce": 0,
            "previous_hash": "0" * 64,
        }
        self.chain.append(genesis)

    @staticmethod
    def hash(block):
        # sort_keys=True gwarantuje deterministyczną kolejność pól
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, transactions):
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time(),
            "transactions": transactions,
            "nonce": 0,
            "previous_hash": self.hash(self.last_block),
        }
        self.chain.append(block)
        return block
    def is_chain_valid(self):
        # Pomijamy blok genezy (indeks 0), zaczynamy od bloku nr 2 (indeks 1)
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Sprawdzamy, czy zapisany previous_hash zgadza się z faktycznym skrótem poprzedniego bloku
            if current_block["previous_hash"] != self.hash(previous_block):
                return False, current_block["index"]
                
        return True, None

if __name__ == "__main__":
    bc = Blockchain()
    bc.add_block(["Alice -> Bob: 5"])
    bc.add_block(["Bob -> Carol: 2"])
    bc.add_block(["Carol -> Anna: 2"])
    
    for block in bc.chain:
        print(json.dumps(block, indent=2, ensure_ascii=False))
        print("hash:", Blockchain.hash(block))
        print("-" * 70)

        # test integralnosci i modyfikacja bloku 2
    print("\n--- TEST INTEGRALNOŚCI ---")
    is_valid, bad_block_index = bc.is_chain_valid()
    print(f"Czy łańcuch jest poprawny przed atakiem? {is_valid}")

    print("\nDokonujemy manipulacji w bloku nr 2")
    bc.chain[1]["transactions"][0] = "Alice -> Bob: 500"
    
    is_valid, bad_block_index = bc.is_chain_valid()
    print(f"Czy łańcuch jest poprawny po ataku? {is_valid}")
    if not is_valid:
        print(f"Wykryto manipulację! Pierwszy niepoprawny blok to nr: {bad_block_index}")

    # naprawa łańcucha
    print("\n--- ATAKUJĄCY NAPRAWIA ŁAŃCUCH ---")
    # Atakujący przelicza skróty dla wszystkich bloków następujących po zmodyfikowanym (od indeksu 2)
    for i in range(2, len(bc.chain)):
        bc.chain[i]["previous_hash"] = bc.hash(bc.chain[i-1])

    is_valid, bad_block_index = bc.is_chain_valid()
    print(f"Czy łańcuch jest poprawny po 'naprawie' przez atakującego? {is_valid}")

    # modyfikacja ostatniego bloku
    print("\n--- ATAK NA OSTATNI BLOK ---")
    bc.chain[-1]["transactions"] = ["Złodziej -> Złodziej: 1000"]
    is_valid, bad_block_index = bc.is_chain_valid()
    print(f"Czy metoda wykryła zmianę w ostatnim bloku? {not is_valid}")

        