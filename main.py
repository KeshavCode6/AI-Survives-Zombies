from stable_baselines3 import PPO
import pygame
from environment import ZombieEnvironment
from constants import total_timesteps, eval_interval, episodes_per_eval

train = False

env = ZombieEnvironment(train)
model = None
if train:
    model = PPO("MlpPolicy", env, verbose=1, device="cuda")
else:
    model = PPO.load("models/rectangle")


def runEpisodes(number):
    for episode in range(number):
        obs = env.reset()
        done = False
        total_reward = 0
        while not done:
            action, _states = model.predict(obs)
            obs, reward, done, info = env.step(action)
            env.render()
            total_reward += reward
        print(
            f"Episode {episode + 1} finished with avg reward: {total_reward/number:.2f}")


if train:
    timesteps_trained = 0
    while timesteps_trained < total_timesteps:
        next_timesteps = min(
            eval_interval, total_timesteps - timesteps_trained)

        if train:
            model.learn(total_timesteps=next_timesteps,
                        reset_num_timesteps=False)

        timesteps_trained += next_timesteps
        pygame.event.pump()

        print(f"\n--- Evaluation after {timesteps_trained} timesteps ---")
        runEpisodes(episodes_per_eval)
        model.save(f"timmy_ppo_model_{timesteps_trained}")
else:
    runEpisodes(5)

env.close()
