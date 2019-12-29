def word2chars(word):
    text = ""
    is_start = True
    for c in word:
        if c == " ":
            is_start = True
            text = text[:-2] + " "
        else:
            if not is_start:
                text += "#"
            text += c + "# "
            is_start = False

    return text[:-2]