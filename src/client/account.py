class Account:
    def __init__(self, account_id, balance):
        self.account_id = account_id
        self.balance = balance


class Bank:
    def __init__(self) -> None:
        self.accounts = {}

    def create_account(self, account_id, initial_balance):
        if account_id not in self.accounts:
            account = Account(account_id, initial_balance)
            self.accounts[account_id] = account

    def get_account_balance(self, account_id):
        if account_id in self.accounts:
            return self.accounts[account_id].balance
        return 0.0
