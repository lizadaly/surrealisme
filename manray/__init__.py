import os.path


THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

BUILD_DIR = os.path.join(THIS_DIR, 'build')
CACHE_DIR = os.path.join(THIS_DIR, 'cache')
CASCADE_FILE = '/usr/local/Cellar/opencv/2.4.10.1/share/OpenCV/haarcascades/haarcascade_frontalface_default.xml'
