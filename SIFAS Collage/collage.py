import matplotlib.pyplot as plt
import numpy as np
import os
import pdb
import cv2
"""
Copyright <2021> <Olionheart>

Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is 
hereby granted, provided that the above copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO 
THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL 
THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES 
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, 
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""

# Quick Guide:
# 1. drop your screenshots in input folder, sorted alphabetically
# 2. the settings were based on my screenshots, which is of dimension 2388 x 1688, if your device has different resolution, change them below so that the initial crop leaves only titles with some white margin. white_margin_width is the size of white rows and columns between titles, in pixels. white_pixel_loc is a location where the white pixel is sampled from (in case it's not 0xFFFFFF)
# 3. set last_image_row_to_flush i.e. how many rows of title on the last image overlap with the previous image. sometimes you have to add 1 because of the line from the previous row's edge.
# 4. run the code. if something seems off, try to change some settings and/or code. remember that this is a quick and dirty solution so I couldn't be bothered to make it more generic
# 5. happy tiering! :)

# in case your screenshot requires flushing on more than one image, change last_image_row_to_flush to a list (make sure that its length corresponds with the number of files in input folder)
# otherwise, make it an integer
# in particular, I used a list for T10 collage and an integer for title collage. Therefore, if you use list, it will also flush from the bottom reading from bottom_flush_list. 
# bottom_flush_list is NOT used if last_image_row_to_flush is an integer (unless you modify it yourself, of course. I told you it's quick and dirty)

# iPhone T10
"""
last_image_row_to_flush = [0, 2]
bottom_flush_list = [1, 1]
top_crop = 240
bot_crop = 1090
left_crop = 20
right_crop = 1632
white_pixel_loc_x = 248
white_pixel_loc_y = 248
white_margin_width = 15
"""

# my settings for T10 collage (or any event ranking collage) - iPad
"""
last_image_row_to_flush = [0, 0, 0, 0]
bottom_flush_list = [1, 1, 1, 3]
top_crop = 400
bot_crop = 1327
left_crop = 20
right_crop = 1764
white_pixel_loc_x = 50
white_pixel_loc_y = 265
white_margin_width = 18
"""

# my settings for title collage
last_image_row_to_flush = 3
top_crop = 315
bot_crop = 1290
left_crop = 50
right_crop = 1760
white_pixel_loc_x = 330
white_pixel_loc_y = 230
white_margin_width = 28

def is_empty_row(img):
    pixel = img[0,:]
    for x in range(img.shape[0]):
        if np.all(img[x,:] == pixel):
            pass
        else:
            return False
    return True

images = list()

if type(last_image_row_to_flush) == type(1):
    files = os.listdir('input/')
    for x in files[:-1]:
        img = cv2.imread('input/' + x)
        crop = img[top_crop:bot_crop,left_crop:right_crop,:]
        empty_col = crop[:,0,:]
        empty_row = crop[0,:,:]
        crop_t = 0
        crop_b = crop.shape[0]
        crop_l = 0
        crop_r = crop.shape[1]
        while is_empty_row(crop[crop_t,:,:]):
            crop_t += 1
        while is_empty_row(crop[crop_b-1,:,:]):
            crop_b -= 1
        while np.all(crop[:,crop_l,:] == empty_col):
            crop_l += 1
        while np.all(crop[:,crop_r-1,:] == empty_col):
            crop_r -= 1
        final_crop = crop[crop_t:crop_b, crop_l:crop_r, :]
        images.append(final_crop)

    img = cv2.imread('input/' + files[-1])
    crop = img[top_crop:bot_crop,left_crop:right_crop,:]
    empty_col = crop[:,0,:]
    crop_t = 0
    crop_b = crop.shape[0]
    crop_l = 0
    crop_r = crop.shape[1]
    while is_empty_row(crop[crop_t,:,:]):
        crop_t += 1
    while last_image_row_to_flush != 0:
        while not is_empty_row(crop[crop_t,:,:]):
            crop_t += 1
        while is_empty_row(crop[crop_t,:,:]):
            crop_t += 1
        last_image_row_to_flush -= 1
    while is_empty_row(crop[crop_b-1,:,:]):
        crop_b -= 1
    while np.all(crop[:,crop_l,:] == empty_col):
        crop_l += 1
    while np.all(crop[:,crop_r-1,:] == empty_col):
        crop_r -= 1
    final_crop = crop[crop_t:crop_b, crop_l:crop_r, :]
    images.append(final_crop)
else:
    files = os.listdir('input/')
    for i in range(len(files)):
        x = files[i]
        img = cv2.imread('input/' + x)
        top_flush = last_image_row_to_flush[i]
        crop = img[top_crop:bot_crop,left_crop:right_crop,:]
        empty_col = crop[:,0,:]
        empty_row = crop[0,:,:]
        crop_t = 0
        crop_b = crop.shape[0]
        crop_l = 0
        crop_r = crop.shape[1]
        while is_empty_row(crop[crop_t,:,:]):
            crop_t += 1
        while top_flush != 0:
            while not is_empty_row(crop[crop_t,:,:]):
                crop_t += 1
            while is_empty_row(crop[crop_t,:,:]):
                crop_t += 1
            top_flush -= 1
        while is_empty_row(crop[crop_b-1,:,:]):
            crop_b -= 1
        bottom_flush = bottom_flush_list[i]
        while bottom_flush != 0:
            while not is_empty_row(crop[crop_b-1,:,:]):
                crop_b -= 1
            while is_empty_row(crop[crop_b-1,:,:]):
                crop_b -= 1
            bottom_flush -= 1
        while np.all(crop[:,crop_l,:] == empty_col):
            crop_l += 1
        while np.all(crop[:,crop_r-1,:] == empty_col):
            crop_r -= 1
        final_crop = crop[crop_t:crop_b, crop_l:crop_r, :]
        images.append(final_crop)


final_crop = images[-2]
white_pixel = final_crop[white_pixel_loc_y, white_pixel_loc_x, :]
row_padding = np.array([[white_pixel for i in range(final_crop.shape[1])] for j in range(white_margin_width)])
output = row_padding.copy()
for img in images:
    output = np.concatenate((output, img, row_padding), axis=0)
col_padding = np.array([[white_pixel for i in range(white_margin_width)] for j in range(output.shape[0])])
output = np.concatenate((col_padding, output, col_padding), axis=1)
cv2.imwrite('collage.png', output)

