import hashlib
import json
import copy
from time import time
import matplotlib.pyplot as plt

class Blockchain:
    def __init__(self, difficulty=4):
        self.chain = []
        self.current_transactions = []
        self.difficulty = difficulty
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
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def get_balance(self, address):
        balance = 0
        
        # 1. Sumowanie z zatwierdzonych bloków w łańcuchu
        for block in self.chain:
            for tx in block.get("transactions", []):
                if tx["sender"] == address:
                    balance -= tx["amount"]
                if tx["recipient"] == address:
                    balance += tx["amount"]
                    
        # 2. Sumowanie z puli oczekujących transakcji (mempool)
        for tx in self.current_transactions:
            if tx["sender"] == address:
                balance -= tx["amount"]
            if tx["recipient"] == address:
                balance += tx["amount"]
                
        return balance

    def new_transaction(self, sender, recipient, amount):
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Kwota musi być liczbą dodatnią.")
        if not isinstance(sender, str) or not sender.strip():
            raise ValueError("Nadawca musi być niepustym ciągiem znaków.")
        if not isinstance(recipient, str) or not recipient.strip():
            raise ValueError("Odbiorca musi być niepustym ciągiem znaków.")
        if sender == recipient:
            raise ValueError("Nadawca i odbiorca nie mogą być sobie równi.")

        if sender != "0":
            current_balance = self.get_balance(sender)
            if current_balance < amount:
                raise ValueError(f"Odrzucono: {sender} próbuje wysłać {amount}, ale ma tylko {current_balance} na koncie.")

        self.current_transactions.append({
            "sender": sender,
            "recipient": recipient,
            "amount": amount,
        })
        
        return self.last_block["index"] + 1

    def proof_of_work(self, block):
        block["nonce"] = 0
        computed_hash = self.hash(block)
        while not computed_hash.startswith("0" * self.difficulty):
            block["nonce"] += 1
            computed_hash = self.hash(block)
        return computed_hash

    def mine(self, miner_address):
        reward = {"sender": "0", "recipient": miner_address, "amount": 1}
        
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time(),
            "transactions": [reward] + self.current_transactions,
            "nonce": 0,
            "previous_hash": self.hash(self.last_block),
        }
        
        self.proof_of_work(block)
        self.current_transactions = []
        self.chain.append(block)
        
        return block

    def valid_chain(self, chain):
        if chain[0] != self.chain[0]:
            return False
            
        for i in range(1, len(chain)):
            previous_block = chain[i - 1]
            current_block = chain[i]
            
            if current_block["previous_hash"] != self.hash(previous_block):
                return False
                
            if not self.hash(current_block).startswith("0" * self.difficulty):
                return False
                
        return True


def simulate_attack(bc_class, difficulty, num_blocks=5):
    print(f"\n{'='*50}")
    print(f"SYMULACJA ATAKU DLA TRUDNOŚCI: {difficulty}")
    print(f"{'='*50}")
    
    bc = bc_class(difficulty=difficulty)
    
    bc.mine(miner_address="User0")
    
    for i in range(1, num_blocks):
        bc.new_transaction(f"User{i-1}", f"User{i}", 0.1)
        bc.mine(miner_address=f"User{i}")
        
    print(f"Oryginalny łańcuch poprawny (przed atakiem): {bc.valid_chain(bc.chain)}")
    
    hacked_chain = copy.deepcopy(bc.chain)
    print("Modyfikacja kwoty w bloku nr 3...")
    hacked_chain[2]["transactions"][1]["amount"] = 9999 
    
    print(f"Łańcuch poprawny po modyfikacji (bez przeliczania): {bc.valid_chain(hacked_chain)}")
    print("Atakujący rozpoczyna ponowne wydobywanie zmodyfikowanego bloku i kolejnych...")
    start_time = time()
    
    for i in range(2, len(hacked_chain)):
        hacked_chain[i]["previous_hash"] = bc.hash(hacked_chain[i-1])
        hacked_chain[i]["nonce"] = 0
        computed_hash = bc.hash(hacked_chain[i])
        while not computed_hash.startswith("0" * difficulty):
            hacked_chain[i]["nonce"] += 1
            computed_hash = bc.hash(hacked_chain[i])
            
    attack_time = time() - start_time
    blocks_remined = len(hacked_chain) - 2
    print(f"Czas ataku (przeliczenie {blocks_remined} bloków): {attack_time:.2f} s")
    print(f"Sfałszowany łańcuch poprawny po przeliczeniu: {bc.valid_chain(hacked_chain)}")


if __name__ == "__main__":
    # --- ZADANIE 2.1 & 2.4: WYDOBYWANIE I WALIDACJA ---
    bc = Blockchain(difficulty=4)
    print("--- ZADANIE 2.1 & 2.4: WYDOBYWANIE I WALIDACJA ---")

    start_time = time()
    block_2 = bc.mine(miner_address="Alice")
    print(f"Blok {block_2['index']} wydobyty w {time() - start_time:.2f} s")
    print(f"Saldo Alice po wydobyciu: {bc.get_balance('Alice')}")

    bc.new_transaction("Alice", "Bob", 0.5)
    
    start_time = time()
    block_3 = bc.mine(miner_address="miner-1")
    print(f"Blok {block_3['index']} wydobyty w {time() - start_time:.2f} s")

    print(f"Saldo Alice: {bc.get_balance('Alice')}")
    print(f"Saldo Boba: {bc.get_balance('Bob')}")

    print("\n--- TEST: PRÓBA WYDANIA ŚRODKÓW BEZ POKRYCIA ---")
    try:
        bc.new_transaction("Alice", "Carol", 5)
    except ValueError as e:
        print(f"Zablokowano: {e}")

    # --- ZADANIE 2.2: BADANIE WPŁYWU TRUDNOŚCI ---
    """
    difficulties = []
    theoretical_tries = []
    average_nonces = []
    average_times = []
    total_nonces = 0
    total_time = 0

    print(f"\n{'Trudność d':<12} | {'Teoria 16^d':<12} | {'Śr. nonce':<12} | {'Śr. czas [s]':<12}")
    print("-" * 55)

    for d in range(1, 7):
        bc_test = Blockchain(difficulty=d)
        num_blocks = 2 if d == 6 else 5
        nonces_for_d = []
        times_for_d = []
        for _ in range(num_blocks):
            bc_test.new_transaction("TestSender", "TestRecipient", 1)
            start_t = time()
            mined_block = bc_test.mine(miner_address="miner-1")
            end_t = time()
            time_taken = end_t - start_t
            nonces_for_d.append(mined_block["nonce"])
            times_for_d.append(time_taken)
        avg_nonce = sum(nonces_for_d) / len(nonces_for_d)
        avg_time = sum(times_for_d) / len(times_for_d)
        total_nonces += sum(nonces_for_d)
        total_time += sum(times_for_d)
        theory = 16 ** d
        difficulties.append(d)
        theoretical_tries.append(theory)
        average_nonces.append(avg_nonce)
        average_times.append(avg_time)
        print(f"{d:<12} | {theory:<12} | {avg_nonce:<12.0f} | {avg_time:<12.4f}")

    hashrate = total_nonces / total_time if total_time > 0 else 0
    print(f"\nWydajność komputera wynosi: {hashrate:.2f} H/s")

    plt.figure(figsize=(10, 6))
    plt.plot(difficulties, theoretical_tries, label="Teoretyczna liczba prób (16^d)", marker='o')
    plt.plot(difficulties, average_nonces, label="Średnia wartość nonce", marker='x')
    plt.yscale('log')
    plt.xlabel('Trudność (liczba zer na początku skrótu)')
    plt.ylabel('Liczba prób / wartość nonce')
    plt.title('Porównanie teoretycznej i rzeczywistej liczby prób (PoW)')
    plt.grid(True, which="both", ls="--")
    plt.legend()
    plt.show()
    """

    # --- ZADANIE 2.3: SYMULACJA ATAKU ---
    simulate_attack(Blockchain, difficulty=4)