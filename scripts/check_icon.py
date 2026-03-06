from PIL import Image

img = Image.open(r'd:\kingshortid\mobile\assets\logo-kingshortfix.png').convert('RGB')
w, h = img.size
print(f'Image size: {w}x{h}')

# Scan from top
top_pad = 0
for y in range(h):
    row_white = True
    for x in range(0, w, 4):
        r, g, b = img.getpixel((x, y))
        if r < 240 or g < 240 or b < 240:
            row_white = False
            break
    if not row_white:
        top_pad = y
        break

# Scan from bottom
bottom_pad = 0
for y in range(h-1, 0, -1):
    row_white = True
    for x in range(0, w, 4):
        r, g, b = img.getpixel((x, y))
        if r < 240 or g < 240 or b < 240:
            row_white = False
            break
    if not row_white:
        bottom_pad = h - y - 1
        break

# Scan from left
left_pad = 0
for x in range(w):
    col_white = True
    for y in range(0, h, 4):
        r, g, b = img.getpixel((x, y))
        if r < 240 or g < 240 or b < 240:
            col_white = False
            break
    if not col_white:
        left_pad = x
        break

# Scan from right
right_pad = 0
for x in range(w-1, 0, -1):
    col_white = True
    for y in range(0, h, 4):
        r, g, b = img.getpixel((x, y))
        if r < 240 or g < 240 or b < 240:
            col_white = False
            break
    if not col_white:
        right_pad = w - x - 1
        break

content_w = w - left_pad - right_pad
content_h = h - top_pad - bottom_pad

print(f'\nPadding (white space) around logo content:')
print(f'  Top:    {top_pad}px  ({top_pad/h*100:.1f}%)')
print(f'  Bottom: {bottom_pad}px ({bottom_pad/h*100:.1f}%)')
print(f'  Left:   {left_pad}px  ({left_pad/w*100:.1f}%)')
print(f'  Right:  {right_pad}px ({right_pad/w*100:.1f}%)')
print(f'  Content: {content_w}x{content_h}px ({content_w/w*100:.1f}% x {content_h/h*100:.1f}%)')

crop = int(h * 0.17)
print(f'\nAndroid adaptive icon crops ~{crop}px per side (17%)')
print(f'  Top:    {top_pad}px vs {crop}px needed -> {"SAFE" if top_pad >= crop else f"TERPOTONG {crop-top_pad}px!"}')
print(f'  Bottom: {bottom_pad}px vs {crop}px needed -> {"SAFE" if bottom_pad >= crop else f"TERPOTONG {crop-bottom_pad}px!"}')
print(f'  Left:   {left_pad}px vs {crop}px needed -> {"SAFE" if left_pad >= crop else f"TERPOTONG {crop-left_pad}px!"}')
print(f'  Right:  {right_pad}px vs {crop}px needed -> {"SAFE" if right_pad >= crop else f"TERPOTONG {crop-right_pad}px!"}')
