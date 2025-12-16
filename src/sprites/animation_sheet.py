import pygame as pg

class AnimationSheet:
    def __init__(self, path, frame_width, frame_height, num_frames):
        self.path = path
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.frame_count = num_frames

        sheet = pg.image.load(path).convert_alpha()
        self.frames = []

        for i in range(num_frames):
            rect = pg.Rect(i * frame_width, 0, frame_width, frame_height)
            frame = sheet.subsurface(rect)
            self.frames.append(frame)

        self.index = 0
        self.timer = 0
        self.speed = 0.08   # seconds per frame

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.speed:
            self.timer = 0
            self.index = (self.index + 1) % len(self.frames)

    def draw(self, screen, x, y, scale=2, flip=False):
        frame = self.frames[self.index]
        if flip:
            frame = pg.transform.flip(frame, True, False)
        frame = pg.transform.scale(frame, (frame.get_width()*scale, frame.get_height()*scale))
        screen.blit(frame, (x, y))

    def clone(self):
        return AnimationSheet(self.path, self.frame_width, self.frame_height, self.frame_count)