from PIL import Image
from io import BytesIO
import numpy as np

def generateDownloadableImage(img):
    img = Image.fromarray(img)
    buf = BytesIO()
    img.save(buf, format="png")
    byte_im = buf.getvalue()
    return byte_im

def generateDownloadableImageFromPilImage(img: Image):
    buf = BytesIO()
    img.save(buf, format="png")
    byte_im = buf.getvalue()
    return byte_im

def _int_to_bin(rgb):
    """Convert an integer tuple to a binary (string) tuple.

    :param rgb: An integer tuple like (220, 110, 96)
    :return: A string tuple like ("00101010", "11101011", "00010110")
    """
    r, g, b = rgb
    return f'{r:08b}', f'{g:08b}', f'{b:08b}'

def _bin_to_int(rgb):
    """Convert a binary (string) tuple to an integer tuple.

    :param rgb: A string tuple like ("00101010", "11101011", "00010110")
    :return: Return an int tuple like (220, 110, 96)
    """
    r, g, b = rgb
    return int(r, 2), int(g, 2), int(b, 2)

def merge_rgb(rgb1, rgb2):
    """Merge two RGB tuples.

    :param rgb1: An integer tuple like (220, 110, 96)
    :param rgb2: An integer tuple like (240, 95, 105)
    :return: An integer tuple with the two RGB values merged.
    """
    r1, g1, b1 = _int_to_bin(rgb1)
    r2, g2, b2 = _int_to_bin(rgb2)
    rgb = r1[:4] + r2[:4], g1[:4] + g2[:4], b1[:4] + b2[:4]
    return _bin_to_int(rgb)

def _unmerge_rgb(rgb):
    """Unmerge RGB.

    :param rgb: An integer tuple like (220, 110, 96)
    :return: An integer tuple with the two RGB values merged.
    """
    r, g, b = _int_to_bin(rgb)
    # Extract the last 4 bits (corresponding to the hidden image)
    # Concatenate 4 zero bits because we are working with 8 bit
    new_rgb = r[4:] + '0000', g[4:] + '0000', b[4:] + '0000'
    return _bin_to_int(new_rgb)

def to_bin(data):
    """
    Convert `data` to binary format as string

    Args:
        data (str, bytes, np array, int or uint8): it refers to the data that its format is needed to be changed

    """
    if isinstance(data, str):
        return ''.join([format(ord(i), "08b") for i in data])
    elif isinstance(data, bytes):
        return ''.join([format(i, "08b") for i in data])
    elif isinstance(data, np.ndarray):
        return [format(i, '08b') for i in data]
    elif isinstance(data, int) or isinstance(data, np.uint8):
        return format(data, "08b")
    else:
        raise TypeError("Type not supported")


def calculate_image_max_bytes(img):
    """ max_bytes calculation: 
        each pixel on a photo holds a byte for each of the 3 makeup colors namely; red, green, blue.
        each pixel equals to 3 bytes, with each color equaling to 1byte, where 1 byte == 8bits
        if we imagine an image with size of 720*480 then we have 720 x 480 = 345,600 pixels
        since each pixel holds three bytes(for the assumed 24 Bit Depth size) 
        so we can calculate total bytes 345600 x 3 =  1, 036, 800 bytes
        and since 1byte = 8bit so we need to divide it by 8 and get the division floor

    Args:
        img (PIL Image Object): The Image

    Returns:
        int: return max_bytes as Integer
    """
    img = Image.open(img)
    img_numpy = np.array(img.convert('RGB'))
    max_bytes = img_numpy.shape[0] * img_numpy.shape[1] * 3 // 8
    return max_bytes


def encode(uploaded: object, secret_data: str, key: str):
    """
    Args:
        image (PIL Image): it refers to the uploaded image
        secret_data (str): refers to your secret message
        key (str): refers to the key that you as sender and the person who is going to receive the message must have
        max_bytes (int):

    Raises:
        ValueError: if there is Insufficient

    Returns:
        img: returns a numpy ndarray
    """
    # read the uploaded image
    img = Image.open(uploaded)
    img = np.array(img.convert('RGB'))
    # add stopping criteria using the defined key
    secret_data += key
    data_index = 0
    # convert data to binary
    binary_secret_data = to_bin(secret_data)
    # size of data to hide
    data_len = len(binary_secret_data)

    for row in img:
        for pixel in row:
            # convert RGB values to binary format
            r, g, b = to_bin(pixel)
            # modify the LSB(least significant bit) only if there is still data to store
            if data_index < data_len:
                # least significant red pixel bit
                pixel[0] = int(r[:-1] + binary_secret_data[data_index], 2)
                data_index += 1
            if data_index < data_len:
                # least significant green pixel bit
                pixel[1] = int(g[:-1] + binary_secret_data[data_index], 2)
                data_index += 1
            if data_index < data_len:
                # least significant blue pixel bit
                pixel[2] = int(b[:-1] + binary_secret_data[data_index], 2)
                data_index += 1
            # if data is encoded, just break out of the loop
            if data_index >= data_len:
                break
    flag = 'Encode-Done'
    return flag, img


def decode(encoded_img, key):
    binary_data = ""
    for row in encoded_img:
        for pixel in row:
            r, g, b = pixel
            r, g, b = to_bin(pixel)
            binary_data += r[-1]
            binary_data += g[-1]
            binary_data += b[-1]
    # split by 8-bits
    all_bytes = [binary_data[i: i+8] for i in range(0, len(binary_data), 8)]
    # convert from bits to characters
    decoded_data = ""
    for byte in all_bytes:
        decoded_data += chr(int(byte, 2))
        if decoded_data[-len(key):] == key:
            break
    flag = 'Decode-Done'
    return flag, decoded_data[:-len(key)]

BLACK_PIXEL = (0, 0, 0)

def encode_images(container_image, secret_image):
    coverImage = container_image
    secretImage = secret_image
    secret_image = secret_image.resize(container_image.size)

    # if secretImage.size[0] > coverImage.size[0] or secretImage.size[1] > coverImage.size[1]:
    #     raise ValueError('Image 2 should be smaller than Image 1!')

    map1 = coverImage.load()
    map2 = secretImage.load()

    new_image = Image.new(coverImage.mode, coverImage.size)
    new_map = new_image.load()

    for i in range(coverImage.size[0]):
        for j in range(coverImage.size[1]):
            is_valid = lambda: i < secretImage.size[0] and j < secretImage.size[1]
            rgb1 = map1[i ,j]
            rgb2 = map2[i, j] if is_valid() else BLACK_PIXEL
            new_map[i, j] = merge_rgb(rgb1, rgb2)
    return new_image

    
    container_np = np.array(container_image.convert('RGB'))
    secret_np = np.array(secret_image.convert('RGB'))

    for i in range(container_np.shape[0]):
        for j in range(container_np.shape[1]):
            for c in range(3):  # Iterate over RGB channels
                container_np[i, j, c] = (container_np[i, j, c] & 0xFE) | (secret_np[i, j, c] >> 7)

    return container_np


def decode_image(encoded_image):
    image = encoded_image
    pixel_map = image.load()

    # Create the new image and load the pixel map
    new_image = Image.new(image.mode, image.size)
    new_map = new_image.load()

    for i in range(image.size[0]):
        for j in range(image.size[1]):
            decoded_pixel = _unmerge_rgb(pixel_map[i, j])
            new_map[i, j] = decoded_pixel
    return new_image

    # width, height = encoded_image.size
    # decoded_np = np.zeros((height, width, 3), dtype=np.uint8)

    # for i in range(height):
    #     for j in range(width):
    #         pixel_value = list(encoded_image.getpixel((j, i)))
    #         for c in range(3):  # Iterate over RGB channels
    #             pixel_value[c] = (pixel_value[c] & 1) * 255
    #         decoded_np[i, j, :] = pixel_value

    # decoded_image = Image.fromarray(decoded_np.astype('uint8'), 'RGB')
    # return decoded_image
