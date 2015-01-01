# encoding: utf-8
# Created by Liza Daly <lizadaly@gmail.com>
#
# This work is in the public domain http://creativecommons.org/publicdomain/zero/1.0/
# Libraries used by this work may be commercial or have other copyright restrictions.

import logging

logging.basicConfig(level=logging.INFO)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.propagate = False
requests_log = logging.getLogger("flickrapi.core")
requests_log.propagate = False

from PIL import Image, ImageChops, ImageOps
from StringIO import StringIO

import colorsys
import flickrapi
import os.path, os
import random
import requests
from glob import glob

from secret import FLICKR_KEY, FLICKR_SECRET
from duchamp import BUILD_DIR

IA_METADATA_URL = 'https://archive.org/metadata/{}'

FLICKR_USER_ID = '126377022@N07'  # The Internet Archive's Flickr ID
MAX_PHOTOS_PER_SECTION = 20
MIN_LIGHTNESS = 200  # Minimize lightness value of the image's primary (background color)
MIN_SIZE = 300  # Minimum length or width of the image, in pixels

class BookImage(object):
    def __init__(self, url, width, height, primary_color, src):
        self.url = url
        self.width = width
        self.height = height
        self.primary_color = primary_color
        self.src = src

def flickr_search(text, tags='bookdecade1920'):
    '''Request images from the IA Flickr account with the given century tags and the related text'''
    book_images = []

    flickr = flickrapi.FlickrAPI(FLICKR_KEY, FLICKR_SECRET, format='etree', cache=True)
    photos = flickr.walk(user_id=FLICKR_USER_ID,
                         per_page=100,
                         text=text,
                         tag_mode='any',
                         tags=tags,
                         extras='url_o',
                         sort='relevance-desc')

    count = 0
    last_image = None
    
    # Randomize the result set
    for index, photo in enumerate(photos):
        # Ensure that images are the correct minimize size
        if int(photo.get('height_o')) < MIN_SIZE or int(photo.get('width_o') < MIN_SIZE):
            continue

        if index % 2 == 0:  # Only grab odd ones
            last_image = photo.get('url_o')
            continue
        if not last_image:
            continue
        
        img1_url = photo.get('url_o')
        img1_file = requests.get(img1_url, stream=True)
        img1_file.raw.decode_content = True
        im = Image.open(StringIO(img1_file.raw.read()))

        img2_url = last_image
        img2_file = requests.get(img2_url, stream=True)
        img2_file.raw.decode_content = True
        im2 = Image.open(StringIO(img2_file.raw.read()))
        
        img_filename = "{}.png".format(photo.get('id'))
        img_dir = os.path.join(BUILD_DIR, img_filename)

        if not os.path.exists(BUILD_DIR):
            os.makedirs(BUILD_DIR)


        
        # Main colors
        try:
            d = im.getcolors(im.size[0] * im.size[1])
            # Image 1 should be a photograph
            if len(d) < 20000:
                continue
            colors1 = max(d)[1] 
            hls1 = colorsys.rgb_to_hls(colors1[0], colors1[1], colors1[2])
            lightness1 = int(hls1[1])

            colors2 = max(im2.getcolors(im2.size[0] * im2.size[1]))[1]  # 2nd value in the tuple is the RGB color set
            hls2 = colorsys.rgb_to_hls(colors2[0], colors2[1], colors2[2])
            lightness2 = int(hls2[1])
        except:
            continue
        
        #print "lightness 1: {}".format(lightness1)
        #print "lightness 2: {}".format(lightness2)
        #print img_filename
        im.save(img_dir)

        print im.size
        print im2.size        
        # Fit the smaller to the larger
        if im.size[0] + im.size[1] > im2.size[0] + im2.size[1]:
            print "Fitting 2 to 1"
            im2 = ImageOps.fit(im2, im.size)
        else:
            print "Fitting 1 to 2"
            im = ImageOps.fit(im, im2.size)

        print im.size
        print im2.size
        # composite the corresponding image from the first set
        if lightness1 == lightness2:
            im = ImageChops.blend(im, im2, 1)
            img_dir = os.path.join(BUILD_DIR, 'blend-' + img_filename)
        elif lightness1 > lightness2:
            im = ImageChops.subtract(im, im2)
            #im = ImageChops.screen(im, im2)
            #im = ImageOps.solarize(im, 50)            
            im = ImageOps.grayscale(im)
            img_dir = os.path.join(BUILD_DIR, 'screen-' + img_filename)            
        else:
            im = ImageChops.multiply(im, im2)
            img_dir = os.path.join(BUILD_DIR, 'multiply-' + img_filename)

#        im = ImageOps.grayscale(im)
        im = ImageOps.autocontrast(im)
        im.save(img_dir)

        src = 'https://www.flickr.com/photos/{}/{}'.format(photo.get('owner'), photo.get('id'))
        book_images.append(BookImage(url=img_filename,
                                     width=im.size[0],
                                     height=im.size[1],
                                     primary_color=None,
                                     src=src))

        
        count += 1
        if count > MAX_PHOTOS_PER_SECTION:
            break

    if count < MAX_PHOTOS_PER_SECTION:
        logging.warn("Did not get enough images for section {}: only {}".format(text, count))

    return book_images

if __name__ == '__main__':
    # Delete previous generated output file
    files = glob(os.path.join(BUILD_DIR, '*'))
    for f in files:
        os.unlink(f)
        
    flickr_search(('anger', 'man', 'sex', 'music', 'photograph'))
