#!/usr/bin/env python

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import pygame as pg
import os
import logging

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
        #super().__init__()
        pg.sprite.Sprite.__init__(self)
        logging.info ("Button %s x=%d y=%d width=%d height=%d" % (text, x, y, width, height))
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
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.image = self.image_down
                self.button_down = True
        elif event.type == pg.MOUSEBUTTONUP:
            # If the rect collides with the mouse pos.
            if self.rect.collidepoint(event.pos) and self.button_down:
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

        s_layout = data.get('layout', 'h')
        buttons = data.get('buttons', [])

        starts = [0]
        if s_layout.startswith('v'):
            interval = self.height / float(len(buttons))
        else:
            interval = self.width / float(len(buttons))
        for i in range(0, len(buttons)):
            start = int ((i+1)*interval)
            starts.append(start)
        logging.info ("starts = %s", starts)

        FONT = pg.font.SysFont('Comic Sans MS', 32)
        IMAGE_NORMAL = pg.Surface((100, 32))
        IMAGE_NORMAL.fill(pg.Color('dodgerblue1'))
        IMAGE_HOVER = pg.Surface((100, 32))
        IMAGE_HOVER.fill(pg.Color('lightskyblue'))
        IMAGE_DOWN = pg.Surface((100, 32))
        IMAGE_DOWN.fill(pg.Color('aquamarine1'))

        for i in range(0, len(buttons)):
            button = buttons[i]
            if s_layout.startswith('v'):
                x = 0
                w = self.width
                y = starts[i]
                h = starts[i+1] - starts[i]
            else:
                x = starts[i]
                w = starts[i+1] - starts[i]
                y = 0
                h = self.height

            pg_button = Button(
                x, y, w, h, self.button_clicked,
                FONT, button.get('text', 'unknown text'), (255, 255, 255),
                IMAGE_NORMAL, IMAGE_HOVER, IMAGE_DOWN, callback_arg=button)
            self.all_sprites.add(pg_button)

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
        logging.info ('button clicked = %s', str(a))
        print a.get('cmd', a.get('text', str(a)))
        self.done = True

    def run(self):
        while not self.done:
            self.dt = self.clock.tick(30) / 1000
            self.handle_events()
            self.run_logic()
            self.draw()

    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.done = True
            for button in self.all_sprites:
                button.handle_event(event)

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
    parser.add_argument("-v", "--verbosity", type=int, help="increase output verbosity")
                
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
