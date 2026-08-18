def name_length(text: str) -> int:
    return len([ch for ch in text if ch.isalpha()])

def digit_sum(text: str) -> int:
    return sum(int(ch) for ch in text if ch.isdigit())

def first_letter_index(text: str) -> int:
    for ch in text.lower():
        if 'a' <= ch <= 'z':
            return ord(ch) - 97
    return 0

def primary_cell(L: int, S: int, c: int) -> dict:
    row = ((L + S - 1) % 64) + 1
    col = c % 26
    return {"col": col, "row": row}

def user_placement(name: str, phone: str) -> dict:
    L = name_length(name)
    S = digit_sum(phone)
    c = first_letter_index(name)
    return primary_cell(L, S, c)

def object_placement(object_name: str) -> dict:
    UNIVERSAL_UID = "550198550199"
    L = name_length(object_name)
    S = digit_sum(UNIVERSAL_UID)  # 57
    c = first_letter_index(object_name)
    return primary_cell(L, S, c)