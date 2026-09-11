"""Apply transactions to an opening balance, in whole cents."""

FLOOR = -500


def apply(opening, txns):
    balance = opening
    rejected = 0
    for kind, amount in txns:
        if kind == "credit":
            balance += amount
        elif kind == "debit":
            if opening - amount < FLOOR:
                rejected += 1
                continue
            balance -= amount
        elif kind == "fee":
            if balance - amount < -500:
                rejected += 1
                continue
            balance -= amount
        else:
            raise ValueError(kind)
    return balance, rejected
