random.chance
=============

A procedurally generated surrealist photoset
--------------

Generate images that resemble surrealist portrait photomontages in the style of Man Ray. Uses the following resources:

* The Flickr API and Internet Archive Commons account to grab period images
* Runs face detection (packaged with OpenCV http://opencv.org/) to identify human faces for candidate portraits
* Blends face and non-face images using some best guesses about optimal blending algorithms (multiply or screen work best)

The source code in this repository is in the public domain. 

The book
--------

![Page](examples/page11.jpg)


After dozens of code runs I selected my favorite images and laid them out into a book with two-page spreads. No changes were made to the images themselves. [Browse all 140 pages online.] (http://lizadaly.com/random-chance/pages/#/0)

A 140-page [PDF version] (https://www.dropbox.com/s/0p7ikz9baw2i7ad/random-chance.pdf?dl=0), best viewed as 2-up, is also available  *(Warning: 240 MB)* or [in print from Blurb.] (http://www.blurb.com/b/5936745-random-chance)


Source code installation
------------

Generate your own book by tweaking parameters in the source code!

Set up a virtual environment:

```
virtualenv ve
````

Ensure that you have various image libraries installed (for OS X users, `brew install libjpeg` and `brew install libpng`).

Install the dependencies:

```
. ve/bin/activate
python setup.py develop
```

*Installing numpy and OpenCV are a huge pain. You've been warned.*

This worked for me:

https://jjyap.wordpress.com/2014/05/24/installing-opencv-2-4-9-on-mac-osx-with-python-support/

(Your version of OpenCV will be newer; link the files into your ve.)

In manray/__init__.py, update this:

```
CASCADE_FILE = '/usr/local/Cellar/opencv/2.4.10.1/share/OpenCV/haarcascades/haarcascade_frontalface_default.xml'
```

If numpy doesn't install, uninstall python via brew and update it, setuptools, and pip. `pip install numpy` should then work.

Get a Flickr API key and add it to a directory called `secret`:

```
mkdir secret
cat "FLICKR_KEY = 'YOUR-KEY-HERE'" > secret/__init__.py
cat "FLICKR_SECRET = 'YOUR-SECRET-HERE'" >> secret/__init__.py
```

Run the program:

```
python manray/flickr.py
```

The program should go off and acquire a _lot_ of images from Flickr and try to generate nice output. Depending on your search parameters you can expect to get around 10 decent images out of each run.

Once it runs, it will cache the resulting images (as local pickle files) in `manray/cache` and pull a random set from those. Delete that directory to re-acquire the assets from Flickr.

The output will be in `manray/build/`.

Example output
==============

[Browse all 140 pages online](https://www.flickr.com/photos/lizadaly/albums/72157648041689654)

![Page](examples/page14.jpg)
![Page](examples/page15.jpg)
![Page](examples/page16.jpg)
![Page](examples/page17.jpg)
![Page](examples/page1.jpg)
![Page](examples/page2.jpg)
![Page](examples/page3.jpg)
![Page](examples/page5.jpg)
![Page](examples/page7.jpg)
![Page](examples/page8.jpg)
![Page](examples/page9.jpg)
![Page](examples/page10.jpg)
![Page](examples/page12.jpg)
![Page](examples/page13.jpg)



