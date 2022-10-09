import _pickle as pk

with open('keyword.txt', 'r') as f:
    lines = f.readlines()
keyword = []
for line in lines[1:]:
    if line != '\n' and line != '\u200b\n':
        for keys in line.split('.')[1].split(', '):
            keyword.append(keys.split(',')[0].strip())

with open('keyword.pkl', 'wb') as f:
    pk.dump(keyword, f)