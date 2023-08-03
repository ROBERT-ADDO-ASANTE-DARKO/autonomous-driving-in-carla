import os
import sys
import glob

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass
import cv2
import numpy as np
import carla
import random
import time

IMG_HEIGHT = 480
IMG_WIDTH = 640

def decode_img(image):
    raw_image = np.array(image.raw_data)
    image_shape = raw_image.reshape((IMG_HEIGHT, IMG_WIDTH, 4))
    rgb_value = image_shape[:, :, :3]

    # Compute histogram of gradients
    gray_value = cv2.cvtColor(rgb_value, cv2.COLOR_RGB2GRAY)
    sobelx = cv2.Sobel(gray_value, cv2.CV_64F, 1, 0, ksize=5)
    sobely = cv2.Sobel(gray_value, cv2.CV_64F, 0, 1, ksize=5)
    magnitude = np.sqrt(sobelx ** 2 + sobely ** 2)
    angle = np.arctan2(sobely, sobelx) * 180 / np.pi
    angle[angle < 0] += 180
    histogram, bin_edges = np.histogram(angle, bins=9, range=(0, 180), weights=magnitude)

    # Display RGB and HOG images
    cv2.imshow("RGB Image", rgb_value)
    hog_image = np.zeros_like(rgb_value)
    for i in range(9):
        angle_range = (i * 20, (i+1) * 20)
        mask = (angle >= angle_range[0]) & (angle < angle_range[1])
        hog_image[:,:,0][mask] = histogram[i]
    cv2.imshow("HOG Image", hog_image)
    cv2.waitKey(1)

    return rgb_value/255.0

actor_list = []
try:
    client = carla.Client('localhost', 2000)
    client.set_timeout(80.0)
    
    world = client.get_world()
    
    blueprint_library = world.get_blueprint_library()
    tesla_model3 = blueprint_library.filter('model3')[0]
    print(tesla_model3)
    
    spawn_point = random.choice(world.get_map().get_spawn_points())
    vehicle = world.spawn_actor(tesla_model3, spawn_point)
    control_vehicle = carla.VehicleControl(throttle=1.0, steer=0.0)
    vehicle.apply_control(control_vehicle)
    actor_list.append(vehicle)
    
    blueprint = blueprint_library.find('sensor.camera.rgb')
    blueprint.set_attribute('image_size_x', f'{IMG_WIDTH}')
    blueprint.set_attribute('image_size_y', f'{IMG_HEIGHT}')
    blueprint.set_attribute('fov', '110')
    
    spawn_point = carla.Transform(carla.Location(x=2.5, z=0.7))
    sensor = world.spawn_actor(blueprint, spawn_point, attach_to=vehicle)
    
    actor_list.append(sensor)
    sensor.listen(lambda data: decode_img(data))
    
    time.sleep(60)
    
finally:
    print("Cleaning up actors...")
    for actor in actor_list:
        actor.destroy()
    print("Done, Actors cleaned-up successfully!")
