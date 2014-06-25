import spyral
import spyral.debug
import pygame
from random import randint, random


def reset():
    scene = spyral.director.get_scene()
    for sprite in scene._sprites.copy():
        sprite.kill()
    scene.background.fill((255,255,255))

def fps():
    scene = spyral.director.get_scene()
    scene.fps = spyral.debug.FPSSprite(scene, (255,0,0))


class RetroTexto(spyral.Sprite):
    def __init__(self, texto):
        scene = spyral.director.get_scene()
        spyral.Sprite.__init__(self, scene)
        self.image = spyral.Image("images/minivintage-frame.png")

        font_path = "fonts/LiberationSans-Regular.ttf"
        self.font = spyral.Font(font_path, 24, (0,0,0))
        self.line_height = self.font.linesize

        self.image.draw_image(self.render_text(texto), 
                                position=(0, 0),
                                anchor="midleft")

    def render_text(self, text):
        text_width = self.font.get_size(text)[0]

        ancho_promedio = self.font.get_size("X")[0]
        caracteres = self.width / ancho_promedio
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
        self.vel = 100 
        self.scale = 3
        self.x, self.y = 100, 100
        self.anchor = "midbottom"

        self.estado = "quieto"
        self.movimiento = spyral.Vec2D(0, 0)

        spyral.event.register("director.render", self.seguir_raton, scene=scene)
        spyral.event.register("director.pre_render", self.determinar_estado, scene=scene)

    def determinar_estado(self):
        if abs(self.movimiento.x) < 5 and abs(self.movimiento.y) < 5:
            self.estado = "quieto"
        else:
            self.estado = "corre_"
            if self.movimiento.y > 0:
                self.estado += "s"
            else:
                self.estado += "n"

            if self.movimiento.x > 0:
                self.estado += "e"
            else:
                self.estado += "o"

    def seguir_raton(self):
        self.stop_all_animations()
        pos = self.scene.activity._pygamecanvas.get_pointer()
        self.movimiento = pos - self.pos
        anim = spyral.Animation("pos", spyral.easing.LinearTuple(self.pos, pos), duration = 0.5)
        self.animate(anim)

class Perro(spyral.Sprite):
    def __init__(self, scene):
        spyral.Sprite.__init__(self, scene)
        self.image = spyral.Image(filename="images/perro.png")

class Mono(spyral.Sprite):
    def __init__(self, scene):
        spyral.Sprite.__init__(self, scene)
        #self.scene = scene
        self.image = spyral.Image(filename="images/monkey_normal.png")
        self.grito = pygame.mixer.Sound("sounds/smile.wav")
        self.x = 100
        self.y = 300

    def sonreir(self):
        self.image = spyral.Image(filename="images/monkey_smile.png")
        self.scene.redraw()
        self.grito.play()
        #self.image = spyral.Image(filename="images/monkey_normal.png")
        

class Juego(spyral.Scene):
    def __init__(self, activity=None, *args, **kwargs):
        spyral.Scene.__init__(self, SIZE)
        self.background = spyral.Image(size=SIZE).fill((255,255,255))
        
        spyral.event.register("system.quit", spyral.director.pop)

        if activity:
            activity.box.next_page()
            activity._pygamecanvas.grab_focus()
            activity.window.set_cursor(None)
            self.activity = activity
