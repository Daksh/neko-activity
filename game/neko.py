# -*- coding: utf-8 -*-

import spyral
import spyral.debug
import pygame
from random import randint, random
import math

splash_done = False

def cargar_frases():
    archivo = open("frases_miau.txt", "r")
    frases = archivo.read().decode("utf-8").splitlines()
    return frases
sabiduria = cargar_frases()

class RetroTexto(spyral.Sprite):
    count = 0

    def __init__(self):
        scene = spyral.director.get_scene()
        spyral.Sprite.__init__(self, scene)
        self.image = spyral.Image("images/minivintage-frame.png")
        self.layer = "fondo"

        font_path = "fonts/new-century-schoolbook-bi-1361846783.ttf"
        self.font = spyral.Font(font_path, 28, (0,0,0))
        self.line_height = self.font.linesize
        self.margen = 50

        self.miau = pygame.mixer.Sound("sounds/sonido_miau.wav")
        self.miau.play()

        texto = sabiduria[self.count]

        self.image.draw_image(self.render_text(texto), 
                                position=(0, 0),
                                anchor="midleft")

        anim_aparecer = spyral.Animation("scale", spyral.easing.Linear(0.1, 1), duration=0.5)
        self.animate(anim_aparecer)

        RetroTexto.count += 1
        if self.count == len(sabiduria):
            RetroTexto.count = 2

    def render_text(self, text):
        text_width = self.font.get_size(text)[0]

        ancho_promedio = self.font.get_size("X")[0]
        caracteres = (self.width - 2 * self.margen) / ancho_promedio
        lineas = self.wrap(text, caracteres).splitlines()

        altura = len(lineas) * self.line_height
        bloque = spyral.Image(size=(self.width, altura))

        ln = 0
        for linea in lineas:
            bloque.draw_image(image=self.font.render(linea),
                                position=(0, ln * self.line_height),
                                anchor="midtop")
            ln = ln + 1
        return bloque
       

    def wrap(self, text, length):
        """ Sirve para cortar texto en varias lineas """
        words = text.split()
        lines = []
        line = ''
        for w in words:
            if len(w) + len(line) > length:
                lines.append(line)
                line = ''
            line = line + w + ' '
            if w is words[-1]: lines.append(line)
        return '\n'.join(lines)

class Gato(spyral.Sprite):
    def __init__(self, scene):
        spyral.Sprite.__init__(self, scene)
        self.image = spyral.Image("images/mati2.png")
        self.layer = "fondo"

        self.scale = 2
        self.pos = spyral.Vec2D(self.scene.size) / 2
        self.anchor = "midbottom"
        self.velocidad = 100.0 * self.scale.x

        self.pensamiento = None # Empezamos sin pensar

        self.animando = False
        self.moviendo = False
        self.cajita = spyral.Rect(self.width/2.0, self.height,
                             self.scene.width - self.width,
                             self.scene.height - self.height)

        self.estado = "despertando"

        # posicion del mouse inicial
        self.pos_mouse_anterior = self.scene.canvas.get_pointer()

        spyral.event.register("director.update", self.actualizar)#, scene=scene)
        spyral.event.register("Gato.image.animation.end", self.fin_animacion)#, scene=scene)
        spyral.event.register("Gato.pos.animation.end", self.fin_movimiento)#, scene=scene)

    def calcular_puntero(self):
        pos_mouse = spyral.Vec2D(self.scene.canvas.get_pointer())
        distancia_al_mouse = pos_mouse.distance(self.pos)

        if distancia_al_mouse > 6:
            linea_al_mouse = (pos_mouse - self.pos)
            angulo = math.degrees(linea_al_mouse.get_angle())
            if angulo < 0:
                angulo = angulo + 360

            if 22.5 <= angulo < 67.5:
                estado = "corre_se"
            elif 67.5 <= angulo < 112.5:
                estado = "corre_s"
            elif 112.5 <= angulo < 157.5:
                estado = "corre_so"
            elif 157.5 <= angulo < 202.5:
                estado = "corre_o"
            elif 202.5 <= angulo < 247.5:
                estado = "corre_no"
            elif 247.5 <= angulo < 292.5:
                estado = "corre_n"
            elif 292.5 <= angulo < 337.5:
                estado = "corre_ne"
            elif 337.5 <= angulo or angulo < 22.5:
                estado = "corre_e"

            if not self.moviendo and not self.cajita.collide_point(pos_mouse):
                estado = estado.replace("corre", "rasca")

            return estado

    def actualizar(self, delta):
        pos_mouse = spyral.Vec2D(self.scene.canvas.get_pointer())
        movimiento_del_mouse = pos_mouse.distance(self.pos_mouse_anterior)

        nuevo_estado = self.calcular_puntero() or "quieto"
        if movimiento_del_mouse > 7:
            # posibilidades:
            #  - no se está ni moviendo ni animando -> animar y mover
            #  - se está moviendo y animando -> cambiar dirección solo si se necesita
            #  - no se está moviendo pero sí animando -> esperar

            if self.estado in ["dormido", "quieto"]:
                self.animar("despertando")
            else:
                if not (self.estado=="despertando") and not self.estado.startswith("rasca"):
                    self.mover(pos_mouse)

            if self.estado.startswith("corre") and not self.animando:
                if nuevo_estado.startswith("rasca"):
                    self.animar(nuevo_estado)

            if not self.animando or (self.estado is not nuevo_estado):
                if self.estado!="despertando":
                    if not(self.estado.startswith("rasca") and nuevo_estado.startswith("rasca")):
                        self.animar(nuevo_estado)

            if self.pensamiento:
                self.pensamiento.kill()
        else:
            # posibilidades:
            #  - no se está moviendo -> llegamos!
            #  - se está moviendo -> esperar hasta llegar! 

            if not self.moviendo:
                if self.animando:
                    if self.estado.startswith("corre"):
                        self.stop_animation(self.anim)
                        self.pensamiento = RetroTexto()
                        self.pensamiento.pos = self.pos
                        if (self.y + self.pensamiento.image.height) > self.scene.height:
                            self.pensamiento.anchor = "bottomleft"
                        if (self.x + self.pensamiento.image.width) > self.scene.width:
                            if self.y - self.pensamiento.image.height < 0:
                                self.pensamiento.anchor = "topright"
                            else:
                                self.pensamiento.anchor = "bottomright"
                else:
                    if self.estado=="quieto":
                        self.animar("dormido")
                        if self.pensamiento:
                            self.pensamiento.kill()
                    elif self.estado=="despertando":
                        self.mover(pos_mouse)
                        nuevo_estado = nuevo_estado.replace("rasca", "corre")
                        self.animar(nuevo_estado)
                    else:
                        self.animar("quieto")

        self.pos_mouse_anterior = pos_mouse

    def mover(self, pos_nueva):
        if self.moviendo:
            self.stop_animation(self.anim_mov)

        # aseguremonos de movernos solo en la cajita
        if pos_nueva.x < self.cajita.left:
            pos_nueva.x = self.cajita.left
        if pos_nueva.x > self.cajita.right:
            pos_nueva.x = self.cajita.right
        if pos_nueva.y < self.cajita.top:
            pos_nueva.y = self.cajita.top
        if pos_nueva.y > self.cajita.bottom:
            pos_nueva.y = self.cajita.bottom

        distancia = self.pos.distance(pos_nueva)
        tiempo = distancia / self.velocidad
        if tiempo > 0:
            self.anim_mov = spyral.Animation("pos", 
                                     spyral.easing.LinearTuple(self.pos, pos_nueva),
                                     duration = tiempo)
            self.animate(self.anim_mov)
            self.moviendo = True

    def animar(self, estado):
        estado_anterior = self.estado
        if self.animando:
            self.stop_animation(self.anim)

        seg_por_paso = 0.4
        if estado == "quieto":
            secuencia = [spyral.Image("images/mati2.png")] * 7 + \
                        [spyral.Image("images/jare2.png"),
                         spyral.Image("images/mati2.png")] * 9 + \
                        [spyral.Image("images/kaki1.png"),
                         spyral.Image("images/kaki2.png")] * 3 + \
                        [spyral.Image("images/mati3.png")] * 7
            duracion = 7 
            repetir = False
        elif estado == "dormido":
            secuencia = [spyral.Image("images/sleep1.png"), 
                         spyral.Image("images/sleep2.png")]
            duracion = 1.5
            repetir = True
        elif estado == "despertando":
            secuencia = [spyral.Image("images/awake.png")] 
            duracion = 0.8
            repetir = False
        elif estado == "corre_e":
            secuencia = [spyral.Image("images/right1.png"), 
                         spyral.Image("images/right2.png")]
            duracion = seg_por_paso
            repetir = True
        elif estado == "corre_ne":
            secuencia = [spyral.Image("images/upright1.png"), 
                         spyral.Image("images/upright2.png")]
            duracion = seg_por_paso
            repetir = True
        elif estado == "corre_n":
            secuencia = [spyral.Image("images/up1.png"), 
                         spyral.Image("images/up2.png")]
            duracion = seg_por_paso
            repetir = True
        elif estado == "corre_no":
            secuencia = [spyral.Image("images/upleft1.png"), 
                         spyral.Image("images/upleft2.png")]
            duracion = seg_por_paso
            repetir = True
        elif estado == "corre_o":
            secuencia = [spyral.Image("images/left1.png"), 
                         spyral.Image("images/left2.png")]
            duracion = seg_por_paso
            repetir = True
        elif estado == "corre_so":
            secuencia = [spyral.Image("images/dwleft1.png"), 
                         spyral.Image("images/dwleft2.png")]
            duracion = seg_por_paso
            repetir = True
        elif estado == "corre_s":
            secuencia = [spyral.Image("images/down1.png"), 
                         spyral.Image("images/down2.png")]
            duracion = seg_por_paso
            repetir = True
        elif estado == "corre_se":
            secuencia = [spyral.Image("images/dwright1.png"), 
                         spyral.Image("images/dwright2.png")]
            duracion = seg_por_paso
            repetir = True
        elif estado.startswith("rasca_n"):
            secuencia = [spyral.Image("images/utogi1.png"), 
                         spyral.Image("images/utogi2.png")] * 8
            duracion = seg_por_paso * 4
            repetir = False
        elif estado.startswith("rasca_s"):
            secuencia = [spyral.Image("images/dtogi1.png"), 
                         spyral.Image("images/dtogi2.png")] * 8
            duracion = seg_por_paso * 4
            repetir = False
        elif estado == "rasca_e":
            secuencia = [spyral.Image("images/rtogi1.png"), 
                         spyral.Image("images/rtogi2.png")] * 8
            duracion = seg_por_paso * 4
            repetir = False
        elif estado == "rasca_o":
            secuencia = [spyral.Image("images/ltogi1.png"), 
                         spyral.Image("images/ltogi2.png")] * 8
            duracion = seg_por_paso * 4
            repetir = False
        else:
            return

        self.estado = estado
        self.anim = spyral.Animation("image", spyral.easing.Iterate(secuencia), 
                                duration=duracion, loop=repetir)

        self.animate(self.anim)
        self.animando = True

    def real_rect(self):
        return spyral.Rect(self.rect.left - self.width/2.0,
                           self.rect.top - self.height,
                           self.width, self.height)

    def fin_animacion(self, sprite):
        if sprite==self:
            self.animando = False

    def fin_movimiento(self, sprite):
        if sprite==self:
            self.moviendo = False


class Juego(spyral.Scene):
    def __init__(self, activity=None, callback=None, *args, **kwargs):
        spyral.Scene.__init__(self)
        self.background = spyral.Image(size=self.size).fill((255,255,255))
        self.layers = ["fondo", "frente"]

        if activity:
            self.activity = activity
            self.canvas = activity._pygamecanvas
        
        self.neko = Gato(self)

        spyral.event.register("system.quit", spyral.director.pop)

        self.taller = spyral.Sprite(self)
        self.taller.layer = "frente"
        self.taller.image = spyral.Image(filename="images/logo_labs.png")
        self.taller.pos = (self.width - self.taller.width, self.height-30)
        self.taller.scale = 1.3
        self.taller.anchor = "midbottom"

        self.taller2 = spyral.Sprite(self)
        self.taller2.layer = "frente"
        self.taller2.image = spyral.Image(filename="images/transformando.png")
        self.taller2.pos = (self.taller2.width/2, self.height-self.taller.image.height)
        self.taller2.anchor = "center"

        spyral.event.register("director.scene.enter", self.blink)

        # le avisamos a la actividad que terminamos de cargar el juego
        if callback:
            callback()

    def blink(self):
        global splash_done
        if not splash_done:
            delay = spyral.DelayAnimation(5)
            moveout = spyral.Animation("y", spyral.easing.Linear(self.taller.y, self.height
                                                                    + self.taller.height), duration=4)
            self.taller.animate(delay + moveout)
            moveout = spyral.Animation("y", spyral.easing.Linear(self.taller2.y, self.height 
                                                                    + self.taller.height/2), duration=5)
            self.taller2.animate(delay+moveout)
            splash_done = True

