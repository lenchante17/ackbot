from datetime import date, timedelta
def parse(message):
    """
    Assume word after # is tag
    return list of tag, list of sentence
    """
    items = message.content.split("#")
    splitters = ['.\n', '?\n', '.', '?', '\n']
    tags = []
    series = []
    sentences = []
    for item in items:
        chunks = item.strip().split()
        if len(chunks) == 1:
            tags += chunks
        else:
            sentences = item.strip().split(splitters[0])
            for splitter in splitters[1:]:
                sentences = split_by_splitter(sentences, splitter)

    for tag in tags:
        if len(tag) > 3 and tag[:3] == '시리즈':
            series.append(tag[3:])
    return tags, series, sentences

def split_by_splitter(sentences, splitter):
    result = []
    for sentence in sentences:
        result += sentence.split(splitter)
    return remove_blank(result)

def remove_blank(sentences):
    return [sentence.strip() for sentence in sentences if len(sentence) > 1]

def UTC9(timestamp):
    # if datetime.hour < 15:
    #     return datetime.replace(hour=datetime.hour+9)
    # else:
    #     return datetime.replace(day=datetime.day+1, hour=datetime.hour-15)
    return timestamp + timedelta(hours=9)