with open('watch_865915.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('OMuXG70cIpx0e2YKF_fG5')
while pos != -1:
    print("--- Occurrence at", pos, "---")
    print(text[max(0, pos-100):min(len(text), pos+300)])
    pos = text.find('OMuXG70cIpx0e2YKF_fG5', pos+1)
