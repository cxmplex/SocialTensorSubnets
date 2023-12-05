import requests
import time
import bittensor as bt
from sd_net.validators.utils.uids import get_random_uids
from sd_net.protocol import ImageGenerating, pil_image_to_base64
from template.base.validator import BaseValidatorNeuron
import random
import torch

class Validator(BaseValidatorNeuron):
    def __init__(self, config=None):
        super(Validator, self).__init__(config=config)

        bt.logging.info("load_state()")
        self.load_state()
        # TODO(developer): Anything specific to your use case you can do here
    def get_prompt(self, seed: int) -> str:

        url = 'http://localhost:8001/prompt_generate'

        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
        }

        data = {
            "prompt": "an image of",
            "seed": seed,
            "max_length": 77,
            "additional_params": {}
        }

        response = requests.post(url, headers=headers, json=data)
        prompt = response.json()['prompt']
        return prompt

    def get_reward(self, miner_response: ImageGenerating, prompt: str, seed: int, additional_params: dict = {}):
        url = "http://localhost:8000/verify"
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
        }
        miner_images = miner_response.images
        data = {
            "prompt": prompt,
            "seed": seed,
            "images": miner_images,
            "additional_params": additional_params
        }
        response = requests.post(url, headers=headers, json=data)
        reward = response.json()['reward']
        return reward

    async def forward(self):
        """
        Validator forward pass. Consists of:
        - Generating the query
        - Querying the miners
        - Getting the responses
        - Rewarding the miners
        - Updating the scores
        """
        seed = random.randint(0, 1000)
        prompt = self.get_prompt(seed)
        print(prompt)
        miner_uids = get_random_uids(self, k=self.config.neuron.sample_size)
        responses = self.dendrite.query(
            axons=[self.metagraph.axons[uid] for uid in miner_uids],
            synapse=ImageGenerating(prompt=prompt, seed=seed),
            deserialize=False,
        )
        # bt.logging.info(f"Received responses: {responses}")

        rewards = [self.get_reward(response, prompt, seed) for response in responses]
        rewards = torch.FloatTensor(rewards)
        #TODO: call api for verify & get reward
        bt.logging.info(f"Scored responses: {rewards}")
        self.update_scores(rewards, miner_uids)


# The main function parses the configuration and runs the validator.
if __name__ == "__main__":
    with Validator() as validator:
        while True:
            bt.logging.info("Validator running...", time.time())
            time.sleep(5)
