from PIL import Image
import numpy as np

def convert_to_nbit_64x64(input_path, output_path, bits_per_channel=1):
    """
    Convert an image to 64x64 with N bits per RGB channel.

    Args:
        input_path (str): path to input image
        output_path (str): path to save output image
        bits_per_channel (int): number of bits per channel (1-8)
    """
    # Load image
    img = Image.open(input_path).convert("RGB")

    # Resize to 64x64
    img = img.resize((64, 64), Image.LANCZOS)

    # Convert to numpy array
    arr = np.array(img, dtype=np.uint8)

    # Calculate number of levels
    levels = 2 ** bits_per_channel

    # Scale and quantize
    arr_nbit = (arr / 255 * (levels - 1)).round() / (levels - 1) * 255
    arr_nbit = arr_nbit.astype(np.uint8)

    # Convert back to image
    img_nbit = Image.fromarray(arr_nbit, 'RGB')

    # Save result
    img_nbit.save(output_path)
    print(f"Saved {bits_per_channel}-bit 64x64 image to: {output_path}")

if __name__ == "__main__":
    base_path = "../files"

    taylor_in = f"{base_path}/taylor_swift.png"
    convert_to_nbit_64x64(taylor_in, f"{base_path}/taylor_swift_64x64x1.png", 1)
    convert_to_nbit_64x64(taylor_in, f"{base_path}/taylor_swift_64x64x2.png", 2)
    convert_to_nbit_64x64(taylor_in, f"{base_path}/taylor_swift_64x64x4.png", 4)
    convert_to_nbit_64x64(taylor_in, f"{base_path}/taylor_swift_64x64x8.png", 8)
    convert_to_nbit_64x64(taylor_in, f"{base_path}/taylor_swift_64x64x16.png", 16)

    olivia_in = f"{base_path}/olivia_rodrigo.png"
    convert_to_nbit_64x64(olivia_in, f"{base_path}/olivia_rodrigo_64x64x1.png", 1)
    convert_to_nbit_64x64(olivia_in, f"{base_path}/olivia_rodrigo_64x64x2.png", 2)
    convert_to_nbit_64x64(olivia_in, f"{base_path}/olivia_rodrigo_64x64x4.png", 4)
    convert_to_nbit_64x64(olivia_in, f"{base_path}/olivia_rodrigo_64x64x8.png", 8)
    convert_to_nbit_64x64(olivia_in, f"{base_path}/olivia_rodrigo_64x64x16.png", 16)
