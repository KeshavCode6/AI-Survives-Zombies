import numpy as np
import pygame
import numpy as np
from constants import SIZE, ZOMBIE_SPEED, WIDTH, HEIGHT
import random


class Object:
    def __init__(self, x, y, sprite):
        self.rect = pygame.Rect(x, y, SIZE, SIZE)

        # Load and resize the default image
        default_img = pygame.image.load(
            f"assets/{sprite}/default.png").convert_alpha()
        self.default = pygame.transform.scale(default_img, (SIZE, SIZE))

        self.walking = []
        for i in range(2):
            img = pygame.image.load(
                f"assets/{sprite}/run_{i}.png").convert_alpha()
            resized_img = pygame.transform.scale(img, (SIZE, SIZE))
            self.walking.append(resized_img)

        self.isWalking = False
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 100

        self.x_vel = 0
        self.y_vel = 0

    def render(self, screen: pygame.Surface):
        now = pygame.time.get_ticks()

        if self.x_vel != 0 or self.y_vel != 0:
            if now - self.animation_timer > self.animation_speed:
                self.animation_timer = now
                self.current_frame = (
                    self.current_frame + 1) % len(self.walking)

            screen.blit(self.walking[self.current_frame], self.rect)
        else:
            # Not moving: show default frame and reset animation
            self.current_frame = 0
            self.animation_timer = now
            screen.blit(self.default, self.rect)

    def move(self, x_vel, y_vel):
        self.x_vel = x_vel
        self.y_vel = y_vel
        self.rect.x += x_vel
        self.rect.y += y_vel

    def moveTo(self, x, y):
        self.rect.x = x
        self.rect.y = y
        self.x_vel = 0
        self.y_vel = 0


class Player(Object):
    def __init__(self, x=0, y=0):
        super().__init__(x, y, "Timmy")
        self.health = 100

    def reset(self):
        self.moveTo(WIDTH // 2, HEIGHT // 2)
        self.health = 100


class BaseZombie(Object):
    def __init__(self, x=0, y=0):
        super().__init__(x, y, "Zombie")
        self.health = 100
        self.cooldown_steps = 30
        self.last_attack_step = -self.cooldown_steps

    def attack(self, player, current_step):
        # Check if cooldown is over
        if current_step - self.last_attack_step >= self.cooldown_steps:
            if self.rect.colliderect(player.rect):
                damage = 10  # Damage dealt per attack (adjust as needed)
                player.health = max(player.health - damage, 0)
                self.last_attack_step = current_step

    def reset(self, player):
        while True:
            x = random.randint(0, WIDTH - SIZE)
            y = random.randint(0, HEIGHT - SIZE)
            dist = ((x - player.rect.x) ** 2 +
                    (y - player.rect.y) ** 2) ** 0.5
            if dist >= 100:
                self.moveTo(x, y)
                self.last_attack_step = - \
                    self.cooldown_steps
                break


class WandererZombie(BaseZombie):
    def __init__(self, x=0, y=0):
        super().__init__(x, y)
        self.move_timer = 0
        self.direction = (0, 0)
        self.steps_in_direction = 0
        self.wander_speed = ZOMBIE_SPEED

    def Wander(self, player):
        if self.move_timer == 0 or self.steps_in_direction <= 0:
            if random.random() < 0.4:
                # Calculate direction vector towards player
                dx = player.rect.centerx - self.rect.centerx
                dy = player.rect.centery - self.rect.centery
                dx = 0 if dx == 0 else int(dx / abs(dx))
                dy = 0 if dy == 0 else int(dy / abs(dy))
                self.direction = (dx, dy)
                self.steps_in_direction = random.randint(5, 25)
            else:
                self.direction = (random.choice([-1, 0, 1]),
                                  random.choice([-1, 0, 1]))
                while self.direction == (0, 0):
                    self.direction = (random.choice([-1, 0, 1]),
                                      random.choice([-1, 0, 1]))
                self.steps_in_direction = random.randint(5, 25)

            self.wander_speed = random.uniform(
                ZOMBIE_SPEED-2, ZOMBIE_SPEED + 2)
            self.move_timer = self.steps_in_direction

        dx, dy = self.direction
        self.move(dx * self.wander_speed,
                  dy * self.wander_speed)

        self.steps_in_direction -= 1
        self.move_timer -= 1


class DasherZombie(BaseZombie):
    def __init__(self, x=0, y=0):
        super().__init__(x, y)
        self.cooldown = 0
        self.MAX_COOLDOWN = 75

    def dash(self, timmy_pos):
        tim_x, tim_y = timmy_pos
        z_x, z_y = self.rect.x, self.rect.y

        if self.cooldown == 0:
            direction = np.sign([tim_x - z_x, tim_y - z_y])
            new_x = z_x + 2 * direction[0] * SIZE
            new_y = z_y + 2 * direction[1] * SIZE
            self.moveTo(new_x, new_y)
            self.cooldown = self.MAX_COOLDOWN
        else:
            self.cooldown -= 1
