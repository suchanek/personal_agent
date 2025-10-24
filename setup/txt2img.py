#
# Use stability AI stable diffusion for text-> image generation
# Author: Eric G. Suchanek, PhD
# Last modification: 2025-10-15 18:45:14 -egs-


import argparse
import datetime
import os
import time

from diffusers import DiffusionPipeline
from tqdm import tqdm

from ImgStuff import annotate_image, annotate_png_image

ArtDir = os.getenv("ArtDir")
if ArtDir is None:
    # print(f"No Artdir Environment defined, defaulting to /tmp/")
    ArtDir = "/tmp/"

Software = f"{__file__}"
Author = "Eric G. Suchanek, PhD"
Copyright = "Copyright (c) 2025 " + Author + " All Rights Reserved"

_turbo = "stabilityai/sdxl-turbo"
_XL = "stabilityai/stable-diffusion-xl-base-1.0"


#
def make_art(prmpt, steps=20, scale=7, imgs=1):
    global pipe
    results = pipe(
        prmpt,
        num_inference_steps=steps,
        guidance_scale=scale,
        autocast=False,
        num_images_per_prompt=imgs,
    )
    return results


def save_image(
    img,
    prmpt,
    prefix="stbldif",
    copyright=Copyright,
    author=Author,
    software=Software,
    savepath=ArtDir,
    noisy=True,
    steps=20,
    scale=10,
):
    from datetime import datetime

    prfx = f"{savepath}{prefix}/"

    if not os.path.exists(prfx):
        os.makedirs(prfx)

    fname_png = (
        f'{prefix}_t{steps}_g{scale}_{datetime.now().strftime("%Y%m%d-%H%M%S")}.png'
    )
    fname_jpg = (
        f'{prefix}_t{steps}_g{scale}_{datetime.now().strftime("%Y%m%d-%H%M%S")}.jpg'
    )
    fullname_png = prfx + fname_png
    fullname_jpg = prfx + fname_jpg

    if noisy:
        print(f"Saving image: {fullname_png}")

    img.save(fullname_png)
    annotate_png_image(fullname_png, prmpt, copyright, author, software)
    fullname_img = fullname_png

    if noisy:
        print(f"Saving image: {fullname_jpg}")

    img.save(fullname_jpg)
    annotate_image(fullname_jpg, prmpt, copyright, author, software)
    fullname_img = fullname_jpg

    return fullname_img


DaliPrompt = "A beautiful sculpture symbolizing the eternal flame of hope in the style of dali, magical lighting, stars and moon in background "

negative_prompt = " remove bad hands, arms, remove bad eyes, remove extra limbs, remove bad eyes, impossible gemetry"
style = " surreal"

start = time.time()

parser = argparse.ArgumentParser()

parser.add_argument(
    "-p",
    "--prompt",
    help="Input text prompt for image generation",
    type=str,
    required=False,
    default=DaliPrompt,
)
parser.add_argument(
    "-m",
    "--model",
    help="Model to use. Big or turbo",
    type=str,
    required=False,
    default="XL",
)
parser.add_argument(
    "-n", "--n_images", help="Number of images", type=int, required=False, default=1
)
parser.add_argument(
    "-s",
    "--steps",
    help="Number of iteration steps",
    type=int,
    required=False,
    default=30,
)
parser.add_argument(
    "-g",
    "--cfg",
    help="Guidance (keep between 1 & 12)",
    type=int,
    required=False,
    default=11,
)
parser.add_argument(
    "-x",
    "--prefix",
    help="Prefix for image creation",
    type=str,
    required=False,
    default="egs_stblDiff",
)
parser.add_argument(
    "--noisy",
    help="Enable verbose output",
    action="store_true",
    default=False,
)

args = parser.parse_args()

global pipe


def main(args):
    import torch

    global pipe

    prompt = args.prompt + negative_prompt
    number = args.n_images
    steps = args.steps
    scale = args.cfg
    prefix = args.prefix
    mdlStr = args.model
    noisy = args.noisy

    if mdlStr == "XL":
        model = _XL
    else:
        model = _turbo

    pipe = DiffusionPipeline.from_pretrained(model).to("mps")

    res = make_art(prompt, steps=steps, scale=scale, imgs=1)
    imga = res.images[0]
    output_filename = save_image(
        imga, prompt, prefix=prefix, steps=steps, scale=scale, noisy=noisy
    )

    end = time.time()
    elapsed = end - start

    if noisy:
        print(
            f"{__file__} --> Image Generation Complete!\nElapsed time: {datetime.timedelta(seconds=elapsed)} (h:m:s)"
        )

    #!/usr/bin/env python3
    import base64
    import sys

    with open(output_filename, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    print("data:image/png;base64," + encoded)


if __name__ == "__main__":
    main(args)

# End of file
