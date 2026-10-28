---
name: empaquetador
description: Revisa y optimiza juntos el título y la miniatura (y la portada del reel) para que se complementen sin repetir la misma información, genera la miniatura en 3D con motor3d y la califica. Úsala antes de publicar cualquier video largo o cuando Efrén pida título o miniatura.
---
# Empaquetador

## Regla de oro
Título y miniatura son **una sola promesa en dos partes**: la miniatura enseña la emoción o el objeto (≤ 4 palabras), el título da el contexto que falta. Si dicen lo mismo, se desperdicia uno de los dos.

## Pasos
1. Escribe 5 títulos (≤ 60 caracteres, palabra clave al inicio, una brecha de curiosidad, número si aplica) y 3 conceptos de miniatura (objeto 3D principal + texto ≤ 4 palabras + contraste).
2. Matriz título × miniatura: descarta pares que repitan palabras o la misma idea. Ejemplo bueno: miniatura "13 AÑOS de espera." + título "¿Por qué GTA 6 tardó tanto? Las 5 razones".
3. Créditos: solo en videos largos y si `vidiq_balance` ≥ 40, califica los 2 mejores títulos con `vidiq_score_title` (`type='long'`, 5 créditos c/u). En Shorts y reels decide con la rúbrica sin gastar.
4. Miniatura 1280×720 con el motor (plantilla `kit/thumb_gta.py`): mismo tema visual del video, objeto 3D grande a un lado, texto gigante del otro, máximo 3 colores fuertes, legible en tamaño de celular (revísala reducida a 320 px). Imágenes oficiales solo si suman (portadas, key art) y con permiso de prensa.
5. Si el video ya está en YouTube y el canal conectado, `vidiq_score_thumbnail` (5 créditos) solo si hay presupuesto.
6. Entrega: título elegido + 2 alternativas, miniatura en `guiones/AAAA-MM-DD_tema_miniatura.jpg` y la portada del reel (cuadro del gancho).
