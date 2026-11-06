"""Codificador QR mínimo (versión 2, corrección H, modo alfanumérico, máscara 0) para dibujar un QR REAL que sí se
lee con la cámara. Basado en el algoritmo público de Project Nayuki (QR Code generator, licencia MIT).
  matriz('MENTE EN ORBITA') -> lista de 25 listas de 0/1 (1 = oscuro); funcion -> mapa de módulos fijos."""
ALNUM = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:'


def _mul(x, y):
    z = 0
    for i in range(7, -1, -1):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z


def _divisor(degree):
    r = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for j in range(len(r)):
            r[j] = _mul(r[j], root)
            if j + 1 < len(r):
                r[j] ^= r[j + 1]
        root = _mul(root, 0x02)
    return r


def _resto(data, div):
    r = [0] * len(div)
    for b in data:
        f = b ^ r.pop(0)
        r.append(0)
        for i, c in enumerate(div):
            r[i] ^= _mul(c, f)
    return r


def matriz(texto='MENTE EN ORBITA', mascara=0):
    V, N = 2, 25
    DATA_CW, EC_CW = 16, 28                      # versión 2-H: un bloque de 16 + 28
    texto = texto.upper()
    bits = [0, 0, 1, 0]                          # modo alfanumérico
    bits += [(len(texto) >> i) & 1 for i in range(8, -1, -1)]
    for i in range(0, len(texto) - 1, 2):
        v = ALNUM.index(texto[i]) * 45 + ALNUM.index(texto[i + 1])
        bits += [(v >> k) & 1 for k in range(10, -1, -1)]
    if len(texto) % 2:
        v = ALNUM.index(texto[-1])
        bits += [(v >> k) & 1 for k in range(5, -1, -1)]
    cap = DATA_CW * 8
    assert len(bits) <= cap, 'texto muy largo'
    bits += [0] * min(4, cap - len(bits))
    bits += [0] * ((8 - len(bits) % 8) % 8)
    cw = [int(''.join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    pad = 0xEC
    while len(cw) < DATA_CW:
        cw.append(pad)
        pad ^= 0xEC ^ 0x11
    cw = cw + _resto(cw, _divisor(EC_CW))
    M = [[0] * N for _ in range(N)]
    F = [[False] * N for _ in range(N)]

    def fset(x, y, d):
        M[y][x] = 1 if d else 0
        F[y][x] = True
    for i in range(N):                           # temporización
        fset(6, i, i % 2 == 0)
        fset(i, 6, i % 2 == 0)
    for cx, cy in ((3, 3), (N - 4, 3), (3, N - 4)):   # buscadores + separadores
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                x, y = cx + dx, cy + dy
                if 0 <= x < N and 0 <= y < N:
                    fset(x, y, max(abs(dx), abs(dy)) not in (2, 4))
    for dy in range(-2, 3):                      # alineación (18, 18)
        for dx in range(-2, 3):
            fset(18 + dx, 18 + dy, max(abs(dx), abs(dy)) != 1)
    data = (2 << 3) | mascara                    # nivel H = 2
    rem = data
    for _ in range(10):
        rem = (rem << 1) ^ ((rem >> 9) * 0x537)
    fb = ((data << 10) | rem) ^ 0x5412
    gb = lambda i: (fb >> i) & 1
    for i in range(6):
        fset(8, i, gb(i))
    fset(8, 7, gb(6)); fset(8, 8, gb(7)); fset(7, 8, gb(8))
    for i in range(9, 15):
        fset(14 - i, 8, gb(i))
    for i in range(8):
        fset(N - 1 - i, 8, gb(i))
    for i in range(8, 15):
        fset(8, N - 15 + i, gb(i))
    fset(8, N - 8, True)
    i = 0
    right = N - 1
    while right >= 1:
        if right == 6:
            right = 5
        for vert in range(N):
            for j in range(2):
                x = right - j
                up = ((right + 1) & 2) == 0
                y = N - 1 - vert if up else vert
                if not F[y][x] and i < len(cw) * 8:
                    M[y][x] = (cw[i >> 3] >> (7 - (i & 7))) & 1
                    i += 1
        right -= 2
    masks = [lambda x, y: (x + y) % 2 == 0, lambda x, y: y % 2 == 0, lambda x, y: x % 3 == 0,
             lambda x, y: (x + y) % 3 == 0]
    for y in range(N):
        for x in range(N):
            if not F[y][x] and masks[mascara](x, y):
                M[y][x] ^= 1
    return M, F


def buscadores(N=25):
    """Cajas (x0, y0, x1, y1) en módulos de los 3 cuadros de las esquinas (7x7)."""
    return [(0, 0, 7, 7), (N - 7, 0, N, 7), (0, N - 7, 7, N)]


if __name__ == '__main__':
    import numpy as np
    from PIL import Image
    M, F = matriz()
    a = np.array(M, np.uint8)
    img = np.pad(1 - a, 4, constant_values=1) * 255
    im = Image.fromarray(img.astype(np.uint8)).resize((33 * 12, 33 * 12), Image.NEAREST)
    im.save('/home/claude/qr_prueba.png')
    import cv2
    d = cv2.QRCodeDetector()
    print('lee:', repr(d.detectAndDecode(np.asarray(im.convert('RGB')))[0]))
