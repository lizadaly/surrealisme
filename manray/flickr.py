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

from pprint import pprint
from PIL import Image, ImageChops, ImageOps, ImageStat, ImageFilter
import math
from StringIO import StringIO
import numpy as np
import colorsys
import flickrapi
import os.path, os
import random
import requests
from glob import glob
import cv2
import pickle
import xml.etree.ElementTree as etree

from secret import FLICKR_KEY, FLICKR_SECRET
from duchamp import BUILD_DIR, CASCADE_FILE, CACHE_DIR

IA_METADATA_URL = 'https://archive.org/metadata/{}'

FLICKR_USER_ID = '126377022@N07'  # The Internet Archive's Flickr ID
MAX_PHOTOS_PER_SECTION = 20
MIN_LIGHTNESS = 200  # Minimize lightness value of the image's primary (background color)
MIN_SIZE = 1000  # Minimum length or width of the image, in pixels

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

CACHE_FILE = os.path.join(CACHE_DIR, 'photos.p')

class BookImage(object):
    def __init__(self):
        pass

    def __repr__(self):
        return self._img_filename
    
def create_opencv_image_from_stringio(img_stream, cv2_img_flag=0):
    img_stream.seek(0)
    img_array = np.asarray(bytearray(img_stream.read()), dtype=np.uint8)
    return cv2.imdecode(img_array, cv2_img_flag)

def flickr_search(text, tags=('bookdecade1890','bookdecade1880','bookdecade1900','bookdecade1910')):
    '''Request images from the IA Flickr account with the given century tags and the related text'''
    book_images = []

    flickr = flickrapi.FlickrAPI(FLICKR_KEY, FLICKR_SECRET, format='etree', cache=True) 
   
    search = flickr.walk(user_id=FLICKR_USER_ID,
                         per_page=200,
                         text=text,
                         tag_mode='any',
                         tags=tags,
                         extras='url_o',
                         sort='interestingness-desc')

    count_faces = 0
    count = 0
    face_cascade = cv2.CascadeClassifier(CASCADE_FILE)

    photos = {}
    photos['faces'] = []  # A set of known-faces
    photos['non_faces'] = []  # Items that aren't faces
    photos['text'] = []  # A set of photos that contain line art or text
    
    for photo in search:
        # Ensure that images are the correct minimum size
        if int(photo.get('height_o')) < MIN_SIZE or int(photo.get('width_o') < MIN_SIZE):
            continue

        # Get the source file directly
        img1_url = photo.get('url_o')
        img1_file = requests.get(img1_url, stream=True)
        img1_file.raw.decode_content = True

        # Create an in-memory representation we can pass to various image libraries
        img_io = StringIO(img1_file.raw.read())
        cv_image = create_opencv_image_from_stringio(img_io)

        # The CV image is best if it's viewable, and its size doesn't really matter for computation 
        small_cv_image = cv2.resize(cv_image, (0,0), fx=0.25, fy=0.25)                 
        faces = face_cascade.detectMultiScale(
            small_cv_image,
            scaleFactor=1.1,
            minNeighbors=4,  # Minimize errors
            minSize=(25, 25),  # 25% of the image has to be a 'face-like' thing
            flags = cv2.cv.CV_HAAR_SCALE_IMAGE
        )

        image = BookImage()
        image._cv_image = cv_image
        img_io.seek(0)
        image._img_io = img_io.read()
        image._metadata = etree.tostring(photo, encoding='utf8')

        # Save off some metadata about it 
        img_filename = "{}.png".format(photo.get('id'))
        img_dir = os.path.join(BUILD_DIR, img_filename)

        image._img_filename = img_filename
        image._img_dir = img_dir
        
        # Debug by showing the images as we move through them
        cv2.imshow("noface", small_cv_image)        
        if len(faces) != 0:
            # Put this in the face bucket
            photos['faces'].append(image)
            count_faces += 1
            
            for (x, y, w, h) in faces:
                cv2.rectangle(small_cv_image, (x, y), (x+w, y+h), (255, 255, 255), 2)

            # Debug showing the face
            cv2.imshow("face", small_cv_image)

        else:
            photos['non_faces'].append(image)  # It's not a face
            
        if count_faces > MAX_PHOTOS_PER_SECTION:
            print "Got enough pictures..."
            break
        
        count += 1
        
    pickle.dump(photos, open(CACHE_FILE, 'w'))
    return photos

def brightness(im):
   stat = ImageStat.Stat(im)
   r,g,b = stat.mean
   return math.sqrt(0.241*(r**2) + 0.691*(g**2) + 0.068*(b**2))

def process_photos(photos):

    # Randomize
    random.shuffle(photos['non_faces'])
    random.shuffle(photos['faces'])
    
    for photo in photos['faces']:

        if not os.path.exists(BUILD_DIR):
            os.makedirs(BUILD_DIR)

        hist = cv2.calcHist([photo._cv_image],[0],None,[256],[0,256])
        # Find one that's very different
        method = cv2.cv.CV_COMP_BHATTACHARYYA
        
        for p2 in list(photos['non_faces']):
            hist2 = cv2.calcHist([p2._cv_image],[0],None,[256],[0,256])
            # Smaller (0) is more similar than very different (1)
            difference = cv2.compareHist(hist, hist2, method)
            if difference > 0.6:
                print "Difference was {}".format(difference)
                
                # Choose this image
                im = Image.open(StringIO(photo._img_io))
                im2 = Image.open(StringIO(p2._img_io))

                # Fit the smaller to the larger
                if im.size[0] + im.size[1] > im2.size[0] + im2.size[1]:
                    im2 = ImageOps.fit(im2, im.size)
                else:
                    im = ImageOps.fit(im, im2.size)

                try:
                    brightness1 = brightness(im)
                    #print "brightness1: {}".format(brightness1)
                    brightness2 = brightness(im2)
                    #print "brightness2: {}".format(brightness2)
                except:
                    continue
                if brightness1 < brightness2:
                    if random.randint(1, 10) < 5:
                        im = ImageOps.solarize(im)
                        im = im.filter(ImageFilter.GaussianBlur(2))
                        im = ImageOps.grayscale(im)
                        im2 = ImageOps.grayscale(im2)                
                    im = im.filter(ImageFilter.SMOOTH_MORE)                                        
                    im2 = ImageOps.invert(im2)
                    im = ImageChops.screen(im, im2)
                    img_dir = os.path.join(BUILD_DIR, 'screen-' + photo._img_filename)

                else:
                    im = ImageChops.multiply(im, im2)
                    im = im.filter(ImageFilter.EDGE_ENHANCE_MORE)
                    im = im.filter(ImageFilter.SMOOTH_MORE)                    
                    img_dir = os.path.join(BUILD_DIR, 'multiply-' + photo._img_filename)

                    
                photos['non_faces'].remove(p2)

                im = ImageOps.autocontrast(im)
                im.save(img_dir)
                break
            
                # Apply an adaptive histogram transformation to improve the final image
                #cv2.imshow('normal', photo._cv_image)
                #clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                #photo._cv_image = clahe.apply(photo._cv_image)


if __name__ == '__main__':
    # Delete previous generated output file
    files = glob(os.path.join(BUILD_DIR, '*'))
    for f in files:
        os.unlink(f)


    if os.path.exists(CACHE_FILE):
        print "Loading from cache..."
        photos = pickle.load(open(CACHE_FILE))
    else:
        photos = flickr_search(('female'))
    process_photos(photos)
    
    
