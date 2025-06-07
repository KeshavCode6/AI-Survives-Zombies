import gym
from stable_baselines3 import PPO
import time
from environment import ZombieEnvironment
# Load the environment
env = ZombieEnvironment(test=True)

# Load the trained model
model = PPO.load("models/rectangle")

# Run for 5 episodes
for episode in range(10):
    obs = env.reset()
    done = False
    total_reward = 0
    step = 0

    print(f"\n=== Episode {episode + 1} ===")

    while not done:
        # Predict the action using the trained model
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, done, info = env.step(action)
        total_reward += reward
        step += 1

        # Render environment (if applicable)
        if hasattr(env, 'render'):
            env.render()
            time.sleep(0.02)  # slow down for visualization

    print(
        f"Episode finished in {step} steps. Total reward: {total_reward:.2f}")

env.close()
