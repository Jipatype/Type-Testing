import os
from flask import Flask, request, Response, render_template
from PIL import Image, ImageDraw, ImageFont, ImageColor
from io import BytesIO
import re
import waitress
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
isDevelopment = False
host = "127.0.0.1"
port = 5555
cwd = os.path.dirname(os.path.realpath(__file__))

def convertToHumanName(fileName):
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', fileName)
    name = name.replace(".otf", "") \
        .replace(".ttf", "") \
        .replace("-", " ") \
        .replace("_", " ") \
        .replace("Extra ", "Extra") \
        .replace("Semi ", "Semi") \
        .replace("Ultra ", "Ultra")
    return name

def getWeigthClass(fileName: str):
    if "Black" in fileName:
        return 900
    if "ExtraBold" in fileName:
        return 800
    if "SemiBold" in fileName:
        return 600
    if "Bold" in fileName:
        return 700
    if "Medium" in fileName:
        return 500
    if "ExtraLight" in fileName:
        return 200
    if "Light" in fileName:
        return 300
    if "Thin" in fileName:
        return 100
    return 400

def isItalic(fileName):
    if "Italic" in fileName:
        return True
    return False

def getWidthClass(fileName):
    if "UltraCondensed" in fileName:
        return 1
    if "ExtraCondensed" in fileName:
        return 2
    if "SemiCondensed" in fileName:
        return 4
    if "Condensed" in fileName:
        return 3
    if "UltraExpanded" in fileName:
        return 9
    if "ExtraExpanded" in fileName:
        return 8
    if "SemiExpanded" in fileName:
        return 6
    if "Expanded" in fileName:
        return 7
    return 5

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/type/<familyName>/<fileName>')
def type(familyName, fileName):
    fontPath = os.path.join(cwd, "preview", familyName, fileName)
    width = int(request.args.get('width')) if "width" in request.args else 1000
    text = request.args.get("text") if "text" in request.args else ""
    text = "The quick brown fox jumps over the lazy dog" if text == "" else text
    color = ImageColor.getrgb("#" + request.args.get("color")) if "color" in request.args else "black"
    bgColor = ImageColor.getrgb("#" + request.args.get("bgColor")) if "bgColor" in request.args else "white"
    size = int(request.args.get('size')) if "size" in request.args else 48
    height = round(size * 120 / 100 + size)
    image = Image.new('RGB', (width, height), bgColor)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(fontPath, size, layout_engine=ImageFont.Layout.RAQM)
    _, _, textWidth, textHeight = draw.textbbox(xy=(0, 0), text=text, font=font)
    position = (0, (height - textHeight) // 2)
    draw.text(position, text, fill=color, font=font)
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    imageBytes = buffered.getvalue()
    return Response(imageBytes, mimetype='image/png'), 200

@app.route('/getFontLists')
def getFontLists():
    directory = os.path.join(cwd, "preview")
    families = dict()
    try:
        with os.scandir(directory) as dirs:
            for dir in dirs:
                if dir.is_dir():
                    dirPath = os.path.join(directory, dir.name)
                    if dir.name not in families:
                        families[dir.name] = list()
                    with os.scandir(dirPath) as files:
                        for file in files:
                            if file.is_file() and (file.name.endswith(".otf") or file.name.endswith(".ttf")):
                                families[dir.name].append({
                                    "fileName": file.name,
                                    "name": convertToHumanName(file.name),
                                    "weight": getWeigthClass(file.name),
                                    "width": getWidthClass(file.name),
                                    "italic": isItalic(file.name)})
                        families[dir.name] = sorted(families[dir.name], key=lambda x: (x['weight'], x['width'], x['italic']))
                        if len(families[dir.name]) == 0:
                            del families[dir.name]
    except FileNotFoundError as e:
        print(f"Error: {e}")
    return families, 200
    

if __name__ == '__main__':
    if isDevelopment:
        print(f"Development server is runing on http://{host}:{port}")
        app.run(host=host, port=port, debug=True)
    else:
        print(f"Server is runing on http://{host}:{port}")
        waitress.serve(app=app, host=host, port=port, threads=100, connection_limit=1000)
    