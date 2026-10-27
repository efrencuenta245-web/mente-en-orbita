"""Mente en órbita — Respuestas: ¿por qué hay que esperar 3 meses después de la vasectomía? (video extra).
Responde a @menkultrx pero con gancho para todo público.
Escenas: campo quirúrgico (corte en el primer segundo y espermatozoides que siguen del otro lado) · escáner ·
pregunta del comentario · el corte frena a los nuevos · del otro lado ya había millones · reserva junto a la próstata
y las vesículas · siguen vivos semanas · cada eyaculación vacía una parte · laboratorio (semana 8, microscopio) ·
mientras: otro método · cierre en loop al campo quirúrgico."""
import math, os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw
import anim
import vasec as VS  # modelos anatómicos, sombreado y ayudantes (fija anim.PHR al importarse; se sobrescribe abajo)
import moto_model as mm
from nc import proj, P2
from fo import clip_near, line3
from anim import (W, H, S, F, B, M, seg, ease, lerp, sc3, P, clamp, glow_of, VIOLET, BLUE, CYAN, ORANGE)
from gps_geo import (norm, cam_keys, polyline3, glow_dot)

FPS = 24
RED = (255, 90, 90)
GREEN = (90, 255, 150)
GOLD = (255, 205, 100)
SPERM = (235, 245, 255)
SCAN = (120, 235, 255)

PHR = [
    (0.3, 5.0, "Te hacen la vasectomía hoy... y todavía puedes embarazar a alguien.", {7, 9}),
    (5.5, 7.0, "Así se ve por dentro.", {4}),
    (7.5, 11.0, "Me preguntaron: ¿por qué hay que esperar 3 meses?", {7, 8}),
    (11.5, 15.6, "El corte frena a los espermatozoides nuevos que bajan de los testículos.", {6}),
    (16.1, 19.6, "Pero del otro lado del corte ya había millones en camino.", {8}),
    (20.1, 24.2, "Se quedan guardados cerca de la próstata y las vesículas seminales.", {2, 6}),
    (24.7, 27.4, "Y ahí pueden seguir vivos durante semanas.", {4, 6}),
    (27.9, 33.2, "Cada eyaculación saca una parte: se necesitan unas 20 o más para vaciarlos.", {7, 8}),
    (33.7, 37.4, "Por eso, desde la semana 8, se hace un análisis de semen.", {4, 10}),
    (37.9, 42.6, "Si no hay espermatozoides, o solo unos pocos que no se mueven, ya funciona.", {13}),
    (43.1, 46.9, "Y si todavía aparecen, se repite el análisis unas semanas después.", {2, 6}),
    (47.4, 51.9, "Mientras, hay que usar otro método: no esperar es la falla más común.", {5, 12}),
    (52.4, 57.9, "Mándaselo a alguien que se la quiere hacer. ¿Sabías lo de la espera? Sí o no.", {0, 14}),
]
anim.PHR = PHR
anim.PH = anim.build_phrases()
for _i in range(len(anim.PH) - 1):
    anim.PH[_i]['b'] = min(anim.PH[_i]['b'], anim.PH[_i + 1]['a'] - 0.31)
_ST = [list(ph['starts']) for ph in anim.PH]


def WT(i, w):
    return _ST[i][w]


DUR = 60.9
NF = int(DUR * FPS)
CUTS = (5.25, 7.25, 11.25, 15.85, 19.85, 27.65, 33.45, 47.15, 52.15)
ENVS = ('hook', 'scan', 'comment', 'cut', 'beyond', 'reserve', 'drain', 'lab', 'method', 'end')
T_OUT = 58.5
T_SNIP = 0.75
T_SCAN = WT(1, 0) + 0.05


def env_at(t):
    for i, ct in enumerate(CUTS):
        if t < ct:
            return ENVS[i]
    return ENVS[-1]


VAS, VAS_CUM, VAS_LEN, S_CUT, GAP = VS.VAS, VS.VAS_CUM, VS.VAS_LEN, VS.S_CUT, VS.GAP
URETHRA = VS.URETHRA
U_CUM = VS.arclen(URETHRA)
CUT_PT = [VS.at_s(VAS[i], VAS_CUM[i], np.array([S_CUT]))[0] for i in range(2)]

# =====================================================================
# Reserva: espermatozoides guardados en la parte final del conducto (ampolla) y junto a las vesículas
# =====================================================================
_rs = np.random.RandomState(12)
RES_PTS, RES_PH = [], []
for i in range(2):
    s0 = VAS_LEN * 0.70
    for k in range(70):
        s = s0 + (VAS_LEN - s0) * _rs.rand()
        p = VS.at_s(VAS[i], VAS_CUM[i], np.array([s]))[0] + _rs.normal(0, 0.22, 3)
        RES_PTS.append(p)
        RES_PH.append(_rs.rand() * 6.28)
    sg = 1 if i == 0 else -1
    for k in range(45):
        u = _rs.uniform(-1, 1)
        p = np.array([sg * 2.7, 3.6, 5.8]) + VS.rot_z(sg * math.radians(32)) @ np.array([2.1 * u, _rs.normal(0, 0.35), _rs.normal(0, 0.35)])
        RES_PTS.append(p)
        RES_PH.append(_rs.rand() * 6.28)
RES_PTS = np.array(RES_PTS)
RES_ORDER = _rs.permutation(len(RES_PTS))  # orden en que se vacían


def sperm_dot(la, c, p, d, a, r=2.8, t=0.0, ph=0.0, tail=0.55, col=SPERM):
    """cabeza brillante + colita ondulante (en la capa de luz)"""
    if a <= 0.01:
        return
    x, y, dep = proj(*p, c)
    if dep < 0.3:
        return
    d = norm(d)
    pts = []
    side = norm(np.cross(d, np.array([0.0, 0.0, 1.0])) + 1e-6)
    for j in range(6):
        q = p - d * tail * j / 5 + side * 0.11 * tail * math.sin(t * 14 + ph + j * 1.3) * j / 5
        qx, qy, qd = proj(*q, c)
        if qd < 0.3:
            break
        pts.append((qx * S, qy * S))
    if len(pts) > 1:
        la.line(pts, fill=sc3((170, 200, 240), a * 0.7), width=max(1, int(1.6 * S * max(1.0, r / 3.0))))
    glow_dot(la, x * S, y * S, r * S, col, a)


def flow_on(la, c, i, s_arr, a, t, r=2.8, sign=1.0):
    """espermatozoides sobre el conducto i, orientados según el avance"""
    for k, s in enumerate(s_arr):
        p = VS.at_s(VAS[i], VAS_CUM[i], np.array([s]))[0]
        p2 = VS.at_s(VAS[i], VAS_CUM[i], np.array([s + 0.25 * sign]))[0]
        sperm_dot(la, c, p, p2 - p, a, r, t, k * 1.7, 0.45)


def reserve_draw(la, c, t, level, a, r=2.4):
    n = int(len(RES_PTS) * clamp(level))
    keep = set(RES_ORDER[len(RES_PTS) - n:].tolist()) if n < len(RES_PTS) else None
    for k, p in enumerate(RES_PTS):
        if keep is not None and k not in keep:
            continue
        ph = RES_PH[k]
        q = p + 0.08 * np.array([math.sin(t * 2.1 + ph), math.cos(t * 1.7 + ph * 1.3), math.sin(t * 1.3 + ph * 0.7)])
        d = np.array([math.cos(ph + t * 0.6), math.sin(ph * 1.7), math.sin(ph + t * 0.4)])
        sperm_dot(la, c, q, d, a * (0.65 + 0.35 * math.sin(t * 3 + ph)), r, t, ph, 0.32)


# =====================================================================
# Campo quirúrgico del gancho (mm)
# =====================================================================
HOOK_VAS = VS.HOOK_VAS_L
HOOK_CUM = VS.HOOK_CUM


def hook_scene(base, bd, od, la, c, t, cut_k, sc_k, flow_a, xray=0.0):
    L = norm((-0.3, 0.9, -0.3))
    bd.polygon([P2(*p, c) for p in clip_near([(-400, -4.2, -300), (400, -4.2, -300), (400, -4.2, 400), (-400, -4.2, 400)], c, 1.0)], fill=(44, 104, 112))
    # pliegues de la tela
    w = max(1, int(1.4 * S))
    for k in range(-8, 9):
        line3(bd, c, (k * 22 + 6 * math.sin(k), -4.15, -260), (k * 22 - 4, -4.15, 360), (52, 116, 124), w, 1.0)
    vst = {'spec': 0.55}
    if xray > 0.01:
        vst = {'spec': 0.55, 'alpha': int(255 - 150 * xray)}
    fl = VS.org_faces(c, VS.hook_vas_model(cut_k), L, {'vas': vst}, near=1.0)
    if sc_k > 0.01:
        op = math.radians(26) * (1 - ease(seg(t, T_SNIP - 0.4, T_SNIP)))
        if t > T_SNIP + 0.2:
            op = math.radians(26) * ease(seg(t, T_SNIP + 0.2, T_SNIP + 0.6))
        mid = VS.at_s(HOOK_VAS, HOOK_CUM, np.array([HOOK_CUM[-1] / 2]))[0]
        pos = mid + np.array([0.0, 1.0 + 70.0 * (1 - sc_k), -30.0 - 20 * (1 - sc_k)])
        Rsc = np.array([[0, 1.0, 0], [0, 0, 1.0], [1.0, 0, 0]])
        fl += VS.org_faces(c, VS.scissors_model(op), L, {'sc': {'spec': 0.9}}, pos=pos, Rm=Rsc, near=1.0, default={'spec': 0.8})
    VS.draw_faces(bd, od, fl)
    mid_s = HOOK_CUM[-1] / 2
    if 0 < cut_k and t < T_SNIP + 0.5:
        mid = VS.at_s(HOOK_VAS, HOOK_CUM, np.array([mid_s]))[0]
        x, y, dep = proj(*mid, c)
        glow_dot(la, x * S, y * S, (20 + 60 * (t - T_SNIP)) * S, (255, 255, 255), 0.7 * (1 - (t - T_SNIP) / 0.5))
    if flow_a > 0.01:
        # del lado derecho (hacia la próstata) siguen avanzando
        sep = 1.5 + 4.0 * cut_k
        for k in range(16):
            s = mid_s + 4.0 + ((k / 16.0) * (HOOK_CUM[-1] / 2 - 6) + 9.0 * t) % (HOOK_CUM[-1] / 2 - 6)
            p = VS.at_s(HOOK_VAS, HOOK_CUM, np.array([s]))[0] + np.array([sep * 0.0, 1.55, 0.0])
            p2 = VS.at_s(HOOK_VAS, HOOK_CUM, np.array([s + 1.0]))[0] + np.array([0, 1.55, 0])
            sperm_dot(la, c, p - np.array([0, 1.55, 0]), p2 - p, flow_a, 5.2, t, k * 2.1, 3.2, (150, 235, 255))
        # del lado izquierdo (testículo): se detienen en la punta
        for k in range(8):
            s = mid_s - 3.5 - (k * 2.6 + 0.6 * math.sin(t * 3 + k))
            p = VS.at_s(HOOK_VAS, HOOK_CUM, np.array([s]))[0] + np.array([-sep * 0.0, 1.55, 0.0])
            sperm_dot(la, c, p - np.array([0, 1.55, 0]), np.array([1.0, 0, 0]), flow_a * 0.5, 4.0, t, k * 1.3, 2.6, (150, 235, 255))
    return mid_s


# =====================================================================
# Cámaras (t, D, phi, yaw, cy, fx, fy, fz)
# =====================================================================
KEYS = {
    'hook': [(0.0, 96, 56, 10, 980, 4, 0, 2), (T_SNIP + 0.2, 90, 58, 12, 980, 4, 0, 2), (5.25, 118, 50, 22, 980, 14, 0, 2)],
    'scan': [(5.25, 52, 10, -36, 1000, 0, -1.0, 2.0), (7.25, 47, 12, -26, 1000, 0, -1.0, 2.0)],
    'comment': [(7.25, 60, 12, -14, 1060, 0, -0.5, 2.0), (11.25, 56, 14, 4, 1060, 0, -0.5, 2.0)],
    'cut': [(11.25, 15, 8, -32, 1000, 3.0, -5.2, 0.0), (15.85, 12.5, 10, -20, 1000, 3.0, -5.2, 0.0)],
    'beyond': [(15.85, 22, 8, -46, 1000, 4.4, -2.0, -0.3), (19.85, 24, 12, -62, 1000, 4.8, 2.4, 1.2)],
    'reserve': [(19.85, 24, 18, 160, 980, 0, 3.4, 4.5), (27.65, 20, 22, 186, 980, 0, 3.2, 4.5)],
    'drain': [(27.65, 32, 12, 200, 1040, 0, 1.6, 3.0), (33.45, 30, 15, 214, 1040, 0, 1.6, 3.0)],
    'lab': [(33.45, 122, 14, -22, 980, 0, 126, 64), (40.5, 104, 16, -8, 980, 0, 128, 64), (47.15, 96, 18, 2, 980, 0, 128, 64)],
    'method': [(47.15, 250, 18, -38, 1000, 0, 88, 0), (52.15, 220, 20, -26, 1000, 0, 88, 0)],
    'end': [(52.15, 112, 52, 20, 980, 12, 0, 2), (DUR, 96, 56, 10, 980, 4, 0, 2)],
}


def cam_for(env, t):
    return cam_keys(t, KEYS[env], False)


def model_above(model, ys):
    m = mm.Model()
    m.F = [f for f in model.F if f[0][:, 1].mean() > ys]
    return m


# =====================================================================
# Render
# =====================================================================
DARK = []
CARD = [None]


def render(t):
    env = env_at(t)
    c = cam_for(env, t)
    LA = Image.new("RGB", (W, H), (0, 0, 0))
    la = ImageDraw.Draw(LA)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    info = {}

    if env in ('hook', 'end'):
        base = Image.fromarray(VS.bg_studio((40, 64, 70), (18, 34, 40), (40, 60, 60)).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        if env == 'hook':
            cut_k = ease(seg(t, T_SNIP + 0.05, T_SNIP + 0.6))
            sc_k = 1.0 - ease(seg(t, T_SNIP + 0.7, T_SNIP + 1.6))
            flow_a = ease(seg(t, WT(0, 5) - 0.6, WT(0, 6)))
            xray = ease(seg(t, WT(0, 5) - 0.7, WT(0, 5) + 0.2))
        else:
            xray = 0.0
            # cierre en loop: vuelve al campo quirúrgico del inicio (conducto entero, tijera esperando)
            cut_k = 0.0
            sc_k = ease(seg(t, T_OUT - 1.2, DUR - 0.2))
            flow_a = 0.0
        mid_s = hook_scene(base, bd, od, la, c, t, cut_k, sc_k, flow_a, xray)
        if env == 'hook':
            # anillo del escáner recorre la mitad derecha (adelanto del sello)
            ks = seg(t, WT(0, 5) - 0.8, WT(0, 5) + 0.4)
            if 0 < ks < 1:
                s_r = HOOK_CUM[-1] / 2 + 3 + ks * (HOOK_CUM[-1] / 2 - 3)
                pc = VS.at_s(HOOK_VAS, HOOK_CUM, np.array([s_r]))[0]
                ring = [tuple(pc + np.array([0, 4.2 * math.cos(q), 4.2 * math.sin(q)])) for q in np.linspace(0, 2 * math.pi, 33)]
                polyline3(la, c, ring, sc3(SCAN, math.sin(math.pi * ks)), max(2, int(4 * S)), 1.0)
        info['right'] = VS.at_s(HOOK_VAS, HOOK_CUM, np.array([mid_s + 22]))[0] + np.array([0, 1.5, 0])
        info['left'] = VS.at_s(HOOK_VAS, HOOK_CUM, np.array([mid_s - 12]))[0] + np.array([0, 1.5, 0])
        info['cut'] = VS.at_s(HOOK_VAS, HOOK_CUM, np.array([mid_s]))[0]
    elif env == 'scan':
        base = Image.fromarray(VS.BG_ANAT.astype(np.uint8))
        bd = ImageDraw.Draw(base)
        ys = lerp(19.0, -13.5, ease(seg(t, T_SCAN, T_SCAN + 1.5)))
        VS.glass(la, c, VS.BODY, (120, 190, 255), 0.6, ('body',))
        VS.glass(la, c, VS.BODY, (255, 190, 170), 0.35, ('scrot',))
        fl = VS.org_faces(c, model_above(VS.ANAT_CUT, ys), VS.ANAT_L, VS.STY_BASE)
        VS.draw_faces(bd, od, fl)
        if T_SCAN - 0.1 <= t <= T_SCAN + 1.6:
            wv = max(2, int(4 * S))
            rx = 14.6 + 2.8 * math.exp(-((ys - 5.0) / 9.0) ** 2) if ys > -1 else 16.5
            pts = [(rx * math.cos(q), ys, 2.5 + (11.5 if math.sin(q) > 0 else 9.0) * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 73)]
            polyline3(la, c, pts, sc3(SCAN, 1.0), wv, 0.5)
            pts2 = [(rx * 1.04 * math.cos(q), ys + 0.25, 2.5 + 11.9 * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 73)]
            polyline3(la, c, pts2, sc3(SCAN, 0.35), max(1, int(2 * S)), 0.5)
        # los dos cortes ya hechos
        for i in range(2):
            for sg in (-1, 1):
                p = VS.at_s(VAS[i], VAS_CUM[i], np.array([S_CUT + sg * GAP / 2]))[0]
                if p[1] > ys:
                    x, y, dep = proj(*p, c)
                    glow_dot(la, x * S, y * S, 4.0 * S, (255, 150, 90), 0.8)
        info['testis'] = VS.TESTIS_C[0]
    elif env in ('comment', 'cut', 'beyond', 'reserve', 'drain'):
        base = Image.fromarray(VS.BG_ANAT.astype(np.uint8))
        bd = ImageDraw.Draw(base)
        if env == 'comment':
            st = VS.anat_styles(('vas', 'testis', 'epi', 'prostate', 'ves'), 0.5)
            bk = 0.5
        elif env in ('cut', 'beyond'):
            st = VS.anat_styles(('vas', 'testis', 'epi'), 0.5)
            bk = 0.5
        else:
            st = VS.anat_styles(('prostate', 'ves', 'vas', 'urethra'), 0.5)
            st['bladder'] = {'alpha': 70, 'dim': 0.6}
            bk = 0.35
        VS.draw_anatomy(base, bd, od, la, c, t, VS.ANAT_CUT, st, bk)
        # puntas selladas
        for i in range(2):
            for sg in (-1, 1):
                p = VS.at_s(VAS[i], VAS_CUM[i], np.array([S_CUT + sg * GAP / 2]))[0]
                x, y, dep = proj(*p, c)
                glow_dot(la, x * S, y * S, (5.0 if env == 'cut' else 3.5) * S, (255, 150, 90), 0.85)
        up_end = S_CUT - GAP / 2
        if env == 'comment':
            for i in range(2):
                s = (np.arange(10) / 10.0 * up_end + 4.0 * t) % up_end
                flow_on(la, c, i, s, 0.55, t, 2.4)
            reserve_draw(la, c, t, 1.0, 0.5, 2.0)
        if env == 'cut':
            k = ease(seg(t, 11.4, 11.9))
            for i in range(2):
                s = (np.arange(14) / 14.0 * up_end + 3.2 * (t - 11.25)) % up_end
                flow_on(la, c, i, s, k, t, 3.0)
                # se juntan en la punta y se desvanecen
                rs = np.random.RandomState(i + 4)
                for j in range(12):
                    ph = ((t - 11.3) * 0.45 + j / 12.0) % 1.0
                    p = VS.at_s(VAS[i], VAS_CUM[i], np.array([up_end - 0.12 - 0.55 * rs.rand()]))[0] + rs.normal(0, 0.12, 3)
                    sperm_dot(la, c, p, np.array([rs.normal(), 1.0, rs.normal()]), k * (1 - ph) * 0.9, 2.6, t, j, 0.35)
                # del otro lado: brillan tenues (anticipo)
                s2 = S_CUT + GAP / 2 + (np.arange(10) / 10.0 * 6.0 + 1.6 * (t - 11.25)) % 6.0
                flow_on(la, c, i, s2, 0.35 * ease(seg(t, WT(3, 9), WT(3, 11))), t, 2.6)
            info['cut'] = CUT_PT[0]
            info['up'] = VS.at_s(VAS[0], VAS_CUM[0], np.array([up_end - 2.2]))[0]
        if env == 'beyond':
            k = ease(seg(t, 16.0, 16.5))
            glow_k = ease(seg(t, WT(4, 7) - 0.3, WT(4, 8) + 0.2))
            for i in range(2):
                lo = S_CUT + GAP / 2 + 0.2
                span_ = VAS_LEN - lo
                s = lo + (np.arange(36) / 36.0 * span_ + 3.8 * (t - 15.85)) % span_
                flow_on(la, c, i, s, k * (0.7 + 0.3 * glow_k), t, 2.8 + 0.6 * glow_k)
                s_up = (np.arange(8) / 8.0 * up_end + 2.5 * t) % up_end
                flow_on(la, c, i, s_up, 0.25, t, 2.2)
            reserve_draw(la, c, t, ease(seg(t, 17.2, 19.6)), 0.8 * k, 2.2)
            info['cut'] = CUT_PT[0]
            info['beyond'] = VS.at_s(VAS[0], VAS_CUM[0], np.array([S_CUT + 6.0]))[0]
        if env == 'reserve':
            k = ease(seg(t, 20.0, 20.5))
            reserve_draw(la, c, t, 1.0, k, 2.6)
            info['prostate'] = np.array([0, 1.6, 4.8])
            info['ves'] = np.array([3.6, 4.2, 6.6])
            info['amp'] = VS.at_s(VAS[1], VAS_CUM[1], np.array([VAS_LEN * 0.86]))[0]
        if env == 'drain':
            t0, t1 = WT(7, 2) - 0.2, 33.0
            n = clamp((t - t0) / (t1 - t0)) * 22.0
            ni = int(n)
            info['n_ej'] = ni
            level = 1.0 - ni / 22.0 * 0.97
            info['level'] = level
            reserve_draw(la, c, t, level, 0.95, 2.4)
            # pulso de salida por la uretra en cada eyaculación
            if ni >= 1:
                ph = n - ni
                if ph < 0.6:
                    a = math.sin(math.pi * ph / 0.6)
                    for j in range(10):
                        s = (ph / 0.6) * U_CUM[-1] * 1.1 - j * 0.45
                        if 0 <= s <= U_CUM[-1]:
                            p = VS.at_s(URETHRA, U_CUM, np.array([s]))[0]
                            p2 = VS.at_s(URETHRA, U_CUM, np.array([s + 0.3]))[0]
                            sperm_dot(la, c, p, p2 - p, a, 2.6, t, j, 0.4)
            info['ure'] = URETHRA[-8]
            info['ves'] = np.array([3.6, 4.2, 6.6])
    elif env == 'lab':
        base = Image.fromarray(VS.bg_studio((206, 214, 226), (176, 184, 196), (20, 20, 20)).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        L = norm((-0.4, 0.85, -0.4))
        fl = VS.org_faces(c, VS.LAB, L, {'floor': {'spec': 0.1}, 'wall': {'spec': 0.0}}, near=5.0, default={'spec': 0.25})
        fl += VS.org_faces(c, VS.MICRO, L, {}, near=5.0, default={'spec': 0.6})
        VS.draw_faces(bd, od, fl)
        x, y, dep = proj(0, 113.6, 60, c)
        glow_dot(la, x * S, y * S, 8 * S, (255, 250, 220), 0.7)
        info['micro'] = (0, 150, 66)
    else:  # method: consultorio
        base = Image.fromarray(VS.bg_studio((220, 232, 228), (200, 212, 210), (10, 10, 10)).astype(np.uint8))
        bd = ImageDraw.Draw(base)
        L = norm((-0.3, 0.85, -0.4))
        fl = VS.org_faces(c, VS.CLINIC, L, {'floor': {'spec': 0.2}, 'wall': {'spec': 0.0}, 'lamp': {'spec': 0.4}}, near=5.0, default={'spec': 0.25})
        VS.draw_faces(bd, od, fl)
        w = max(1, int(1.2 * S))
        for k in range(-10, 12):
            line3(bd, c, (k * 30, 0.2, -250), (k * 30, 0.2, 296), (178, 186, 190), w, 5.0)
        for k in range(-8, 19):
            line3(bd, c, (-300, 0.2, k * 30), (300, 0.2, k * 30), (178, 186, 190), w, 5.0)

    # ---------- composición ----------
    arr = np.asarray(base, np.float32)
    imgA = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    imgB = Image.alpha_composite(imgA, ov).convert("RGB")
    LAa = np.asarray(LA, np.float32)
    gl = glow_of(LA, 4)
    out = np.asarray(imgB, np.float32) + LAa + 1.3 * gl
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    out = out * (0.5 + 0.5 * np.clip(yy / (H * 0.28), 0, 1))
    f = 1.0
    for ct in CUTS:
        f = min(f, clamp(abs(t - ct) / 0.25))
    out = out * f
    out = out * (1 - 0.88 * seg(t, T_OUT, T_OUT + 0.8) * (1 - seg(t, DUR - 1.2, DUR - 0.3)))
    L2 = Image.new("RGB", (W, H), (0, 0, 0))
    l2 = ImageDraw.Draw(L2)
    anim.draw_caption(l2, t)
    DARK.clear()
    CARD[0] = None
    if env in ('hook', 'end', 'lab', 'method'):
        DARK.append((40, 150, 1040, 420, 0.95))
    hud(l2, c, t, env, info)
    if DARK:
        mk = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(mk)
        for (x0, y0, x1, y1, a) in DARK:
            md.rounded_rectangle((*P(x0, y0), *P(x1, y1)), radius=int(30 * S), fill=int(255 * 0.66 * a))
        out = out * (1 - np.asarray(mk, np.float32)[..., None] / 255.0)
    if CARD[0] is not None:
        ca = np.asarray(CARD[0], np.float32)
        al = ca[..., 3:4] / 255.0
        out = out * (1 - al) + ca[..., :3] * al
    out = out + np.asarray(L2, np.float32) + 1.2 * glow_of(L2, 3)
    out = out * (seg(t, 0.0, 0.3) * (1 - seg(t, DUR - 0.5, DUR)))
    return np.clip(out, 0, 255).astype(np.uint8)


# =====================================================================
# HUD
# =====================================================================
def check_icon(l2, x, y, r, a, col=GREEN):
    VS.check_icon(l2, x, y, r, a, col)


def hud(l2, c, t, env, info):
    def label(txt, target, text_pos, anchor, a, col=(225, 228, 245), size=30):
        if a <= 0:
            return
        f = F(B, size)
        tw = f.getlength(txt) / S
        tx, ty = text_pos
        DARK.append(((tx - tw - 20) if anchor == "rm" else tx - 20, ty - 28, (tx + 20) if anchor == "rm" else tx + tw + 20, ty + 28, a * 0.85))
        l2.text(P(tx, ty), txt, font=f, fill=sc3(col, a), anchor=anchor)
        ex = (tx - tw - 14) if anchor == "rm" else (tx + tw + 14)
        l2.line([P(*target), P(ex, ty)], fill=sc3((190, 190, 230), a), width=max(1, int(2 * S)))
        rr = 6 * S
        px, py = P(*target)
        l2.ellipse((px - rr, py - rr, px + rr, py + rr), outline=sc3((240, 240, 255), a), width=max(1, int(2 * S)))

    def pill(txt, y, a, col=BLUE, w=560, size=36):
        if a <= 0:
            return
        DARK.append((540 - w / 2, y - 42, 540 + w / 2, y + 42, a))
        l2.rounded_rectangle((*P(540 - w / 2, y - 42), *P(540 + w / 2, y + 42)), radius=int(42 * S), outline=sc3(col, a), width=max(2, int(3 * S)))
        l2.text(P(540, y), txt, font=F(B, size), fill=sc3((240, 244, 255), a), anchor="mm")

    def note(txt, a, y=1860):
        if a > 0:
            DARK.append((1040 - F(B, 22).getlength(txt) / S - 14, y - 20, 1054, y + 20, a * 0.6))
            l2.text(P(1040, y), txt, font=F(B, 22), fill=sc3((200, 200, 220), a * 0.9), anchor="rm")

    def win(a, b, e=0.4):
        return ease(seg(t, a, a + e)) * (1 - ease(seg(t, b - e, b)))

    def P3(p):
        sx, sy, _ = proj(*p, c)
        return (sx, sy)

    def calendar(x0, y0, weeks_on, a, hi=None, cols=4, cell=74, gapc=12, label_txt=None):
        """12 semanas (3 meses) en cuadritos"""
        DARK.append((x0 - 24, y0 - 70, x0 + cols * (cell + gapc) + 12, y0 + 3 * (cell + gapc) + 20, a))
        if label_txt:
            l2.text(P(x0, y0 - 40), label_txt, font=F(B, 28), fill=sc3((220, 225, 245), a), anchor="lm")
        for k in range(12):
            r_, q_ = divmod(k, cols)
            x = x0 + q_ * (cell + gapc)
            y = y0 + r_ * (cell + gapc)
            on = k < weeks_on
            col = (hi if (hi and k + 1 == hi) else (CYAN if on else (90, 100, 130)))
            l2.rounded_rectangle((*P(x, y), *P(x + cell, y + cell)), radius=int(12 * S), outline=sc3(col, a), width=max(2, int(3 * S)),
                                 fill=sc3(col, a * 0.25) if on else None)
            l2.text(P(x + cell / 2, y + cell / 2), f"{k + 1}", font=F(B, 30), fill=sc3((235, 240, 255), a * (1.0 if on else 0.6)), anchor="mm")

    for ct in CUTS:
        if abs(t - ct) < 0.25:
            return
    if env == 'hook':
        pill("HOY: VASECTOMÍA", 1560, win(0.2, WT(0, 6) - 0.1), (255, 220, 160), 560, 38)
        a = win(WT(0, 6) - 0.1, 5.2)
        if a > 0:
            pill("AÚN FÉRTIL", 1560, a, RED, 480, 44)
            label("YA ESTABAN DEL OTRO LADO", P3(tuple(info['right'])), (1020, 1300), "rm", a, (255, 236, 210), 28)
        a = win(1.2, 5.2)
        if a > 0:
            label("CORTE", P3(tuple(info['cut'])), (60, 640), "lm", a * (1 - ease(seg(t, WT(0, 6) - 0.4, WT(0, 6)))), (255, 210, 190))
        note("RECREACIÓN · EL CONDUCTO MIDE 2 A 3 mm", win(0.6, 5.2))
    if env == 'scan':
        pill("ESCÁNER: RAYOS X", 1600, win(T_SCAN - 0.1, 7.2), SCAN, 560, 36)
        note("MODELO ANATÓMICO SIMPLIFICADO", win(5.6, 7.2))
    if env == 'comment':
        a = win(7.4, 11.2)
        if a > 0:
            # tarjeta del comentario (capa opaca, no aditiva)
            cardim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            cd = ImageDraw.Draw(cardim)
            al = int(255 * a)
            dy = 30 * (1 - ease(seg(t, 7.4, 7.9)))
            x0, y0, x1, y1 = 110, 520 + dy, 970, 760 + dy
            cd.rounded_rectangle((*P(x0, y0), *P(x1, y1)), radius=int(34 * S), fill=(246, 246, 250, al))
            cx, cy = x0 + 80, y0 + 90
            cd.ellipse((*P(cx - 46, cy - 46), *P(cx + 46, cy + 46)), fill=(120, 110, 230, al))
            cd.text(P(cx, cy), "M", font=F(B, 46), fill=(255, 255, 255, al), anchor="mm")
            cd.text(P(x0 + 150, y0 + 66), "¿Por qué hay que esperar", font=F(B, 44), fill=(30, 32, 44, al), anchor="lm")
            cd.text(P(x0 + 150, y0 + 122), "3 meses?", font=F(B, 44), fill=(30, 32, 44, al), anchor="lm")
            cd.text(P(x0 + 150, y0 + 186), "Respondiendo a @menkultrx", font=F(B, 28), fill=(110, 114, 130, al), anchor="lm")
            CARD[0] = cardim
        a = win(WT(2, 6) - 0.2, 11.2)
        if a > 0:
            wk = int(12 * ease(seg(t, WT(2, 6) - 0.1, WT(2, 8) + 0.6)))
            calendar(330, 1300, wk, a, label_txt="12 SEMANAS ≈ 3 MESES")
        pill("RESPUESTAS", 1760, win(7.6, 11.2), VIOLET, 420, 34)
    if env == 'cut':
        a = win(11.6, 15.8)
        if a > 0:
            label("CORTE SELLADO", P3(tuple(info['cut'])), (1020, 700), "rm", a, (255, 196, 150))
            label("NUEVOS: YA NO PASAN", P3(tuple(info['up'])), (60, 1400), "lm", ease(seg(t, WT(3, 4) - 0.2, WT(3, 4) + 0.2)) * a, (220, 236, 255))
        pill("EL CORTE FUNCIONA AL INSTANTE", 1640, win(WT(3, 2) - 0.2, 15.8), GREEN, 860, 34)
        note("GROSOR EXAGERADO PARA VERLO", win(11.6, 15.8))
    if env == 'beyond':
        a = win(16.3, 19.8)
        if a > 0:
            label("CORTE", P3(tuple(info['cut'])), (60, 1460), "lm", a, (255, 196, 150))
            label("YA IBAN EN CAMINO", P3(tuple(info['beyond'])), (1020, 640), "rm", ease(seg(t, WT(4, 5) - 0.2, WT(4, 5) + 0.2)) * a, (255, 236, 210))
        a = win(WT(4, 9) - 0.3, 19.8)
        if a > 0:
            DARK.append((190, 1540, 890, 1760, a))
            l2.text(P(540, 1610), "MILLONES", font=F(M, 84), fill=sc3((240, 246, 255), a), anchor="mm")
            l2.text(P(540, 1710), "QUEDAN DEL OTRO LADO", font=F(B, 32), fill=sc3(RED, a), anchor="mm")
        note("MODELO SIMPLIFICADO · CANTIDAD ILUSTRATIVA", win(16.3, 19.8))
    if env == 'reserve':
        a = win(20.3, 27.6)
        if a > 0:
            label("PRÓSTATA", P3(tuple(info['prostate'])), (60, 1400), "lm", ease(seg(t, WT(5, 8) - 0.2, WT(5, 8) + 0.2)) * a, (255, 196, 186))
            label("VESÍCULAS SEMINALES", P3(tuple(info['ves'])), (1020, 600), "rm", ease(seg(t, WT(5, 10) - 0.2, WT(5, 10) + 0.2)) * a, (255, 226, 190))
            label("FINAL DEL CONDUCTO", P3(tuple(info['amp'])), (60, 760), "lm", ease(seg(t, WT(5, 3) - 0.2, WT(5, 3) + 0.2)) * a, (255, 236, 210))
        a = win(WT(6, 2) - 0.3, 27.6)
        if a > 0:
            DARK.append((200, 1540, 880, 1770, a))
            d = int(1 + 20 * ease(seg(t, WT(6, 2) - 0.2, 27.2)))
            l2.text(P(540, 1610), f"DÍA {d}", font=F(M, 84), fill=sc3((240, 246, 255), a), anchor="mm")
            l2.text(P(540, 1715), "SIGUEN VIVOS: SEMANAS", font=F(B, 32), fill=sc3(GOLD, a), anchor="mm")
        note("VISTA DESDE ATRÁS · ILUSTRACIÓN", win(20.3, 27.6))
    if env == 'drain':
        a = win(28.0, 33.4)
        if a > 0:
            label("SALEN AL EYACULAR", P3(tuple(info['ure'])), (1020, 1380), "rm", a, (240, 236, 220))
            DARK.append((120, 1500, 960, 1800, a))
            n = info.get('n_ej', 0)
            l2.text(P(290, 1580), f"{n}", font=F(M, 110), fill=sc3((240, 246, 255), a), anchor="mm")
            l2.text(P(290, 1680), "EYACULACIONES", font=F(B, 26), fill=sc3(CYAN, a), anchor="mm")
            # medidor de la reserva
            lv = info.get('level', 1.0)
            x0, x1, yb = 470, 920, 1600
            l2.text(P(x0, 1545), "QUEDAN EN LA RESERVA", font=F(B, 26), fill=sc3((225, 228, 245), a), anchor="lm")
            l2.rounded_rectangle((*P(x0, yb), *P(x1, yb + 50)), radius=int(18 * S), outline=sc3((150, 160, 200), a), width=max(2, int(3 * S)))
            colb = GREEN if lv < 0.15 else (GOLD if lv < 0.5 else RED)
            l2.rounded_rectangle((*P(x0 + 6, yb + 6), *P(x0 + 6 + (x1 - x0 - 12) * lv, yb + 44)), radius=int(14 * S), fill=sc3(colb, a))
            l2.text(P(x0, 1700), f"{int(round(lv * 100))}%", font=F(M, 54), fill=sc3(colb, a), anchor="lm")
        note("≈20 A 25 EYACULACIONES · VARÍA EN CADA PERSONA", win(28.0, 33.4))
    if env == 'lab':
        a = win(33.9, 47.1)
        if a > 0:
            DARK.append((80, 1230, 420, 1520, a))
            wk = int(1 + 7 * ease(seg(t, WT(8, 2) - 0.3, WT(8, 4) + 0.4)) + 4 * ease(seg(t, WT(10, 6) - 0.2, WT(10, 9) + 0.3)))
            l2.text(P(250, 1280), "SEMANA", font=F(B, 30), fill=sc3((220, 225, 245), a), anchor="mm")
            l2.text(P(250, 1380), f"{wk}", font=F(M, 96), fill=sc3((240, 246, 255), a), anchor="mm")
            l2.text(P(250, 1470), "SE REPITE" if t > WT(10, 6) else "DESDE AQUÍ", font=F(B, 30), fill=sc3(GOLD if t > WT(10, 6) else CYAN, a * ease(seg(t, WT(8, 4), WT(8, 4) + 0.3))), anchor="mm")
            cx, cy, r = 760, 1380, 170
            DARK.append((cx - r - 20, cy - r - 20, cx + r + 20, cy + r + 60, a))
            l2.ellipse((*P(cx - r, cy - r), *P(cx + r, cy + r)), fill=sc3((26, 36, 52), a), outline=sc3((200, 220, 255), a), width=max(2, int(3 * S)))
            dens = 1 - 0.9 * ease(seg(t, WT(9, 1), WT(9, 7)))
            still = ease(seg(t, WT(9, 9), WT(9, 12)))
            # frase 10: si todavía aparecen (vuelven unos pocos que se mueven) -> se repite semanas después -> listo
            again = ease(seg(t, WT(10, 1) - 0.1, WT(10, 3))) * (1 - ease(seg(t, WT(10, 9), WT(10, 10) + 0.3)))
            dens = max(dens, 0.35 * again)
            still = still * (1 - again)
            rs = np.random.RandomState(6)
            nsp = int(26 * dens)
            for k in range(26):
                ang = rs.uniform(0, 2 * math.pi)
                rr = rs.uniform(0, r - 24)
                mv = 12 * (1 - still)
                x = cx + rr * math.cos(ang) + mv * math.sin(t * 2 + k)
                y = cy + rr * math.sin(ang) + mv * math.cos(t * 1.7 + k)
                if k < max(nsp, 2):
                    hd = 7
                    l2.ellipse((*P(x - hd, y - hd * 0.7), *P(x + hd, y + hd * 0.7)), fill=sc3((220, 236, 255), a))
                    wig = 4 * (1 - still)
                    tail = [P(x - hd - 4 * j, y + wig * math.sin(t * 9 + j + k) + (1.5 * j * still)) for j in range(8)]
                    l2.line(tail, fill=sc3((200, 220, 255), a * 0.8), width=max(1, int(2 * S)))
            ka = ease(seg(t, WT(9, 13), WT(9, 13) + 0.3)) * (1 - again) + ease(seg(t, WT(10, 10), WT(10, 10) + 0.3)) * (1 - ease(seg(t, WT(9, 13), WT(9, 13) + 0.3)))
            ka = clamp(ka)
            if ka > 0:
                check_icon(l2, cx, cy, 70, a * ka)
            txt_m = "0 MÓVILES · LISTO" if ka > 0.5 else ("AÚN HAY: SE REPITE" if again > 0.5 else "ANÁLISIS DE SEMEN")
            col_m = GREEN if ka > 0.5 else (GOLD if again > 0.5 else (220, 225, 245))
            l2.text(P(cx, cy + r + 36), txt_m, font=F(B, 28), fill=sc3(col_m, a), anchor="mm")
        pill("ANÁLISIS DESDE LA SEMANA 8", 1720, win(WT(8, 6) - 0.2, WT(9, 0)), CYAN, 800, 34)
        pill("0 O MUY POCOS Y SIN MOVERSE", 1720, win(WT(9, 4) - 0.2, WT(10, 0) - 0.1), GREEN, 820, 34)
        pill("¿AÚN HAY? SE REPITE EN UNAS SEMANAS", 1720, win(WT(10, 1) - 0.2, 47.1), GOLD, 900, 32)
        note("GUÍA AUA 2026", win(33.9, 47.1))
    if env == 'method':
        a = win(47.6, 52.1)
        if a > 0:
            DARK.append((110, 1250, 970, 1560, a))
            l2.text(P(540, 1310), "HASTA EL ANÁLISIS:", font=F(B, 36), fill=sc3((230, 235, 250), a), anchor="mm")
            l2.text(P(540, 1400), "OTRO MÉTODO", font=F(M, 76), fill=sc3(GOLD, a), anchor="mm")
            l2.text(P(540, 1500), "CONDÓN U OTRO ANTICONCEPTIVO", font=F(B, 28), fill=sc3((220, 225, 245), a), anchor="mm")
        pill("NO ESPERAR: LA FALLA MÁS COMÚN", 1660, win(WT(11, 7) - 0.2, 52.1), RED, 880, 34)
        note("EFECTIVIDAD ≈99.85% · HEALTHPARTNERS", win(47.6, 52.1))
    if env == 'end':
        pill("MÁNDASELO A QUIEN SE LA QUIERE HACER", 1560, win(52.6, T_OUT), (255, 200, 120), 900, 32)
        a = win(WT(12, 12) - 0.2, T_OUT)
        if a > 0:
            for (x0, txt, col) in ((300, "SÍ", GREEN), (780, "NO", RED)):
                DARK.append((x0 - 150, 1660, x0 + 150, 1800, a))
                l2.rounded_rectangle((*P(x0 - 130, 1675), *P(x0 + 130, 1785)), radius=int(30 * S), outline=sc3(col, a), width=max(3, int(4 * S)))
                l2.text(P(x0, 1730), txt, font=F(B, 56), fill=sc3(col, a), anchor="mm")
            l2.text(P(540, 1840), "¿SABÍAS LO DE LA ESPERA?", font=F(B, 26), fill=sc3((220, 220, 240), a), anchor="mm")
    ta = ease(seg(t, T_OUT + 0.2, T_OUT + 1.0)) * (1 - ease(seg(t, DUR - 1.0, DUR - 0.4)))
    if ta > 0:
        l2.text(P(540, 900), "Mente en órbita", font=F(B, 112), fill=sc3((240, 235, 255), ta), anchor="mm")
        ang = 2 * math.pi * (t - T_OUT) / 3.0
        ox, oy = 540 + 440 * math.cos(ang), 900 + 130 * math.sin(ang)
        l2.ellipse((*P(540 - 440, 900 - 130), *P(540 + 440, 900 + 130)), outline=sc3(VIOLET, 0.45 * ta), width=max(1, int(2 * S)))
        rr = 9 * S
        px, py = P(ox, oy)
        l2.ellipse((px - rr, py - rr, px + rr, py + rr), fill=sc3(CYAN, ta))


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "preview":
        os.makedirs("/home/claude/esp_prev", exist_ok=True)
        import time
        for ts in sys.argv[2:]:
            t0 = time.time()
            Image.fromarray(render(float(ts))).save(f"/home/claude/esp_prev/t_{ts}.png")
            print(ts, f"{time.time() - t0:.2f}s", flush=True)
    elif mode == "times":
        for i, ph in enumerate(anim.PH):
            print(i, [round(s, 2) for s in ph['starts']])
        print("T_SCAN", round(T_SCAN, 2))
    elif mode == "chunk":
        a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-vf", "scale=1080:1920:flags=lanczos", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", out]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for fr in range(a, b):
            pr.stdin.write(render(fr / FPS).tobytes())
        pr.stdin.close()
        pr.wait()
        print("ok", a, b, "de", NF)
