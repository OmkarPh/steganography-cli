import argparse
import numpy as np
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import mean_squared_error as mse
from PIL import Image

import warnings
warnings.filterwarnings("ignore")


class Steganography:

    BLACK_PIXEL = (0, 0, 0)

    def _int_to_bin(self, rgb):
        """Convert an integer tuple to a binary (string) tuple.

        :param rgb: An integer tuple like (220, 110, 96)
        :return: A string tuple like ("00101010", "11101011", "00010110")
        """
        r, g, b = rgb
        return f'{r:08b}', f'{g:08b}', f'{b:08b}'

    def _bin_to_int(self, rgb):
        """Convert a binary (string) tuple to an integer tuple.

        :param rgb: A string tuple like ("00101010", "11101011", "00010110")
        :return: Return an int tuple like (220, 110, 96)
        """
        r, g, b = rgb
        return int(r, 2), int(g, 2), int(b, 2)

    def _merge_rgb(self, rgb1, rgb2):
        """Merge two RGB tuples.

        :param rgb1: An integer tuple like (220, 110, 96)
        :param rgb2: An integer tuple like (240, 95, 105)
        :return: An integer tuple with the two RGB values merged.
        """
        r1, g1, b1 = self._int_to_bin(rgb1)
        r2, g2, b2 = self._int_to_bin(rgb2)
        rgb = r1[:4] + r2[:4], g1[:4] + g2[:4], b1[:4] + b2[:4]
        return self._bin_to_int(rgb)

    def _unmerge_rgb(self, rgb):
        """Unmerge RGB.

        :param rgb: An integer tuple like (220, 110, 96)
        :return: An integer tuple with the two RGB values merged.
        """
        r, g, b = self._int_to_bin(rgb)
        # Extract the last 4 bits (corresponding to the hidden image)
        # Concatenate 4 zero bits because we are working with 8 bit
        new_rgb = r[4:] + '0000', g[4:] + '0000', b[4:] + '0000'
        return self._bin_to_int(new_rgb)

    def merge(self, coverImage, secretImage):
        """Merge secretImage into coverImage.

        :param coverImage: First image
        :param secretImage: Second image
        :return: A new merged image.
        """
        # Check the images dimensions
        if secretImage.size[0] > coverImage.size[0] or secretImage.size[1] > coverImage.size[1]:
            raise ValueError('Image 2 should be smaller than Image 1!')

        # Get the pixel map of the two images
        map1 = coverImage.load()
        map2 = secretImage.load()

        new_image = Image.new(coverImage.mode, coverImage.size)
        new_map = new_image.load()

        for i in range(coverImage.size[0]):
            for j in range(coverImage.size[1]):
                is_valid = lambda: i < secretImage.size[0] and j < secretImage.size[1]
                rgb1 = map1[i ,j]
                rgb2 = map2[i, j] if is_valid() else self.BLACK_PIXEL
                new_map[i, j] = self._merge_rgb(rgb1, rgb2)
        return new_image

    def unmerge(self, image, compare=None):
        """Unmerge an image.

        :param image: The input image.
        :param compare: The path to the original image for comparison.
        :return: The unmerged/extracted image.
        """
        pixel_map = image.load()

        # Create the new image and load the pixel map
        new_image = Image.new(image.mode, image.size)
        new_map = new_image.load()

        original_image = None
        if compare:
            original_image = Image.open(compare)

        ssim_value, psnr_value, mse_value = 0, 0, 0

        for i in range(image.size[0]):
            for j in range(image.size[1]):
                decoded_pixel = self._unmerge_rgb(pixel_map[i, j])
                new_map[i, j] = decoded_pixel

                if compare and original_image and i < original_image.size[0] and j < original_image.size[1]:
                    original_pixel = original_image.getpixel((i, j))

                    # Convert pixels to numpy arrays for metric calculations
                    decoded_np = np.array(decoded_pixel)
                    original_np = np.array(original_pixel)

                    # Calculate metrics
                    ssim_value += ssim(original_np, decoded_np, win_size=3, full=True)[1].mean()
                    if decoded_pixel != original_pixel:
                        psnr_value += psnr(original_np, decoded_np)
                    mse_value += mse(original_np, decoded_np)

        if compare and original_image:
            num_pixels = image.size[0] * image.size[1]
            ssim_value /= num_pixels
            psnr_value /= num_pixels
            mse_value /= num_pixels

            print()
            print(f'Structural Similarity Index (SSIM): {ssim_value:.4f}')
            print(f'Peak Signal-to-Noise Ratio (PSNR): {psnr_value:.2f} dB')
            print(f'Mean Squared Error (MSE): {mse_value:.2f}')
            print()

            # print(f'Mean Absolute Error (MAE): {mae_value:.2f}')

        return new_image


def main():
    parser = argparse.ArgumentParser(description='Steganography')
    subparser = parser.add_subparsers(dest='command')

    merge = subparser.add_parser('merge')
    merge.add_argument('--coverImage', required=True, help='coverImage path')
    merge.add_argument('--secretImage', required=True, help='secretImage path')
    merge.add_argument('--output', required=True, help='Output path')

    unmerge = subparser.add_parser('unmerge')
    unmerge.add_argument('--image', required=True, help='Image path')
    unmerge.add_argument('--output', required=True, help='Output path')
    unmerge.add_argument('--compare', required=False, help='Compare original secret path')

    args = parser.parse_args()

    if args.command == 'merge':
        coverImage = Image.open(args.coverImage)
        secretImage = Image.open(args.secretImage)
        Steganography().merge(coverImage, secretImage).save(args.output)
        print(f"Saved encoded image to {args.output}")

    elif args.command == 'unmerge':
        image = Image.open(args.image)
        Steganography().unmerge(image, compare=args.compare).save(args.output)
        print(f"Saved decoded image to {args.output}")

if __name__ == '__main__':
    main()
