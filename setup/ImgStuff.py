#
# Functions to manipulate EXIF data and read/write images
# Author: Eric G. Suchanek, PhD
import os
import datetime
import matplotlib.pyplot as plt
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas as pd

import cv2
from exif import Image as EXIF_Image
from PIL import Image as PIL_Image
from PIL import ImageChops
from PIL.PngImagePlugin import PngInfo

Author = "Eric G. Suchanek, PhD"
Copyright = 'Copyright (c) 2024 ' + Author + ' All Rights Reserved'
Software = "EGS_txt2img.py"

ArtDir = os.getenv('ArtDir')
if ArtDir is None:
   print(f'No Artdir Environment defined, defaulting to .')
   ArtDir = './'

iPad_DPI = 264

def draw_images(images):
  import ipyplot

  ipyplot.plot_images(images)
  return

def plot_images(images, cols=3):
  img_cnt = len(images)
  rows = img_cnt / cols
  fig = plt.figure(figsize=(8, 12), dpi=iPad_DPI)
  for i in range(img_cnt):
      sub = fig.add_subplot(rows, cols, i+1)
      sub.imshow(images[i])
      plt.axis("off")       
  return

# save all images stored in an image array to
# individual time stamped files, indexed by their position in 
# the array. we include exif info so that we can annotate the images
# correctly as well.
def save_images(images, prmpt, prefix='stbldifXL', copyright=Copyright, 
                author=Author, software=Software, savepath='.', noisy=False):
  for i in enumerate(images):   
      fname = prefix + "_" + \
        datetime.datetime.now().strftime("%Y%m%d-%H%M%S_") +str(i) + ".jpg"
      fullname = savepath + fname

      if (noisy):
        print(f'Saving image: {fullname}')
      
      src = images[i]
      src.save(fullname)
      annotate_image(fullname, prmpt, copyright, author, software)
  return


# add the input prompt , author, copyright and generational software
# to the EXIF data for a specific image   

def annotate_png_image(fname, prmpt, copyright=Copyright, author=Author, 
                   software=Software):
  
  metadata = PngInfo()
  metadata.add_text("Copyright", copyright)
  metadata.add_text("Author", author)
  metadata.add_text("Prompt", prmpt)
  metadata.add_text("Software", software)

  targetImage = PIL_Image.open(fname)
  targetImage.save(fname, pnginfo=metadata)
  return

def annotate_image(fname, prmpt, copyright=Copyright, author=Author, 
                   software=Software):
  with open(fname, 'rb') as img_file:
    myimg = EXIF_Image(img_file)

  myimg.copyright = copyright
  myimg.artist = author
  myimg.software = Software
  myimg.user_comment = prmpt
  myimg.image_description = prmpt
  img_file.close()

  with open(fname, 'wb') as img_file2:
    img_file2.write(myimg.get_file())
  return

# list my specific exif data for a given image
def list_image_data(fname):
  file_extension = os.path.splitext(fname)[1]
  if file_extension == '.jpg':
    with open(fname, 'rb') as img_file:
      img = EXIF_Image(img_file)
    if img.has_exif:
      c = img.get('Copyright')
      a = img.get('artist')
      s = img.get('software')
      pr = img.get('image_description')
      print(f'Copyright: {c}')
      print(f'Author: {a}')
      print(f'Prompt: {pr}')
      print(f'Software: {s}')
    else:
      noExif = True
      #print(f'No new exif data in {fname}')
      img_file.close()
      img_file = PIL_Image.open(fname)
      metadata = img_file.text
      for k,v in metadata.items:
        print(f'{k}: {v}')
    return
  else:
      img_file = PIL_Image.open(fname)
      metadata = img_file.info
      for k,v in metadata.items():
        print(f'{k}: {v}')

def print_png_metadata(fname):
   img = PIL_Image.open(fname)
   print(img.text)
   return

# print all exif metadata from an individual file
def get_metadata_single(img_path):
  with open(img_path, 'rb') as img_file:
      img = EXIF_Image(img_file)
      if not img.has_exif:
          print('Image does not have EXIF metadata')
      else:
        df = pd.DataFrame(columns=['attribute', 'value'])
        attr_list = img.list_all()
        
        # Add image file name
        df = df.append({'attribute': 'image_path',
                        'value': img_path}, 
                        ignore_index=True)
        
        for attr in attr_list:
            value = img.get(attr)
            dict_i = {'attribute': attr,
                      'value': value}
            df = df.append(dict_i, ignore_index=True)
        
        df.sort_values(by='attribute', inplace=True)
        df.set_index('attribute', inplace=True)
        return df

# simply display the image using cv2
def display_image(fname):

  myimg = cv2.imread(fname) 
  cv2.cv2_imshow(myimg)
  return

def image_grid(imgs, rows, cols):
  #assert len(imgs) == rows*cols

  w = h = 512
  grid = PIL_Image.new('RGB', size=(cols*w, rows*h))
  grid_w, grid_h = grid.size
  
  for i, img in enumerate(imgs):
    src = imgs[i]
    grid.paste(src, box=(i%cols*w, i//cols*h))

  return grid
  
def save_imagelist(images, prompts, prefix='stbldif', copyright=Copyright, 
                author=Author, software=Software, savepath=ArtDir, 
                verbose=False):
  for i, imgs in enumerate(images):      
      fname = prefix + "_" + \
        datetime.datetime.now().strftime("%Y%m%d-%H%M%S_") +str(i) + ".jpg"
      fullname = savepath + fname

      if (verbose):
        print(f'Saving image: {fullname}')
    
      imgs.save(fullname)
      annotate_image(fullname, prompts[i], copyright, author, software)
  return

# produce a row x cols image from the list of images (PIL) bytes returned by the model
# return the image
def imagelist_grid(imgs, rows, cols):
  w = h = 512
  grid = PIL_Image.new('RGB', size=(cols*w, rows*h))
  grid_w, grid_h = grid.size
  
  for i, img in enumerate(imgs):
    grid.paste(imgs[i], box=(i%cols*w, i//cols*h))

  return grid

from PIL import ImageChops
from functools import reduce

import math, operator

def img_rmsdiff(im1, im2):
    "Calculate the root-mean-square difference between two images"

    h = ImageChops.difference(im1, im2).histogram()

    # calculate rms
    return math.sqrt(reduce(operator.add,
        map(lambda h, i: h*(i**2), h, range(256))
    ) / (float(im1.size[0]) * im1.size[1]))

def img_equal(im1, im2):
    return ImageChops.difference(im1, im2).getbbox() is None