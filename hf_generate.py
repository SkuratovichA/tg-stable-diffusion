import os
from PIL import Image
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
parser.add_argument('--model-path', type=str, default='models/stable_diffusion_pipe', help="Path to model")
parser.add_argument('--model-id', type=str, default='CompVis/stable-diffusion-v1-4', help="Model id")
parser.add_argument('--query_id', type=str, default='no-id', help="Query id")
parser.add_argument('--queries_dir', type=str, default='queries', help="Queires directory")
parser.add_argument('--images_dir', type=str, default='images', help="Image directory")
parser.add_argument('-n', '--num_images', type=int, default=1, help="Number of images to generate")
parser.add_argument('-d', '--image_dims', nargs=2, default=[512, 512], help='Image dimensions')
parser.add_argument('--make_grid', action="store_true", help='Set to make pictures join together')
parser.add_argument('--grid_dims', nargs=2, default=[0, 0], help='Cols and rows of grid')
parser.add_argument('-s', '--num_inference_steps', type=int, default=15, help="Number of inference steps")


def get_prompt(prompt_dir, query_id):
    prompt_txt_path = os.path.join(prompt_dir, f'{query_id}.txt')
    logger.info(f'Text prompt .txt path: {prompt_txt_path}')
    with open(prompt_txt_path) as f:
        prompt = f.read()
    logger.info(f'Got text prompt: {prompt}')
    return prompt


def generate_and_save_image(
        prompt: list, 
        images_dir: str, 
        query_id: str,
        image_dims: list,
        make_grid: bool, 
        grid_dims: list,
        num_inference_steps: int,
        pipe: StableDiffusionPipeline):

    logger.info(f'Generating {"a grid image" if make_grid else "an image" if len(prompt) == 1 else "images"}...')  # we utilise a bit of bad code practices
    with autocast("cuda"):
        images = pipe(prompt, height=image_dims[1], width=image_dims[0], guidance_scale=7.5, num_inference_steps=num_inference_steps)["sample"]
    # grid 
    if make_grid is True:
        grid_path = f'{query_id}.png'
        width, height, rows, cols = images[0].size, grid_dims
        grid = Image.new('RGB', size=(rows*width, cols*height))
        for i, image in enumerate(images):
            grid.paste(image, box=(i%cols*width, i//cols*height))
        grid.save(os.path.join(images_dir, grid_path))
        return
    # no grid
    for id, image in enumerate(images):
        image_path = f'{query_id}_{id}.png'
        logger.info(f'Image will be saved to: {image_path}')
        image.save(os.path.join(images_dir, image_path))


def main():
    args = parser.parse_args()
    logger.info(f'Provided arguments:\n{args}')

    if train_type == 'online CPU':
        pipe = StableDiffusionPipeline.from_pretrained(args.model_id, use_auth_token=True)
        pipe.save_pretrained(args.model_path)
        logger.info(f'Pipeline saved to {args.model_path}. Exiting...')
        return

    pipe = StableDiffusionPipeline.from_pretrained(args.model_path, use_auth_token=False).to(device)

    prompt = [get_prompt(args.queries_dir, args.query_id)] * args.num_images
    generate_and_save_image(prompt, args.images_dir, args.query_id, args.image_dims, args.make_grid, args.grid_dims, args.num_inference_steps, pipe)  


if __name__ == "__main__":
    # TODO: 
    # to parse args here, thereby making them global?
    main()
