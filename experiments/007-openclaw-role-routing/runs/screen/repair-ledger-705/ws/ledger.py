"""Apply transactions to an opening balance, in whole cents."""


def apply(opening, txns):
    balance = opening
    rejected = 0
    for kind, amount in txns:
        if kind == "credit":
            balance += amount
        elif kind == "debit":
            if balance - amount < 0:
                rejected += 1
                continue
            balance -= amount
        elif kind == "fee":
            balance -= amount
        else:
            raise ValueError(kind)
    return balance, rejected
