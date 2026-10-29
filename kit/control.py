"""Reel diario: Lo que no ves — el control de la tele (29-oct-2026). Tema visual: orbita.
Escenas: control + celular (gancho) · ojo vs cámara · rayos X del control · LED 940 nm · espectro visible ·
sensor del celular · 38 000 parpadeos (2º gancho) · sol y focos vs control · código de pulsos · tele cambia de canal ·
cámara de selfie vs trasera · pilas · cierre Sí/No · loop.
Uso: MOTOR_TEMA=orbita GTA_FMT=v VIDEO_TL=/home/claude/tl_control.json python3 control.py info|preview T out.png|sheet out.jpg t..|chunk A B out.mp4"""
import os
os.environ.setdefault('MOTOR_TEMA', 'orbita')
os.environ.setdefault('GTA_FMT', 'v')
os.environ.setdefault('VIDEO_TL', '/home/claude/tl_control.json')
import math
import numpy as np
import escenas as S
from PIL import ImageDraw
import entornos as EN
from escenas import *  # noqa: F401,F403
from starlink import scan_ring, lab, bigc, cnt, phone_m, CYAN, ICE, LASER, LGREEN, AMBER, PINK, WHITE

BODY = (38, 38, 44)
BODY2 = (58, 58, 66)
BTN = (92, 92, 104)
RED = (210, 40, 46)
IRP = (190, 120, 255)      # cómo pinta la cámara el infrarrojo (morado)
IRW = (240, 230, 255)
LEDC = (60, 40, 50)
PCB = (30, 110, 60)
CHIP = (24, 24, 28)
GOLD = (214, 176, 80)
BAT = (40, 40, 40)
BAT2 = (196, 160, 60)
TVC = (24, 24, 28)
SOFA = (120, 70, 60)
WALL = (230, 220, 200)


def sala(fr):
    EN.env(fr, 'cocina')   # piso de madera de la casa


def remote(x=0.0, y=0.0, z=0.0, ry=0.0, rx=0.0, s=1.0, press=0.0, a=1.0, led=0.0):
    """Control de tele: cuerpo redondeado, teclado de botones, botón rojo y domo del LED al frente (+z)."""
    ms = []
    body = rbox(0.62 * s, 0.16 * s, 2.3 * s, 0.07 * s, BODY, gloss=0.5, shadow=0.35)
    body.alpha = a
    ms.append(body)
    top = rbox(0.54 * s, 0.02 * s, 2.15 * s, 0.05 * s, BODY2, gloss=0.3, shadow=0, base=False).tf(t=(0, 0.16 * s, 0))
    top.alpha = a
    ms.append(top)
    pw = cyl(0.07 * s, 0.03 * s, RED, n=20, shadow=0, gloss=0.6).tf(t=(0.16 * s, 0.17 * s, 0.85 * s))
    ms.append(pw)
    for r in range(5):
        for c in range(3):
            dz = -0.15 * press if (r, c) == (1, 1) else 0
            b = cyl(0.055 * s, 0.03 * s + dz * s * 0.1, BTN, n=16, shadow=0, gloss=0.5).tf(
                t=((c - 1) * 0.16 * s, 0.17 * s, (0.45 - r * 0.22) * s))
            ms.append(b)
    for r in range(3):
        ms.append(rbox(0.36 * s, 0.025 * s, 0.09 * s, 0.03 * s, BTN, gloss=0.4, shadow=0, base=False).tf(
            t=(0, 0.17 * s, (-0.75 - r * 0.18) * s)))
    dome = sphere(0.09 * s, mix(LEDC, IRW, led), nu=24, nv=12, shadow=0, gloss=0.9).tf(s=(1, 0.8, 0.6), t=(0, 0.09 * s, 1.15 * s))
    ms.append(dome)
    return [m.tf(rx=rx, ry=ry, t=(x, y, z)) for m in ms]


def glow(fr, p, r, col, a=1.0, layers=6):
    def f(d, cam, p=p):
        for k in range(layers, 0, -1):
            dot3(d, cam, p, r * k / layers * 1.0, col, a * (0.12 + 0.6 * (1 - k / layers)))
    fr.over.append(f)


def ir_beam(fr, a, b, k, col=IRP, alpha=0.8):
    """Ondas que viajan del LED hacia b (solo para la cámara)."""
    def f(d, cam):
        n = 7
        for i in range(n):
            u = ((k * 1.6 + i / n) % 1.0)
            p = tuple(a[j] + (b[j] - a[j]) * u for j in range(3))
            ring3(d, cam, p, 0.06 + 0.25 * u, col, 2.4, alpha * (1 - u), axis='z')
    fr.over.append(f)


_T = {}


def scr_tex(kind, k=0.0):
    key = (kind, round(k, 2))
    if key in _T:
        return _T[key]

    def f(d, im):
        w, h = im.size
        d.rectangle((0, 0, w, h), fill=(30, 30, 34))
        if kind == 'cam':
            # lo que ve la cámara: el control apuntando, con el destello morado
            d.rectangle((0, 0, w, h), fill=(56, 48, 42))
            d.rounded_rectangle((w * 0.3, h * 0.35, w * 0.7, h * 1.1), 12, fill=(36, 36, 40))
            if k > 0:
                r = w * (0.12 + 0.12 * k)
                for j in range(6, 0, -1):
                    rr = r * j / 6
                    c = mix(IRP, IRW, 1 - j / 6)
                    d.ellipse((w / 2 - rr, h * 0.36 - rr, w / 2 + rr, h * 0.36 + rr), fill=tuple(int(v) for v in c))
            d.rectangle((0, h * 0.92, w, h), fill=(0, 0, 0))
            d.ellipse((w / 2 - 10, h * 0.94, w / 2 + 10, h * 0.94 + 20), outline=(255, 255, 255), width=3)
        elif kind == 'tv':
            ch = int(k)
            cols = [((30, 90, 170), (250, 200, 60)), ((200, 60, 60), (255, 255, 255)), ((40, 140, 80), (250, 240, 200))]
            c1, c2 = cols[ch % 3]
            d.rectangle((0, 0, w, h), fill=c1)
            d.ellipse((w * 0.6, h * 0.15, w * 0.85, h * 0.6), fill=c2)
            d.rectangle((0, h * 0.7, w, h), fill=mix(c1, (0, 0, 0), 0.4))
            d.rectangle((w * 0.04, h * 0.06, w * 0.2, h * 0.2), fill=(0, 0, 0))
            d.text((w * 0.07, h * 0.08), str(ch + 2), fill=(255, 255, 255))
        _T[key] = im
    _T[key] = tex(240 if kind == 'tv' else 160, 135 if kind == 'tv' else 320, (0, 0, 0, 255), f)
    return _T[key]


def tv(x=0.0, z=-2.0, s=1.0, ch=0):
    fr_ = box(3.2 * s, 1.85 * s, 0.12 * s, TVC, shadow=0.3, gloss=0.5, base=False).tf(t=(x, 1.3 * s, z))
    sc = box(3.0 * s, 1.68 * s, 0.01, (10, 10, 12), edge=False, shadow=0, base=False).tf(t=(x, 1.3 * s, z + 0.07 * s))
    decal(sc, sc.FACE['front'] if 'front' in sc.FACE else sc.FACE['top'], scr_tex('tv', ch))
    st = box(0.9 * s, 0.05 * s, 0.4 * s, TVC, shadow=0.3).tf(t=(x, 0.0, z))
    neck = box(0.12 * s, 0.4 * s, 0.08 * s, TVC, shadow=0, base=False).tf(t=(x, 0.05 * s, z))
    rec = sphere(0.035 * s, (120, 20, 20), nu=10, nv=6, shadow=0, gloss=0.9).tf(t=(x + 1.3 * s, 0.42 * s, z + 0.08 * s))
    return [st, neck, fr_, sc, rec]


def hand_press(fr, lt):
    return max(0.0, math.sin(lt * 6)) ** 6


# ================================================================== escenas
def s_hook(fr, t, lt, dur, loop=False):
    """El control apunta al celular; aprietas y en la pantalla del celular aparece el destello morado."""
    t0 = t - lt
    sala(fr)
    fr.cam = Cam(target=(0.15, 0.5, 0.3), dist=vfit(5.0) - lt * 0.15, yaw=-35 + lt * 6, pitch=26)
    pr = hand_press(fr, lt) if lt > 0.3 or loop else 0
    fr.meshes += remote(-0.2, 0.25, -0.6, ry=8, rx=-8, press=pr, led=0.0)
    fr.meshes += phone_m(0.55, 0.85, 1.25, rx=-70, ry=180, s=1.2, scr=scr_tex('cam', pr))
    if pr > 0.05:
        ir_beam(fr, (-0.04, 0.34, 0.55), (0.55, 0.85, 1.15), lt, alpha=0.5 * pr)
    if not loop:
        head(fr, ['Agarra el control', 'de la tele.'], CYAN, t, t0 + 0.05, kicker='Lo que no ves')
    else:
        head(fr, ['Agarra el control', 'de la tele.'], CYAN, t, t0 + 0.05, kicker='Ahora sí…')
    lab(fr, 'Recreación', clamp(lt / 0.4))


def s_eye(fr, t, lt, dur):
    """Pantalla dividida: tu ojo ve el foco apagado; la cámara lo ve encendido."""
    t0 = t - lt
    sala(fr)
    fr.cam = Cam(target=(0, 0.3, 0.6), dist=vfit(2.6), yaw=-10 + lt * 8, pitch=18)
    pr = hand_press(fr, lt)
    fr.meshes += remote(0, 0, 0, led=0.0, press=pr)
    on = pr > 0.2

    def f(img, d, lt=lt, on=on):
        a = ease(clamp(lt / 0.4))
        pill(img, d, W * 0.28, H * 0.62, '  TU OJO: NADA  ', a, size=44, dotc=LASER)
        pill(img, d, W * 0.72, H * 0.62, '  CÁMARA: LUZ  ', a, size=44, dotc=IRP if on else (120, 120, 120))
    fr.ui.append(f)
    if on:
        glow(fr, (0, 0.09, 1.16), 26, IRP, 0.8)
    head(fr, ['Una luz que tus ojos', 'no pueden ver.'], CYAN, t, t0 + 0.1, kicker='Aprieta un botón')
    lab(fr, 'Recreación', clamp(lt / 0.4))


def s_xray(fr, t, lt, dur):
    """Escáner de rayos X sobre el control: plástico transparente, tarjeta verde, chip, pilas y el LED."""
    t0 = t - lt
    EN.env(fr, 'laboratorio')
    fr.cam = Cam(target=(0, 0.2, 0.1), dist=vfit(3.6), yaw=-30 + lt * 9, pitch=34)
    ts, te = t0 + 0.15, t0 + 1.3
    ys, k = scan_ring(fr, t, ts, te, 0.6, -0.1, center=(0, 0, 0.1), r=1.3)
    e = ease(k)
    if e < 0.98:
        fr.meshes += remote(0, 0, 0, a=1 - e)
    if k > 0.05:
        fr.meshes.append(box(0.5, 0.02, 2.1, PCB, shadow=0, gloss=0.3, edge=False).tf(t=(0, 0.06, 0)))
        fr.meshes.append(box(0.18, 0.04, 0.18, CHIP, shadow=0, gloss=0.6).tf(t=(0, 0.08, 0.2)))
        for i in range(2):
            fr.meshes.append(cyl(0.07, 0.6, BAT, n=20, shadow=0, gloss=0.5).tf(rx=90, t=((i - 0.5) * 0.2, 0.08, -0.9)))
        fr.meshes.append(sphere(0.07, (90, 60, 80), nu=20, nv=10, shadow=0, gloss=0.9).tf(t=(0, 0.1, 1.08)))
        fr.over.append(lambda d, cam, e=e: line3(d, cam, [(0, 0.09, 0.2), (0, 0.1, 1.05)], GOLD, 2.4, a=e))
        ui_label3(fr, (0, 0.1, 1.08), 'LED infrarrojo', a=clamp((lt - 1.2) / 0.4), side=1, length=110, up=150)
        ui_label3(fr, (0, 0.08, 0.2), 'Chip', sub='arma el código', a=clamp((lt - 1.5) / 0.4), side=-1, length=110, up=-120)
        ui_label3(fr, (0.1, 0.08, -0.9), 'Pilas', a=clamp((lt - 1.8) / 0.4), side=1, length=100, up=-160)
    head(fr, ['Así se ve', 'por dentro.'], CYAN, t, t0 + 0.1, kicker='Rayos X')
    lab(fr, 'Recreación · Esquema simplificado', clamp(lt / 0.4))


def s_led(fr, t, lt, dur):
    """Acercamiento al LED: ondas largas saliendo; contador 940 nm."""
    t0 = t - lt
    EN.env(fr, 'laboratorio')
    fr.cam = Cam(target=(0, 0.1, 1.2), dist=vfit(1.6) - lt * 0.05, yaw=-60 + lt * 6, pitch=14)
    fr.meshes += remote(0, 0, 0, led=0.15)
    ir_beam(fr, (0, 0.09, 1.2), (0, 0.4, 3.2), lt * 0.6, col=LASER, alpha=0.7)
    v = cnt(940, t, t0 + 0.4, 1.4)
    bigc(fr, f'{int(v)} nm', 'longitud de onda', a=ease(clamp((lt - 0.3) / 0.4)))
    head(fr, ['Luz infrarroja.'], CYAN, t, t0 + 0.1, kicker='La punta del control')
    lab(fr, 'Escala exagerada', clamp(lt / 0.4))


def s_spectrum(fr, t, lt, dur):
    """Regla de colores 380–750 nm; el marcador sigue hasta 940, donde todo es negro."""
    t0 = t - lt
    EN.env(fr, 'laboratorio')
    fr.cam = Cam(target=(0, 0.3, 0), dist=vfit(4.2), yaw=0, pitch=8)

    def f(img, d, lt=lt):
        a = ease(clamp(lt / 0.4))
        x0, x1, y = W * 0.08, W * 0.92, H * 0.55
        n = 120
        span_ = 380, 1000
        for i in range(n):
            nm = span_[0] + (span_[1] - span_[0]) * i / n
            if nm <= 750:
                hue = (nm - 380) / 370
                stops = [(130, 0, 200), (0, 60, 255), (0, 200, 120), (250, 230, 0), (255, 120, 0), (220, 0, 0)]
                q = hue * (len(stops) - 1)
                j = min(int(q), len(stops) - 2)
                c = mix(stops[j], stops[j + 1], q - j)
            else:
                c = (20, 18, 24)
            xa = x0 + (x1 - x0) * i / n
            d.rectangle((xa, y - 60, xa + (x1 - x0) / n + 1, y + 60), fill=tuple(int(v) for v in c))
        for nm in (380, 750, 940):
            xx = x0 + (x1 - x0) * (nm - 380) / 620
            draw_text(d, (xx, y + 110), str(nm), font('mono', 44), INK, 'mm', a=a)
        k = ease(clamp((lt - 0.8) / 1.6))
        nm = lerp(500, 940, k)
        xx = x0 + (x1 - x0) * (nm - 380) / 620
        d.polygon([(xx, y - 80), (xx - 22, y - 120), (xx + 22, y - 120)], fill=IRP)
        draw_text(d, ((x0 + x0 + (x1 - x0) * 370 / 620) / 2, y - 160), 'LO QUE VES', font('sb', 46), INK, 'mm', a=a)
        if k > 0.95:
            pill(img, d, W / 2, y - 260, '  940: APAGADO PARA TI  ', a, size=44, dotc=LASER)
    fr.ui.append(f)
    head(fr, ['Tus ojos solo ven', 'hasta 750.'], CYAN, t, t0 + 0.1, kicker='Escala real')
    lab(fr, 'nanómetros', clamp(lt / 0.4))


def s_sensor(fr, t, lt, dur):
    """El sensor del celular: una cuadrícula de píxeles que se enciende morada donde llega el infrarrojo."""
    t0 = t - lt
    EN.env(fr, 'laboratorio')
    fr.cam = Cam(target=(0, 0.4, 0), dist=vfit(3.6), yaw=-25 + lt * 7, pitch=50)
    fr.meshes.append(box(2.2, 0.08, 2.2, (40, 40, 46), shadow=0.3, gloss=0.4).tf(t=(0, 0, 0)))
    k = lt
    fr.meshes += remote(0, 1.4, -2.0, rx=-28, s=0.6, led=0.0)
    ir_beam(fr, (0, 1.5, -1.3), (0, 0.15, 0), k * 0.7, alpha=0.6)

    def px(d, cam, lt=lt):
        n = 14
        for i in range(n):
            for j in range(n):
                x = -1.0 + 2.0 * i / (n - 1)
                z = -1.0 + 2.0 * j / (n - 1)
                r = math.hypot(x, z)
                on = clamp((ease(clamp((lt - 0.4) / 1.4)) * 1.2 - r))
                c = mix([(200, 40, 40), (40, 180, 60), (40, 80, 220)][(i + j) % 3], IRW if r < 0.25 else IRP, on)
                dot3(d, cam, (x, 0.09, z), 7, c, 0.95)
    fr.over.append(px)
    head(fr, ['Tu celular sí', 'la capta.'], CYAN, t, t0 + 0.1, kicker='Sensor de la cámara')
    ui_pill(fr, '  LA PINTA MORADA O BLANCA  ', a=ease(clamp((lt - 1.4) / 0.4)), dotc=IRP)
    lab(fr, 'Recreación', clamp(lt / 0.4), where='bl')


def s_blink(fr, t, lt, dur):
    """2º gancho: el LED parpadea y el contador se dispara a 38 000 por segundo."""
    t0 = t - lt
    EN.env(fr, 'laboratorio')
    fr.cam = Cam(target=(0, 0.1, 1.0), dist=vfit(2.0) - lt * 0.08, yaw=30 - lt * 5, pitch=16)
    on = (int(lt * (6 + lt * 18)) % 2) == 0
    fr.meshes += remote(0, 0, 0, led=0.9 if on else 0.0)
    if on:
        glow(fr, (0, 0.09, 1.16), 40, IRP, 0.9)
    v = cnt(38000, t, t0 + 0.5, 2.2)
    bigc(fr, fmt_int(int(v)), 'parpadeos por segundo', a=ease(clamp((lt - 0.3) / 0.4)))
    head(fr, ['Y lo más raro…'], AMBER, t, t0 + 0.05, kicker='¡Ojo!')
    lab(fr, 'Cámara lenta · Recreación', clamp(lt / 0.4))


def s_sun(fr, t, lt, dur):
    """La tele sólo escucha luz que parpadea a 38 kHz: el sol y los focos no la engañan."""
    t0 = t - lt
    sala(fr)
    fr.cam = Cam(target=(0, 1.1, -0.8), dist=vfit(7.0), yaw=-20 + lt * 4, pitch=12)
    fr.meshes += tv(0, -2.2)
    fr.meshes += remote(0.5, 0.3, 0.9, ry=180, rx=-6, s=0.7, led=0.5)
    # foco del techo y sol por la ventana
    fr.meshes.append(sphere(0.25, (255, 240, 200), nu=24, nv=12, shadow=0, gloss=1.0).tf(t=(-1.3, 2.3, -0.4)))
    glow(fr, (-1.3, 2.3, -0.4), 60, (255, 230, 150), 0.6)
    fr.meshes.append(sphere(0.35, (255, 200, 60), nu=24, nv=12, shadow=0, gloss=1.0).tf(t=(1.9, 2.4, -1.8)))
    glow(fr, (1.9, 2.4, -1.8), 80, (255, 200, 60), 0.6)
    ir_beam(fr, (0.5, 0.35, 0.5), (1.3, 0.42, -2.1), lt * 0.8, alpha=0.6)
    a = ease(clamp((lt - 0.6) / 0.4))
    fr.over.append(lambda d, cam: line3(d, cam, [(-1.3, 2.3, -0.4), (1.3, 0.42, -2.1)], LASER, 2.0, dash=12, a=a * 0.7))

    def f(img, d, lt=lt):
        pill(img, d, W / 2, H * 0.62, '  SOLO ESCUCHA 38 000/s  ', ease(clamp((lt - 1.0) / 0.4)), size=44, dotc=LGREEN)
    fr.ui.append(f)
    head(fr, ['No lo confunde', 'con el sol.'], CYAN, t, t0 + 0.1, kicker='Ni con tus focos')
    lab(fr, 'Recreación', clamp(lt / 0.4))


CODE = [1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0]


def s_code(fr, t, lt, dur):
    """El código del botón: 32 pulsos que avanzan como clave Morse."""
    t0 = t - lt
    EN.env(fr, 'laboratorio')
    fr.cam = Cam(target=(0, 0.2, 0.6), dist=vfit(3.4), yaw=-40 + lt * 5, pitch=24)
    fr.meshes += remote(0, 0, -0.6, led=0.6 if int(lt * 8) % 2 else 0.0)

    def f(img, d, lt=lt):
        a = ease(clamp(lt / 0.4))
        x0, y0 = W * 0.06, H * 0.58
        x = x0
        k = clamp((lt - 0.3) / 2.6)
        shown = int(k * 32)
        for i, b in enumerate(CODE[:shown]):
            wv = 18
            d.rectangle((x, y0 - 50, x + wv, y0), fill=IRP)
            x += wv + (54 if b else 20)
            if x > W * 0.94:
                break
        d.line([(x0, y0), (W * 0.94, y0)], fill=(140, 140, 150), width=3)
        draw_text(d, (W * 0.5, y0 + 70), f'{shown} / 32 pulsos', font('mono', 46), INK, 'mm', a=a)
    fr.ui.append(f)
    head(fr, ['Cada botón,', 'un código.'], CYAN, t, t0 + 0.1, kicker='Como clave Morse')
    lab(fr, 'Esquema simplificado', clamp(lt / 0.4))


def s_tv(fr, t, lt, dur):
    """Menos de una décima de segundo… y la tele cambia de canal."""
    t0 = t - lt
    sala(fr)
    fr.cam = Cam(target=(0, 1.2, -2.0), dist=vfit(5.0) - lt * 0.2, yaw=-10 + lt * 5, pitch=8)
    ch = int(clamp((lt - 1.0) / 2.0) * 2.99)
    fr.meshes += tv(0, -2.2, ch=ch)
    fr.meshes += remote(0.2, 0.3, 1.6, ry=180, s=0.8, led=0.6)
    ir_beam(fr, (0.2, 0.35, 1.2), (1.3, 0.42, -2.1), lt * 0.9, alpha=0.5)
    v = min(0.07, 0.07 * clamp((lt - 0.3) / 0.8))
    bigc(fr, f'0.{int(v * 100):02d} s', 'lo que tarda el mensaje', a=ease(clamp((lt - 0.2) / 0.4)), y=0.30)
    head(fr, ['¡Y cambia', 'de canal!'], CYAN, t, t0 + 0.1, kicker='Menos de 0.1 s')
    lab(fr, 'Recreación', clamp(lt / 0.4))


def s_selfie(fr, t, lt, dur):
    """Truco: la cámara de selfie casi no trae filtro infrarrojo; la de atrás sí."""
    t0 = t - lt
    sala(fr)
    fr.cam = Cam(target=(0, 0.9, 0), dist=vfit(3.6), yaw=-20 + lt * 30, pitch=14)
    fr.meshes += phone_m(0, 0.9, 0, rx=-90, s=1.6, scr=scr_tex('cam', 1.0))
    fr.meshes.append(sphere(0.06, (20, 20, 30), nu=16, nv=8, shadow=0, gloss=1.0).tf(t=(0, 1.65, 0.07)))
    fr.meshes.append(sphere(0.09, (20, 20, 30), nu=16, nv=8, shadow=0, gloss=1.0).tf(t=(-0.2, 1.55, -0.08)))
    a = ease(clamp((lt - 0.6) / 0.4))
    ui_label3(fr, (0, 1.65, 0.07), 'Selfie', sub='poco filtro', a=a, side=1, length=110, up=120)
    ui_label3(fr, (-0.2, 1.55, -0.08), 'Trasera', sub='con filtro IR', a=ease(clamp((lt - 1.2) / 0.4)), side=-1, length=110, up=-120)
    head(fr, ['¿No ves nada?', 'Usa la de selfie.'], CYAN, t, t0 + 0.1, kicker='Truco')
    lab(fr, 'Recreación', clamp(lt / 0.4))


def s_pilas(fr, t, lt, dur):
    """Si ninguna cámara ve el destello: las pilas."""
    t0 = t - lt
    sala(fr)
    fr.cam = Cam(target=(0, 0.3, 0), dist=vfit(3.4), yaw=20 + lt * 6, pitch=30)
    fr.meshes += remote(-0.5, 0, 0, ry=-10)
    out = ease(clamp((lt - 0.3) / 0.8))
    for i in range(2):
        b = cyl(0.13, 1.0, BAT, n=24, shadow=0.3, gloss=0.5, top=BAT2).tf(rx=90, t=(0.6 + i * 0.32, 0.13 + 0.6 * (1 - out), -0.4))
        fr.meshes.append(b)
        fr.meshes.append(cyl(0.135, 0.18, BAT2, n=24, shadow=0, gloss=0.6).tf(rx=90, t=(0.6 + i * 0.32, 0.13 + 0.6 * (1 - out), 0.5)))
    ui_pill(fr, '  REVISA LAS PILAS  ', a=ease(clamp((lt - 0.8) / 0.4)), dotc=AMBER)
    head(fr, ['¿Con ninguna?', 'Las pilas.'], CYAN, t, t0 + 0.1, kicker='Último truco')
    lab(fr, 'Recreación', clamp(lt / 0.4), where='bl')


def s_share(fr, t, lt, dur):
    t0 = t - lt
    sala(fr)
    fr.cam = Cam(target=(0, 0.3, 0), dist=vfit(4.4), yaw=-20 + lt * 6, pitch=34)
    fr.meshes += remote(0, 0, 0, ry=lt * 15, led=0.5 if int(lt * 4) % 2 else 0)

    def f(img, d, lt=lt):
        yy = H * 0.66
        a = ease(clamp((lt - 1.2) / 0.4))
        pill(img, d, W / 2 - 170, yy, '  SÍ  ', a, size=54, dotc=LGREEN)
        pill(img, d, W / 2 + 170, yy, '  NO  ', a, size=54, dotc=LASER)
        draw_text(d, (W / 2, H * 0.29), 'MENTE EN ÓRBITA', font('mono', 60), INK, 'mm', a=ease(clamp(lt / 0.5)), spacing=5)
    fr.ui.append(f)
    head(fr, ['Mándaselo a quien', 'pierde el control.'], CYAN, t, t0 + 0.1, kicker='¿Lo sabías?')


def s_loop(fr, t, lt, dur):
    s_hook(fr, t, lt, dur, loop=True)


SHOTS = [(('c0', 0), s_hook), (('c0', 1), s_eye), (('c0', 2), s_xray), (('c0', 3), s_led), (('c0', 4), s_spectrum),
         (('c0', 5), s_sensor), (('c0', 6), s_blink), (('c0', 7), s_sun), (('c0', 8), s_code), (('c0', 9), s_tv),
         (('c0', 10), s_selfie), (('c0', 11), s_pilas), (('c0', 12), s_share), (('c0', 13), s_loop)]

if __name__ == '__main__':
    S.main(SHOTS, {})
