import textwrap
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import requests

x_max = 1280
y_max = 640
white = (255, 255, 255, 255)

x_logo = 10
y_logo = 10
x_title = 120
y_title = 45
x_desc = 120
y_desc = 65
x_ann = 120
y_ann = 10
x_foot = (x_max / 2) - (int(len('Earned by mentioning someone 50 times') / 2) * 5.7)
y_foot = 120

# Base empty image
new_im = Image.new('RGBA', (x_max, y_max))
draw = ImageDraw.Draw(new_im, 'RGBA') # RGBA
draw.rectangle((0,0,x_max,y_max), outline=white, fill=white, width = 1) 
bg = Image.open('./logos/bg.png').convert("RGBA")
bg = bg.resize((x_max, y_max))
new_im.paste(bg, (0, 0), bg)
# Inserting achievement logo into empty image


ba = Image.open('./logos/ba.png').convert("RGBA")
ba_ = ba.resize((20, 20))
new_im.paste(ba_, (20, 20), ba_)

# Instancing fonts
title_font = ImageFont.truetype("arial.ttf", 18)
desc_font = ImageFont.truetype("arial.ttf", 14)
foot_font = ImageFont.truetype("arial.ttf", 12)

def write_lines(text, font, img, x, y, color, max_size=40):
    lines = textwrap.wrap(text, width=max_size)
    y_text = 0
    for line in lines:
        # width, height = font.getsize(line)
        img.text((x, y + y_text),line,color,font=font)
        y_text += 15

text_im = ImageDraw.Draw(new_im)
write_lines('Pigeon intern', title_font, text_im, x_title, y_title, (0,0,0))
write_lines('Congratulations! You have unlocked:', desc_font, text_im, x_desc, y_desc, (0,0,0))
new_im.save('aa.png')