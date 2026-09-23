with open('movie_865915.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('2d:')
if pos != -1:
    print(text[pos:pos+500])
else:
    print("2d: not found")
