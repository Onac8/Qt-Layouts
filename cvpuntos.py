#!/usr/bin/python3
import cv2
import argparse, textwrap

parser = argparse.ArgumentParser(description='Selección de puntos a con imagen o vídeo.',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=textwrap.dedent('''\
Teclas interactivas
--------------------------------
m       Mostrar puntos
r       Resetear puntos
d       Deshacer el último punto
q       Mostrar puntos y salir
'''))
parser.add_argument('input', type=str, nargs=1, help='imagen o video')
args = parser.parse_args()

print(parser.epilog)

puntos = []

img_original = cv2.imread(args.input[0])
if img_original is None:
    cap = cv2.VideoCapture(args.input[0])
    ret, img_original = cap.read()
if img_original is None:
    print('No se ha podido leer la entrada')
    exit(-1)

def DibujarPuntos():
    L = len(puntos)
    img = img_original.copy()
    if L > 0:
        for i in range(0, L+2, 2):
            cv2.line(img, (puntos[i%L], puntos[(i+1)%L]), (puntos[(i+2)%L], puntos[(i+3)%L]), (0, 255, 0))
    cv2.imshow('puntos', img)

def Callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        puntos.append(x)
        puntos.append(y)
        DibujarPuntos()
        print(f'({x}, {y})')

def MostrarPuntos():
    print(puntos)

cv2.namedWindow('puntos')
cv2.setMouseCallback('puntos', Callback)
cv2.imshow('puntos', img_original)

key = chr(cv2.waitKey(0))
while key != 'q':
    if key == 'm':
        MostrarPuntos()
    elif key == 'r':
        puntos = []
        cv2.imshow('puntos', img_original)
    elif key == 'd':
        if len(puntos) > 0:
            puntos = puntos[:-2]
            DibujarPuntos()

    key = chr(cv2.waitKey(0))

MostrarPuntos()
