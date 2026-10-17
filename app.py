import tkinter as tk
import random
import os
import json

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================

ANCHO = 1000
ALTO = 500
SUELO = 400

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imagenes")
ARCHIVO_RECORD = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "record.json"
)

VENTANA = tk.Tk()
VENTANA.title("DINO RUN")
VENTANA.resizable(False, False)

lienzo = tk.Canvas(
    VENTANA, width=ANCHO, height=ALTO,
    bg="#83d8ff", highlightthickness=0
)
lienzo.pack()

# ==========================================
# 2. CARGA SEGURA DE IMÁGENES
# ==========================================

def cargar_imagen(nombre):
    ruta = os.path.join(CARPETA, nombre)

    if not os.path.isfile(ruta):
        print(f"[AVISO] No se encontró: {ruta}")
        return None

    try:
        imagen = tk.PhotoImage(file=ruta)

        # Evita que las imágenes demasiado grandes
        # ocupen media pantalla.
        factor = max(
            1,
            (imagen.width() + 119) // 120,
            (imagen.height() + 119) // 120
        )

        if factor > 1:
            imagen = imagen.subsample(factor, factor)

        print(
            f"[OK] {nombre}: "
            f"{imagen.width()}x{imagen.height()}"
        )
        return imagen

    except tk.TclError as error:
        print(f"[ERROR] No se pudo cargar {nombre}: {error}")
        return None


def cargar_gif(nombre):
    ruta = os.path.join(CARPETA, nombre)
    fotogramas = []

    if not os.path.isfile(ruta):
        print(f"[AVISO] No se encontró: {ruta}")
        return fotogramas

    # Lee los fotogramas del GIF hasta encontrar el final.
    for indice in range(50):
        try:
            imagen = tk.PhotoImage(
                file=ruta, format=f"gif -index {indice}"
            )

            factor = max(
                1,
                (imagen.width() + 119) // 120,
                (imagen.height() + 119) // 120
            )

            if factor > 1:
                imagen = imagen.subsample(factor, factor)

            fotogramas.append(imagen)

        except tk.TclError:
            break

    if fotogramas:
        print(f"[OK] {nombre}: {len(fotogramas)} fotograma(s)")
    else:
        print(f"[ERROR] No se pudieron leer los fotogramas de {nombre}")

    return fotogramas


# Estas variables conservan las imágenes en memoria.
fotogramas_dino = cargar_gif("dinosaurio.gif")
imagen_agachado = cargar_imagen("dinosaurio_agachado.png")
imagen_cactus = cargar_imagen("cactus.png")
imagen_ave = cargar_imagen("pajaro.png")

# ==========================================
# 3. RÉCORD
# ==========================================

def cargar_record():
    try:
        with open(ARCHIVO_RECORD, "r", encoding="utf-8") as archivo:
            return int(json.load(archivo).get("record", 0))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0


def guardar_record():
    try:
        with open(ARCHIVO_RECORD, "w", encoding="utf-8") as archivo:
            json.dump({"record": record}, archivo)
    except OSError as error:
        print(f"[AVISO] No se pudo guardar el récord: {error}")


record = cargar_record()

# ==========================================
# 4. ESTADO DEL JUEGO
# ==========================================

estado = "menu"

puntuacion = 0
velocidad = 7
energia = 0
escudo = False
tiempo_escudo = 0

dino_x = 100
dino_y = SUELO - 60
velocidad_salto = 0
en_suelo = True
agachado = False
fotograma_actual = 0

obstaculos = []
cristales = []

teclas = set()
contador_obstaculos = 0
contador_cristales = 0
mensaje = ""
mensaje_tiempo = 0

# ==========================================
# 5. FONDO
# ==========================================

def dibujar_fondo():
    lienzo.delete("fondo")

    # Cielo
    lienzo.create_rectangle(
        0, 0, ANCHO, SUELO,
        fill="#83d8ff", outline="", tags="fondo"
    )

    # Sol
    lienzo.create_oval(
        820, 45, 900, 125,
        fill="#fff1a6", outline="", tags="fondo"
    )

    # Montañas lejanas
    lienzo.create_polygon(
        0, 330, 150, 190, 300, 330,
        fill="#91c9a0", outline="", tags="fondo"
    )
    lienzo.create_polygon(
        230, 330, 430, 220, 640, 330,
        fill="#a0d3a2", outline="", tags="fondo"
    )
    lienzo.create_polygon(
        570, 330, 760, 185, 970, 330,
        fill="#91c9a0", outline="", tags="fondo"
    )

    # Nubes
    for x, y in [(100, 80), (380, 120), (650, 65)]:
        lienzo.create_oval(
            x, y, x + 55, y + 25,
            fill="white", outline="", tags="fondo"
        )
        lienzo.create_oval(
            x + 20, y - 12, x + 70, y + 25,
            fill="white", outline="", tags="fondo"
        )

    # Suelo
    lienzo.create_rectangle(
        0, SUELO, ANCHO, ALTO,
        fill="#f3d49b", outline="", tags="fondo"
    )
    lienzo.create_line(
        0, SUELO, ANCHO, SUELO,
        fill="#806b42", width=4, tags="fondo"
    )

    # Piedras decorativas
    for x in range(20, ANCHO, 100):
        lienzo.create_oval(
            x, SUELO + 25, x + 13, SUELO + 30,
            fill="#c2a574", outline="", tags="fondo"
        )


# ==========================================
# 6. DINOSAURIO
# ==========================================

dino_id = None


def dibujar_dino():
    global dino_id

    if dino_id is not None:
        lienzo.delete(dino_id)

    # Agacharse solo funciona estando en el suelo.
    imagen = None

    if agachado and en_suelo and imagen_agachado:
        imagen = imagen_agachado
    elif fotogramas_dino:
        imagen = fotogramas_dino[fotograma_actual % len(fotogramas_dino)]

    if imagen:
        alto_dino = imagen.height()

        # Centra el sprite en la altura correspondiente.
        y = SUELO - alto_dino if en_suelo else dino_y
        if agachado and en_suelo:
            y = SUELO - alto_dino + 12

        dino_id = lienzo.create_image(
            dino_x, y, image=imagen, anchor="nw", tags="dino"
        )
    else:
        # Figura de respaldo si faltan las imágenes.
        if agachado and en_suelo:
            dino_id = lienzo.create_rectangle(
                dino_x, SUELO - 35,
                dino_x + 65, SUELO,
                fill="#48a83b", outline="#246d27", tags="dino"
            )
        else:
            dino_id = lienzo.create_rectangle(
                dino_x, dino_y,
                dino_x + 45, dino_y + 60,
                fill="#48a83b", outline="#246d27", tags="dino"
            )

            lienzo.create_oval(
                dino_x + 25, dino_y + 3,
                dino_x + 48, dino_y + 25,
                fill="#48a83b", outline="#246d27", tags="dino"
            )

            lienzo.create_oval(
                dino_x + 34, dino_y + 8,
                dino_x + 39, dino_y + 13,
                fill="white", outline="", tags="dino"
            )

            lienzo.create_rectangle(
                dino_x + 5, dino_y + 48,
                dino_x + 16, dino_y + 60,
                fill="#246d27", outline="", tags="dino"
            )


# ==========================================
# 7. OBSTÁCULOS Y CRISTALES
# ==========================================

def crear_obstaculo():
    tipo = random.choice(["cactus", "cactus", "ave"])

    if tipo == "cactus":
        escala = random.choice([1, 1, 2])

        if imagen_cactus:
            # Usa el sprite ya reducido por cargar_imagen.
            imagen = imagen_cactus
            objeto = lienzo.create_image(
                ANCHO, SUELO - imagen.height(),
                image=imagen, anchor="nw", tags="obstaculo"
            )
            caja = (
                ANCHO, SUELO - imagen.height(),
                ANCHO + imagen.width(), SUELO
            )
        else:
            ancho = 25 * escala
            alto = 45 * escala
            objeto = lienzo.create_rectangle(
                ANCHO, SUELO - alto, ANCHO + ancho, SUELO,
                fill="#23883a", outline="#155a29", tags="obstaculo"
            )
            caja = (ANCHO, SUELO - alto, ANCHO + ancho, SUELO)

        obstaculos.append({
            "id": objeto,
            "tipo": "cactus",
            "caja": caja
        })

    else:
        altura = random.choice([SUELO - 100, SUELO - 70, SUELO - 42])

        if imagen_ave:
            imagen = imagen_ave
            objeto = lienzo.create_image(
                ANCHO, altura - imagen.height() // 2,
                image=imagen, anchor="nw", tags="obstaculo"
            )
            caja = (
                ANCHO, altura - imagen.height() // 2,
                ANCHO + imagen.width(), altura + imagen.height() // 2
            )
        else:
            objeto = lienzo.create_oval(
                ANCHO, altura, ANCHO + 45, altura + 25,
                fill="#454b58", outline="", tags="obstaculo"
            )
            caja = (ANCHO, altura, ANCHO + 45, altura + 25)

        obstaculos.append({
            "id": objeto,
            "tipo": "ave",
            "caja": caja
        })


def crear_cristal():
    y = random.choice([SUELO - 55, SUELO - 100, SUELO - 145])

    objeto = lienzo.create_polygon(
        ANCHO, y - 12,
        ANCHO + 10, y,
        ANCHO, y + 12,
        ANCHO - 10, y,
        fill="#21e6ed", outline="#087dba", width=2,
        tags="cristal"
    )

    cristales.append({"id": objeto})


# ==========================================
# 8. INTERFAZ
# ==========================================

def dibujar_texto():
    lienzo.delete("interfaz")

    lienzo.create_text(
        20, 20, anchor="nw",
        text=f"Puntos: {int(puntuacion)}",
        font=("Arial", 17, "bold"),
        fill="#18364a", tags="interfaz"
    )

    lienzo.create_text(
        20, 48, anchor="nw",
        text=f"Récord: {record}",
        font=("Arial", 12, "bold"),
        fill="#18364a", tags="interfaz"
    )

    # Barra de energía
    lienzo.create_text(
        ANCHO - 225, 20, anchor="nw",
        text=f"Energía: {energia}/5",
        font=("Arial", 13, "bold"),
        fill="#18364a", tags="interfaz"
    )

    lienzo.create_rectangle(
        ANCHO - 225, 45, ANCHO - 25, 62,
        outline="#18364a", width=2, tags="interfaz"
    )

    lienzo.create_rectangle(
        ANCHO - 222, 48,
        ANCHO - 222 + energia * 39, 59,
        fill="#20dce8", outline="", tags="interfaz"
    )

    if escudo:
        lienzo.create_text(
            ANCHO // 2, 30, text="ESCUDO ACTIVO",
            font=("Arial", 16, "bold"),
            fill="#087dba", tags="interfaz"
        )

    if mensaje_tiempo > 0:
        lienzo.create_text(
            ANCHO // 2, 80, text=mensaje,
            font=("Arial", 15, "bold"),
            fill="#18364a", tags="interfaz"
        )


def mostrar_menu():
    lienzo.delete("all")
    dibujar_fondo()

    lienzo.create_text(
        ANCHO // 2, 145,
        text="DINO RUN",
        font=("Arial", 44, "bold"),
        fill="#174d32"
    )

    lienzo.create_text(
        ANCHO // 2, 205,
        text="¡Corre, esquiva y recoge cristales!",
        font=("Arial", 17),
        fill="#18364a"
    )

    lienzo.create_text(
        ANCHO // 2, 270,
        text="ESPACIO: saltar     ↓: agacharse",
        font=("Arial", 14),
        fill="#18364a"
    )

    lienzo.create_text(
        ANCHO // 2, 300,
        text="← →: moverte     E: escudo     P: pausa",
        font=("Arial", 14),
        fill="#18364a"
    )

    lienzo.create_text(
        ANCHO // 2, 355,
        text="Pulsa ENTER para comenzar",
        font=("Arial", 20, "bold"),
        fill="#174d32"
    )


def mostrar_game_over():
    lienzo.create_rectangle(
        250, 145, 750, 335,
        fill="#fff8e8", outline="#18364a", width=3,
        tags="interfaz"
    )

    lienzo.create_text(
        ANCHO // 2, 185,
        text="¡FIN DE LA PARTIDA!",
        font=("Arial", 26, "bold"),
        fill="#b42e2e", tags="interfaz"
    )

    lienzo.create_text(
        ANCHO // 2, 230,
        text=f"Puntuación: {int(puntuacion)}",
        font=("Arial", 18),
        fill="#18364a", tags="interfaz"
    )

    lienzo.create_text(
        ANCHO // 2, 280,
        text="ENTER: volver a jugar   |   ESC: menú",
        font=("Arial", 14, "bold"),
        fill="#18364a", tags="interfaz"
    )


# ==========================================
# 9. INICIAR Y REINICIAR
# ==========================================

def iniciar_juego():
    global estado, puntuacion, velocidad, energia
    global escudo, tiempo_escudo, dino_x, dino_y
    global velocidad_salto, en_suelo, agachado
    global obstaculos, cristales, contador_obstaculos
    global contador_cristales, mensaje_tiempo, fotograma_actual

    estado = "jugando"
    puntuacion = 0
    velocidad = 7
    energia = 0
    escudo = False
    tiempo_escudo = 0

    dino_x = 100
    dino_y = SUELO - 60
    velocidad_salto = 0
    en_suelo = True
    agachado = False
    fotograma_actual = 0

    for objeto in obstaculos:
        lienzo.delete(objeto["id"])
    for cristal in cristales:
        lienzo.delete(cristal["id"])

    obstaculos = []
    cristales = []
    contador_obstaculos = 0
    contador_cristales = 0
    mensaje_tiempo = 0

    lienzo.delete("all")
    dibujar_fondo()
    dibujar_dino()
    dibujar_texto()


def volver_menu():
    global estado
    estado = "menu"
    mostrar_menu()


# ==========================================
# 10. CONTROLES
# ==========================================

def tecla_presionada(evento):
    global velocidad_salto, en_suelo, agachado
    global escudo, energia, mensaje, mensaje_tiempo

    tecla = evento.keysym.lower()
    teclas.add(tecla)

    if tecla == "escape":
        volver_menu()
        return

    if estado == "menu" and tecla in ("return", "kp_enter"):
        iniciar_juego()
        return

    if estado == "fin" and tecla in ("return", "kp_enter"):
        iniciar_juego()
        return

    if estado == "jugando":
        if tecla in ("space", "up", "w") and en_suelo:
            velocidad_salto = -16
            en_suelo = False
            agachado = False

        elif tecla in ("down", "s"):
            if en_suelo:
                agachado = True

        elif tecla == "p":
            pausar_juego()

        elif tecla == "e":
            if energia >= 5 and not escudo:
                energia = 0
                escudo = True
                tiempo_escudo = 90
                mensaje = "¡ESCUDO ACTIVADO!"
                mensaje_tiempo = 60


def tecla_soltada(evento):
    global agachado
    teclas.discard(evento.keysym.lower())

    if evento.keysym.lower() in ("down", "s"):
        agachado = False


def pausar_juego():
    global estado

    if estado == "jugando":
        estado = "pausa"
        lienzo.create_rectangle(
            300, 170, 700, 300,
            fill="#fff8e8", outline="#18364a", width=3,
            tags="interfaz"
        )
        lienzo.create_text(
            ANCHO // 2, 215, text="PAUSA",
            font=("Arial", 30, "bold"),
            fill="#18364a", tags="interfaz"
        )
        lienzo.create_text(
            ANCHO // 2, 260, text="Pulsa P para continuar",
            font=("Arial", 15),
            fill="#18364a", tags="interfaz"
        )

    elif estado == "pausa":
        estado = "jugando"


VENTANA.bind("<KeyPress>", tecla_presionada)
VENTANA.bind("<KeyRelease>", tecla_soltada)

# ==========================================
# 11. COLISIONES
# ==========================================

def hay_colision(caja1, caja2):
    if not caja1 or not caja2:
        return False

    margen = 9

    x1, y1, x2, y2 = caja1
    a1, b1, a2, b2 = caja2

    # Se reducen las cajas para evitar choques injustos
    # con los bordes transparentes de los sprites.
    return (
        x1 + margen < a2 - margen
        and x2 - margen > a1 + margen
        and y1 + margen < b2 - margen
        and y2 - margen > b1 + margen
    )


# ==========================================
# 12. BUCLE PRINCIPAL
# ==========================================

def actualizar():
    global puntuacion, velocidad, energia, escudo
    global tiempo_escudo, dino_x, dino_y
    global velocidad_salto, en_suelo, fotograma_actual
    global contador_obstaculos, contador_cristales
    global estado, record, mensaje_tiempo

    try:
        if estado == "jugando":
            puntuacion += 0.15
            velocidad = min(15, 7 + puntuacion / 250)

            # Movimiento lateral
            if "left" in teclas or "a" in teclas:
                dino_x = max(0, dino_x - 5)
            if "right" in teclas or "d" in teclas:
                dino_x = min(ANCHO - 70, dino_x + 5)

            # Salto con gravedad
            if not en_suelo:
                velocidad_salto += 0.8
                dino_y += velocidad_salto

                if dino_y >= SUELO - 60:
                    dino_y = SUELO - 60
                    velocidad_salto = 0
                    en_suelo = True

            fotograma_actual += 1

            # Crear obstáculos con intervalos variables
            contador_obstaculos += 1
            if contador_obstaculos >= random.randint(42, 68):
                crear_obstaculo()
                contador_obstaculos = 0

            # Crear cristales
            contador_cristales += 1
            if contador_cristales >= 100:
                crear_cristal()
                contador_cristales = 0

            # Actualizar obstáculos y eliminar los que salieron
            for obstaculo in obstaculos[:]:
                objeto = obstaculo["id"]
                lienzo.move(objeto, -velocidad, 0)

                caja = lienzo.bbox(objeto)

                if caja and caja[2] < 0:
                    lienzo.delete(objeto)
                    obstaculos.remove(obstaculo)
                    continue

                caja_dino = lienzo.bbox(dino_id)
                if caja and caja_dino and hay_colision(caja_dino, caja):
                    if escudo:
                        lienzo.delete(objeto)
                        obstaculos.remove(obstaculo)
                        mensaje = "¡El escudo te salvó!"
                        mensaje_tiempo = 35
                    else:
                        estado = "fin"
                        break

            # Actualizar cristales y recogerlos
            for cristal in cristales[:]:
                objeto = cristal["id"]
                lienzo.move(objeto, -velocidad, 0)
                caja = lienzo.bbox(objeto)

                if caja and caja[2] < 0:
                    lienzo.delete(objeto)
                    cristales.remove(cristal)
                    continue

                caja_dino = lienzo.bbox(dino_id)
                if caja and caja_dino and hay_colision(caja_dino, caja):
                    energia = min(5, energia + 1)
                    puntuacion += 25
                    lienzo.delete(objeto)
                    cristales.remove(cristal)
                    mensaje = "+25 puntos"
                    mensaje_tiempo = 25

            # Duración del escudo
            if escudo:
                tiempo_escudo -= 1
                if tiempo_escudo <= 0:
                    escudo = False
                    mensaje = "Escudo terminado"
                    mensaje_tiempo = 30

            if mensaje_tiempo > 0:
                mensaje_tiempo -= 1

            if int(puntuacion) > record:
                record = int(puntuacion)
                guardar_record()

            # Redibujar personaje e interfaz
            dibujar_dino()
            dibujar_texto()

            if estado == "fin":
                mostrar_game_over()

        elif estado == "fin":
            # Mantiene la pantalla final sin seguir jugando.
            pass

    except Exception as error:
        print("[ERROR EN EL JUEGO]", repr(error))
        estado = "fin"
        mostrar_game_over()

    # El bucle siempre se programa de nuevo.
    VENTANA.after(30, actualizar)


# ==========================================
# 13. ARRANQUE
# ==========================================

mostrar_menu()
actualizar()
VENTANA.mainloop()
