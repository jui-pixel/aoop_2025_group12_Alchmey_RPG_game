import argparse
import os
from PIL import Image

def get_project_path(*subpaths):
    """Get the absolute path to the project root (roguelike_dungeon/) and join subpaths."""
    project_root = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(project_root, *subpaths)

def split_image(input_path, output_dir, tile_size=32):
    """Split an image into tile_size x tile_size tiles and save them."""
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Open the image
    try:
        img = Image.open(input_path)
    except Exception as e:
        print(f"無法開啟圖片 {input_path}: {e}")
        return

    width, height = img.size

    # Check if image dimensions are multiples of tile_size
    if width % tile_size != 0 or height % tile_size != 0:
        print(f"警告：圖片 {input_path} 尺寸 {width}x{height} 不是 {tile_size}x{tile_size} 的整數倍，可能導致裁切不完整！")

    # Calculate number of rows and columns
    cols = width // tile_size
    rows = height // tile_size

    # Get base name of input file (without extension)
    base_name = os.path.splitext(os.path.basename(input_path))[0]

    # Iterate and split tiles
    for row in range(rows):
        for col in range(cols):
            left = col * tile_size
            upper = row * tile_size
            right = left + tile_size
            lower = upper + tile_size

            # Crop the tile
            tile = img.crop((left, upper, right, lower))

            # Save tile with format: base_name_row_col.png
            tile_name = f"{base_name}_{row}_{col}.png"
            tile_path = os.path.join(output_dir, tile_name)
            tile.save(tile_path)
            print(f"已儲存：{tile_path}")

def process_all_images(input_dir, output_dir, tile_size=32):
    """Process all PNG/JPG images in the input directory."""
    if not os.path.exists(input_dir):
        print(f"錯誤：輸入資料夾 {input_dir} 不存在！")
        print(f"正在建立輸入資料夾：{input_dir}")
        os.makedirs(input_dir)
        return

    for filename in os.listdir(input_dir):
        if filename.lower().endswith((".png", ".jpg")):
            input_path = os.path.join(input_dir, filename)
            split_image(input_path, output_dir, tile_size)

if __name__ == "__main__":
    # Define default paths relative to project root
    default_input_dir = get_project_path("src", "assets", "original")
    default_output_dir = get_project_path("src", "assets", "processed")
    default_tile_size = 32

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Split images into tiles for Alchemy RPG Game.")
    parser.add_argument("--input_dir", type=str, default=default_input_dir,
                        help=f"Input directory containing images to split (default: {default_input_dir})")
    parser.add_argument("--output_dir", type=str, default=default_output_dir,
                        help=f"Output directory for processed tiles (default: {default_output_dir})")
    parser.add_argument("--tile_size", type=int, default=default_tile_size,
                        help=f"Size of each tile in pixels (default: {default_tile_size})")

    # Parse arguments
    args = parser.parse_args()

    # Validate tile_size
    if args.tile_size <= 0:
        print(f"錯誤：tile_size 必須為正整數，收到 {args.tile_size}")
        exit(1)

    # Convert relative paths to absolute paths if necessary
    input_dir = os.path.abspath(args.input_dir)
    output_dir = os.path.abspath(args.output_dir)
    tile_size = args.tile_size

    # Print directories and tile size for debugging
    print(f"當前工作目錄: {os.getcwd()}")
    print(f"輸入資料夾: {input_dir}")
    print(f"輸出資料夾: {output_dir}")
    print(f"瓦片大小: {tile_size}x{tile_size}")

    # Process all images
    process_all_images(input_dir, output_dir, tile_size)