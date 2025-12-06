import logging

class Wallet:
    """Manages an agent's token balance."""
    def __init__(self, initial_balance: int):
        self.balance = initial_balance
        logging.info(f"Wallet initialized with {self.balance} tokens.")

    def spend(self, amount: int) -> bool:
        """Deducts tokens. Returns False if funds are insufficient."""
        if self.balance >= amount:
            self.balance -= amount
            return True
        return False

    def earn(self, amount: int):
        """Adds tokens to the balance."""
        self.balance += amount

class Ledger:
    """Records all transactions for auditing."""
    def __init__(self):
        self.transactions = []

    def record(self, description: str, cost: int, balance: int):
        transaction = f"'{description}' | Cost: {cost} | Balance: {balance}"
        self.transactions.append(transaction)
        logging.info(f"Ledger: {transaction}")

# --- The Official MISO Cost Model ---
COST_MODEL = {
    "strategist_planning": 50, # High cost for high-level strategy
    "tactician_step": 10,      # Cost per tactical action
    "read_file": 1,
    "write_file": 5,
    "patch_code": 10,
    "run_tests": 3,
    "finish_milestone": 0
}

# The final prize for successfully completing the entire mission.
SUCCESS_REWARD = 1000
