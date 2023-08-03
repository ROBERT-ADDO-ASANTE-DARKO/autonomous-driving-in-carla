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
import carla
import random
import cv2
import numpy as np
import math
import time

IMG_WIDTH = 640
IMG_HEIGHT = 480

def decode_img(image):
    raw_image = np.array(image.raw_data)
    image_shape = raw_image.reshape((IMG_HEIGHT, IMG_WIDTH, 4))
    rgb_value = image_shape[:, :, :3]
    cv2.imshow("", rgb_value)
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
