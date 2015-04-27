#!/usr/bin/env python
#  PhotoBoothSw is a photobooth implementation supporting the RasberryPi
#  Copyright (C) 2015 Jason Holden

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import pygame, sys
import pygame.camera
import PIL
from PIL import Image 
from time import sleep
from pygame.locals import *
import tempfile
import atexit


# See if the rasberry pi camera is available
try:
    import picamera
    picamera_available = True
except ImportError:
    picamera_available = False

# See if rasberry pi gpio is available
try:
    import RPi.GPIO as GPIO
    rpi_gpio_available = True
    gpio_mode=GPIO.BOARD
    pin_takephoto = 7
    pin_alarm     = 18
    print "RPi GPIO Version: " + str(GPIO.VERSION)
except ImportError:
    rpi_gpio_available = False
    
print "picamera available," + str(picamera_available)
print "rpi_gpio available, " + str(rpi_gpio_available)

# set up pygame
pygame.init()

WIDTH=1280
HEIGHT=1024
# .5 = 640x512
# .4 ~= 512x409
NUM_SHOTS_PER_PRINT=4
curShot=0


# INIT CAMERA
if picamera_available == True:
    # Initialize camera with picamera library
    print "Initializing Rasberry Pi Camera"
    camera = picamera.PiCamera()
    camera.vflip = True
    camera.hflip = False
    camera.brightness = 60
else:
    print "Initializing Native Linux Camera"
    pygame.camera.init()
    cameras = pygame.camera.list_cameras()
    print ("Using camera " + cameras[0])
    camera = pygame.camera.Camera(cameras[0],(WIDTH, HEIGHT))
    camera.start()
    
screen = pygame.display.set_mode( ( WIDTH, HEIGHT ) )
pygame.display.set_caption("pyGame Camera View")
black = pygame.Color(0, 0, 0)
textcol = pygame.Color(255, 255, 0)
screen.fill(black)

# Open the photobooth background image
in_bgimage = PIL.Image.open("./photo_template.jpg")

#Cleanup GPIO settings
def cleanup():
    if (rpi_gpio_available == True):
        print('Cleaning up GPIO')
        GPIO.cleanup()

atexit.register(cleanup)

# Platform-agonstic function to save snapshot as jpg
def get_current_image_as_jpg( camera, filename ):
    if picamera_available == True:
        #camera.start_preview()
        camera.capture(filename, format='jpeg', resize=(WIDTH,HEIGHT))
        #camera.stop_preview()
    else:
        img = camera.get_image()
        pygame.image.save(img,filename)
    return

# Platform-agnostic function to get camera image (needs to be fast)
def get_current_image_fast( camera ):
    if picamera_available == True:
        camera.capture('/tmp/photobooth_curcam.jpg', format='jpeg', resize=(WIDTH,HEIGHT))
	return pygame.image.load('/tmp/photobooth_curcam.jpg')
    else:
        return camera.get_image()
    return


# Create the final composited image for printing
def composite_images ( bgimage ):
    print "Creating final image for printing"
    for x in xrange(0,NUM_SHOTS_PER_PRINT):
        cam_image = PIL.Image.open("./image" + str(x) + ".jpg")
        cam_image.thumbnail((512,419), Image.ANTIALIAS)
        if x == 0:
            bgimage.paste(cam_image,(64,25))
            bgimage.paste(cam_image,(640,25))
        if x == 1:
            bgimage.paste(cam_image,(64,469))
            bgimage.paste(cam_image,(640,469))
        if x == 2:
            bgimage.paste(cam_image,(64,913))
            bgimage.paste(cam_image,(640,913))
        if x == 3:
            bgimage.paste(cam_image,(64,1357))
            bgimage.paste(cam_image,(640,1357))
    bgimage.save("out.jpg")
    return

# Setup gpio
def setup_gpio():
    global gpio_mode
    global pin_takephoto
    global pin_alarm

    print "Setting up GPIO" + str(pin_takephoto)  + "," + str(pin_alarm)

    GPIO.setmode(gpio_mode)
    GPIO.setup(pin_takephoto,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(pin_alarm,GPIO.OUT)
    GPIO.add_event_detect(pin_takephoto, GPIO.RISING, callback=delayed_photo, bouncetime=300) 
    GPIO.output(pin_alarm,True)

def delayed_photo(channel):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN,key = pygame.K_SPACE))
    
def initiate_photo(channel):
    global curShot
    print "Taking a snapshot " + str(curShot)
    # Update the display with the latest image
    get_current_image_as_jpg(camera, 'image' + str(curShot) + '.jpg')
    print "Finished getting image"
    curShot = curShot + 1
    if curShot == NUM_SHOTS_PER_PRINT:
        # Produce the final output image
        composite_images ( in_bgimage )
        curShot = 0
    
if rpi_gpio_available == True:
    setup_gpio()

print "Press <space> to take a snapshot"
while True :

    # Loop Over all events
    for e in pygame.event.get() :
        if e.type == pygame.QUIT :
            sys.exit()

        # On a Key-Down, trigger a photo-event
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE:
                initiate_photo(0)
                
    #READ IMAGE AND PUT ON SCREEN
    img = get_current_image_fast( camera )
    screen.blit(img, (0, 0))
    pygame.display.update()

