from PIL import Image
import os

def get_project_path(*subpaths):
    """Get the absolute path to the project root (roguelike_dungeon/) and join subpaths."""
    # Assume the script is in the project root (roguelike_dungeon/)
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
    # Define input and output directories relative to project root
    input_dir = get_project_path("src", "assets", "original")
    output_dir = get_project_path("src", "assets", "processed")

    # Print current working directory for debugging
    print(f"當前工作目錄: {os.getcwd()}")
    print(f"輸入資料夾: {input_dir}")
    print(f"輸出資料夾: {output_dir}")

    # Process all images
    process_all_images(input_dir, output_dir, tile_size=32)