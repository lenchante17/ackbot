from datetime import date, timedelta
def parse(message):
    """
    Assume word after # is tag
    return list of tag, list of sentence
    """
    items = message.content.split("#")
    splitters = ['.\n', '.', '\n']
    tags = []
    sentences = []
    for item in items:
        chunks = item.strip().split()
        if len(chunks) == 1:
            tags += chunks
        else:
            temp1 = []
            sentences = []
            temp0 = item.strip().split(splitters[0])
            temp0 = remove_blank(temp0)
            for temp in temp0:
                temp1 += temp.split(splitters[1])
            temp1 = remove_blank(temp1)
            for temp in temp1:
                sentences += temp.split(splitters[2])
            sentences = remove_blank(sentences)
    return tags, sentences

def remove_blank(sentences):
    return [sentence.strip() for sentence in sentences if len(sentence) > 1]

def UTC9(timestamp):
    # if datetime.hour < 15:
    #     return datetime.replace(hour=datetime.hour+9)
    # else:
    #     return datetime.replace(day=datetime.day+1, hour=datetime.hour-15)
    return timestamp + timedelta(hours=9)