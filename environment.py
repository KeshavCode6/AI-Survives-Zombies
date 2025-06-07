import gym
from gym import spaces
import pygame
import random
import numpy as np
from constants import SIZE, WIDTH, HEIGHT, PLAYER_SPEED, ZOMBIE_SPEED, MAX_STEPS
from characters import BaseZombie, DasherZombie, Player, WandererZombie

pygame.init()
pygame.display.init()


class ZombieEnvironment(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self, test=False):
        super(ZombieEnvironment, self).__init__()
        self.test = test

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.zombies = [WandererZombie(), BaseZombie(),
                        DasherZombie()]
        self.player = Player()

        obs_len = 3 + 2 * len(self.zombies)
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(obs_len,), dtype=np.float32)
        self.action_space = spaces.Discrete(4)

    def get_neighbors(self, zombie, radius=50):
        neighbors = []
        for other in self.zombies:
            if other is zombie:
                continue
            dx = other.rect.centerx - zombie.rect.centerx
            dy = other.rect.centery - zombie.rect.centery
            dist = (dx ** 2 + dy ** 2) ** 0.5
            if dist < radius:
                neighbors.append(other)
        return neighbors

    def render(self, mode='human'):
        pygame.event.pump()

        self.screen.fill((30, 30, 30))
        self.player.render(self.screen)
        for z in self.zombies:
            z.render(self.screen)

        pygame.display.flip()
        self.clock.tick(60)

    def reset(self):
        self.player.moveTo(WIDTH // 2, HEIGHT // 2)
        self.player.health = 100  # start with full health, better for training
        self.corner_time = 0
        self.steps = 0

        for i in range(len(self.zombies)):
            while True:
                x = random.randint(0, WIDTH - SIZE)
                y = random.randint(0, HEIGHT - SIZE)
                dist = ((x - self.player.rect.x) ** 2 +
                        (y - self.player.rect.y) ** 2) ** 0.5
                if dist >= 100:
                    self.zombies[i].moveTo(x, y)
                    self.zombies[i].last_attack_step = - \
                        self.zombies[i].cooldown_steps
                    break

        return self._get_obs()

    def step(self, action):
        done = False
        old_health = self.player.health
        reward = 1.0
        old_x, old_y = self.player.rect.x, self.player.rect.y

        # Player movement
        if action == 0:
            self.player.move(0, PLAYER_SPEED)
        elif action == 1:
            self.player.move(0, -PLAYER_SPEED)
        elif action == 2:
            self.player.move(-PLAYER_SPEED, 0)
        elif action == 3:
            self.player.move(PLAYER_SPEED, 0)

        # Clamp player inside screen
        self.player.rect.x = max(0, min(self.player.rect.x, WIDTH - SIZE))
        self.player.rect.y = max(0, min(self.player.rect.y, HEIGHT - SIZE))

        movement_distance = ((self.player.rect.x - old_x) ** 2 +
                             (self.player.rect.y - old_y) ** 2) ** 0.5

        # Detect proximity to edge
        dist_left = self.player.rect.x
        dist_right = WIDTH - (self.player.rect.x + SIZE)
        dist_top = self.player.rect.y
        dist_bottom = HEIGHT - (self.player.rect.y + SIZE)
        min_dist_to_edge = min(dist_left, dist_right, dist_top, dist_bottom)
        near_edge = min_dist_to_edge < WIDTH * 0.1

        if movement_distance < 7 and near_edge:
            self.corner_time += 1
            edge_penalty = (1 - (min_dist_to_edge / (WIDTH * 0.1)))
            penalty_scale = min(self.corner_time / 100, 1.0)
            reward -= edge_penalty * (2 + penalty_scale * 8)
        else:
            self.corner_time = 0

        for z in self.zombies:
            if isinstance(z, WandererZombie):
                z.Wander(self.player)
            else:
                # BaseZombie just chases the player
                target_x = self.player.rect.centerx
                target_y = self.player.rect.centery
                dx = target_x - z.rect.centerx
                dy = target_y - z.rect.centery

                neighbors = self.get_neighbors(z)
                sep_x, sep_y = 0, 0
                for other in neighbors:
                    offset_x = z.rect.centerx - other.rect.centerx
                    offset_y = z.rect.centery - other.rect.centery
                    distance = max((offset_x**2 + offset_y**2) ** 0.5, 0.1)
                    sep_x += offset_x / distance
                    sep_y += offset_y / distance

                if neighbors:
                    sep_x /= len(neighbors)
                    sep_y /= len(neighbors)

                move_x = dx + sep_x * 25
                move_y = dy + sep_y * 25

                mag = max((move_x**2 + move_y**2) ** 0.5, 1)
                z.move(int(ZOMBIE_SPEED * move_x / mag),
                       int(ZOMBIE_SPEED * move_y / mag))

                if isinstance(z, DasherZombie):
                    z.dash((self.player.rect.centerx, self.player.rect.centery))

            z.attack(self.player, self.steps)
            # Keep zombies inside bounds
            z.rect.x = max(0, min(z.rect.x, WIDTH - SIZE))
            z.rect.y = max(0, min(z.rect.y, HEIGHT - SIZE))

        # Health change impact
        health_change = self.player.health - old_health
        reward += health_change * 0.5

        self.steps += 1
        done = self.player.health <= 0 or (
            not self.test and self.steps >= MAX_STEPS)

        return self._get_obs(), reward, done, {}

    def _get_obs(self):
        # Normalize health to [0,1]
        obs = [self.player.rect.x / WIDTH,
               self.player.rect.y / HEIGHT,
               self.player.health / 100]
        for z in self.zombies:
            obs += [z.rect.x / WIDTH, z.rect.y / HEIGHT]
        return np.array(obs, dtype=np.float32)
