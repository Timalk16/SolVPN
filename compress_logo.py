from PIL import Image

# Path to the original logo
input_path = 'assets/logo.jpeg'
# Path to save the compressed logo
output_path = 'assets/logo_compressed.jpeg'

# Open the image
img = Image.open(input_path)

# Resize to max 1024x1024, keeping aspect ratio
img.thumbnail((1024, 1024))

# Save with reduced quality
img.save(output_path, 'JPEG', quality=85, optimize=True)

print(f"Compressed image saved to {output_path}") 