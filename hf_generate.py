import os
import torch
import logging
import argparse
from torch import autocast
from diffusers import StableDiffusionPipeline

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s %(message)s', '%H:%M'
))
logger.addHandler(handler)

try:
    from safe_gpu import safe_gpu
    gpuOwner = safe_gpu.GPUOwner(1)
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['HF_DATASETS_OFFLINE'] = '1'
    os.environ['WANDB_MODE'] = 'offline'
    device = "cuda"
    train_type = 'offline GPU'
    logger.info('GPU is enabled. Here we go computing')
except Exception as e:
    device = 'This fails because stable diffusion requires GPU. Hence, model will only be downloaded'
    logger.info(e)
    train_type = 'online CPU'
    logger.info('A model will be downloaded')


parser = argparse.ArgumentParser()
parser.add_argument('--model-path', type=str, default='models/stable_diffusion_pipe')
parser.add_argument('--model-id', type=str, default='CompVis/stable-diffusion-v1-4')

parser.add_argument('--querry_id', type=str, default='no-id')
parser.add_argument('--querries_dir', type=str, default='querries')
parser.add_argument('--images_dir', type=str, default='images')


def get_prompt(prompt_dir, querry_id):
    prompt_txt_path = os.path.join(prompt_dir, f'{querry_id}.txt')
    logger.info(f'Text prompt .txt path: {prompt_txt_path}')
    with open(prompt_txt_path) as f:
        prompt = f.read()
    logger.info(f'Got text prompt: {prompt}')
    return prompt


def generate_and_save_image(prompt, images_dir, querry_id, pipe):
    logger.info('Generating an image...')
    with autocast("cuda"):
        image = pipe(prompt, guidance_scale=7.5)["sample"][0]

    image_path = f'{querry_id}.png'
    logger.info(f'Image will be saved to: {image_path}')
    image.save(os.path.join(images_dir, image_path))


def main():
    args = parser.parse_args()
    logger.info(f'Provided arguments:\n{args}')


    if train_type == 'online CPU':
        pipe = StableDiffusionPipeline.from_pretrained(args.model_id, use_auth_token=True)
        pipe.save_pretrained(args.model_path)
        logger.info(f'Pipeline saved to {path}. Exiting...')
        return

    pipe = StableDiffusionPipeline.from_pretrained(args.model_path, use_auth_token=False).to(device)

    prompt = get_prompt(args.querries_dir, args.querry_id)
    generate_and_save_image(prompt, args.images_dir, args.querry_id, pipe)


if __name__ == "__main__":
    main()
