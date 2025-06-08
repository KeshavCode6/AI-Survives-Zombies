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
                        BaseZombie(), DasherZombie()]
        self.player = Player()

        num_dashers = sum(isinstance(z, DasherZombie) for z in self.zombies)
        obs_len = 3 + 2 * len(self.zombies) + num_dashers

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
        self.player.reset()
        self.corner_time = 0
        self.steps = 0

        for z in self.zombies:
            z.reset(self.player)

        return self._get_obs()

    def step(self, action):
        done = False
        old_health = self.player.health
        reward = 1.0
        old_x, old_y = self.player.rect.x, self.player.rect.y

        # Player handles movement + clamping
        self.player.update(action)

        movement_distance = ((self.player.rect.x - old_x) ** 2 +
                             (self.player.rect.y - old_y) ** 2) ** 0.5

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

        # Update zombies
        for z in self.zombies:
            z.update(self.player, self.zombies, self.steps)

        # Distance-based reward from zombies
        total_distance = 0
        for z in self.zombies:
            dx = self.player.rect.centerx - z.rect.centerx
            dy = self.player.rect.centery - z.rect.centery
            dist = (dx ** 2 + dy ** 2) ** 0.5
            total_distance += dist

        avg_distance = total_distance / len(self.zombies)
        safe_distance_reward = min(
            avg_distance / 100, 1.0)  # Scale and cap at 1.0
        reward += safe_distance_reward * 0.5  # Tweak scaling factor as needed

        health_change = self.player.health - old_health
        reward += health_change * 0.5

        self.steps += 1
        done = self.player.health <= 0 or (
            not self.test and self.steps >= MAX_STEPS)

        return self._get_obs(), reward, done, {}

    def _get_obs(self):
        obs = [self.player.rect.x / WIDTH,
               self.player.rect.y / HEIGHT,
               self.player.health / 100]
        for z in self.zombies:
            obs += [z.rect.x / WIDTH, z.rect.y / HEIGHT]

        for z in self.zombies:
            if isinstance(z, DasherZombie):
                obs += [z.cooldown]
        return np.array(obs, dtype=np.float32)
