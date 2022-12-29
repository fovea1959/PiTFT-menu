#!/usr/bin/env python3

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os
import logging

# https://stackoverflow.com/a/54247065
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame as pg

def factors(n):    
    return [(i, n//i) for i in range(1, int(n**0.5) + 1) if n % i == 0]

def rgb (s):
    if s.startswith('#'):
        # from John1024's answer in https://stackoverflow.com/questions/29643352/converting-hex-to-rgb-value-in-python
        rv = tuple(int(s.lstrip('#')[i:i+2], 16) for i in (0, 2 ,4))
    else:
        rv = pg.Color(s)

    logging.debug ('Converted %s to %s', s, rv)
    return rv

# Button is a sprite subclass, that means it can be added to a sprite group.
# You can draw and update all sprites in a group by
# calling `group.update()` and `group.draw(screen)`.
class Button(pg.sprite.Sprite):

    def __init__(self, x, y, width, height, callback,
                 font=None, text='', text_color=(0, 0, 0),
                 image_normal=None, image_hover=None,
                 image_down=None,
                 callback_arg=None,
                 ):
        super().__init__()
        logging.info ("Button %s x=%d y=%d width=%d height=%d" % (text, x, y, width, height))
        self.text = text
        # Scale the images to the desired size (doesn't modify the originals).
        self.image_normal = pg.transform.scale(image_normal, (width, height))
        self.image_hover = pg.transform.scale(image_hover, (width, height))
        self.image_down = pg.transform.scale(image_down, (width, height))

        self.image = self.image_normal  # The currently active image.
        self.rect = self.image.get_rect(topleft=(x, y))
        # To center the text rect.
        image_center = self.image.get_rect().center
        text_surf = font.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=image_center)
        # Blit the text onto the images.
        for image in (self.image_normal, self.image_hover, self.image_down):
            image.blit(text_surf, text_rect)

        # This function will be called when the button gets pressed.
        self.callback = callback
        self.callback_arg = callback_arg
        self.button_down = False

    def handle_event(self, event):
        logging.info ("%s got event, type=%s, pos=%s", self.text, event.type, event.pos)
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                logging.info ("%s button down", self.text)
                self.image = self.image_down
                self.button_down = True
        elif event.type == pg.MOUSEBUTTONUP:
            # If the rect collides with the mouse pos.
            if self.rect.collidepoint(event.pos) and self.button_down:
                logging.info ("%s button up", self.text)
                self.callback(self.callback_arg)  # Call the function.
                self.image = self.image_hover
            self.button_down = False
        elif event.type == pg.MOUSEMOTION:
            collided = self.rect.collidepoint(event.pos)
            if collided and not self.button_down:
                self.image = self.image_hover
            elif not collided:
                self.image = self.image_normal

class Game:

    def __init__(self, data):
        self.get_screen()
        self.done = False
        self.clock = pg.time.Clock()
        # Contains all sprites. Also put the button sprites into a
        # separate group in your own game.
        self.all_sprites = pg.sprite.Group()
        self.number = 0
        pg.mouse.set_visible(False)

        buttons = data.get('buttons', [])
        n_buttons = len(buttons)

        s_layout = data.get('layout', '2d')
        if s_layout.startswith('v'):
            n_rows = n_buttons
            n_columns = 1
        elif s_layout.startswith('h'):
            n_rows = 1
            n_columns = n_buttons
        else:
            # 2d layout
            f = factors(n_buttons)
            if len(f) == 1 and n_button > 4:
                f = factors(n_buttons+1)
            (n_rows, n_columns) = f[-1]

        x_starts = [0]
        y_starts = [0]
        x_interval = self.width // n_columns
        y_interval = self.height // n_rows
        for i in range(0, n_columns):
            start = int ((i+1)*x_interval)
            x_starts.append(start)
        for i in range(0, n_rows):
            start = int ((i+1)*y_interval)
            y_starts.append(start)

        FONT = pg.font.SysFont('Comic Sans MS', 32)

        for i in range(0, len(buttons)):
            button = buttons[i]
            x_index = i % n_columns
            y_index = i // n_columns
            x = x_starts[x_index]
            w = x_starts[x_index+1] - x
            y = y_starts[y_index]
            h = y_starts[y_index+1] - y

            image_normal = self.makesurface (button, data, 'normal', 'dodgerblue1')
            image_hover = self.makesurface (button, data, 'hover', 'lightskyblue')
            image_down = self.makesurface (button, data, 'down', 'aquamarine')

            pg_button = Button(
                x, y, w, h, self.button_clicked,
                FONT, button.get('text', 'unknown text'), (255, 255, 255),
                image_normal, image_hover, image_down, callback_arg=button)
            self.all_sprites.add(pg_button)

    def makesurface (self, button, data, whichstate, defaultcolor):
        color = defaultcolor
        style_name = button.get('style', None)
        if style_name is not None:
            style = data.get('styles', {}).get(style_name,None)
            if style is not None:
                state = style.get(whichstate, None)
                if state is None:
                    logging.warn ('cannot find state "%s" in style %s for button %s', whichstate, style, button)
                else:
                    color = state.get('color', None)
                    if color is None:
                        logging.warn ('cannot find "color" in state %s for style %s for button %s', state, style, button)
                        color = defaultcolor
            else:
                logging.warn ('cannot find style %s for button %s', style_name, button)
        rv = pg.Surface((100, 32))
        rv.fill(rgb(color))
        return rv

    def get_screen(self):
        "Ininitializes a new pygame screen using the framebuffer"
        # Based on "Python GUI in Linux frame buffer"
        # http://www.karoltomala.com/blog/?p=679
        disp_no = os.getenv("DISPLAY")
        if disp_no:
            logging.info("I'm running under X display = {0}".format(disp_no))
            pg.display.init()
        else:
            # Check which frame buffer drivers are available
            # Start with fbcon since directfb hangs with composite output
            drivers = ['fbcon', 'directfb', 'svgalib']
            found = False
            for driver in drivers:
                # Make sure that SDL_VIDEODRIVER is set
                if not os.getenv('SDL_VIDEODRIVER'):
                    os.putenv('SDL_VIDEODRIVER', driver)
                try:
                    pg.display.init()
                    logging.info ('Driver: %s worked.', driver)
                    found = True
                    break
                except pg.error:
                    logging.info ('Driver: %s failed.', driver)
        
            if not found:
                raise Exception('No suitable video driver found!')
        
        size = (pg.display.Info().current_w, pg.display.Info().current_h)
        self.width = size[0]
        self.height = size[1]
        logging.info ('Framebuffer size: %d x %d', size[0], size[1])
        self.screen = pg.display.set_mode(size, pg.FULLSCREEN)

        if False:
            # Clear the screen to start
            self.screen.fill((0, 0, 0))        
            # Initialise font support
            pg.font.init()
            # Render the screen
            pg.display.update()

    def button_clicked(self, a):
        if not self.done:
            logging.info ('button clicked = %s', str(a))
            print(a.get('cmd', a.get('text', str(a))))
            self.done = True

    def run(self):
        while not self.done:
            self.dt = self.clock.tick(30) / 1000
            self.handle_events()
            self.run_logic()
            self.draw()

    def handle_events(self):
        got_some = False
        for event in pg.event.get():
            got_some = True
            if event.type == pg.QUIT:
                self.done = True
            for button in self.all_sprites:
                button.handle_event(event)
        if got_some:
            logging.info ('==== end of event batch ====')

    def run_logic(self):
        self.all_sprites.update(self.dt)

    def draw(self):
        self.screen.fill((30, 30, 30))
        self.all_sprites.draw(self.screen)
        pg.display.flip()


def main():

    import json
    import argparse
    from pprint import pformat

    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="input file")
    parser.add_argument("-v", "--verbosity", default=0, action="count", help="increase output verbosity")
                
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO if args.verbosity < 1 else logging.DEBUG)

    import json

    with open(args.input) as f:
        data = json.load(f)
        logging.info ("data = %s", data)

    os.putenv('SDL_FBDEV', '/dev/fb1')
    os.putenv('SDL_MOUSEDRV', 'TSLIB')
    os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')
    pg.init()
    Game(data).run()
    pg.quit()

if __name__ == '__main__':
    main()
