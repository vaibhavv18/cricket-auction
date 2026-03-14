"""
Utility functions for the Auction Management System.

Helper scripts for setup and data management.
"""

import os
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from config import IMAGES_DIR, PLAYERS_CSV_PATH


def generate_photo_filename(full_name: str) -> str:
    """
    Generate a photo filename from player's full name.

    Args:
        full_name: Player's full name

    Returns:
        Generated filename (e.g., "vaibhav_ahir.jpg")

    Example:
        >>> generate_photo_filename("Vaibhav Ahir")
        'vaibhav_ahir.jpg'
    """
    filename = full_name.lower().replace(" ", "_")
    filename = "".join(c for c in filename if c.isalnum() or c == "_")
    return f"{filename}.jpg"


def list_required_photos():
    """
    List all photo filenames required based on players.csv.

    Prints a list of required photo filenames.
    """
    if not PLAYERS_CSV_PATH.exists():
        print(f"Error: {PLAYERS_CSV_PATH} not found")
        return

    df = pd.read_csv(PLAYERS_CSV_PATH)
    print("Required photo filenames:")
    print("-" * 50)

    for _, row in df.iterrows():
        full_name = row["Full Name"]
        photo_filename = generate_photo_filename(full_name)
        exists = (IMAGES_DIR / photo_filename).exists()
        status = "✅" if exists else "❌"
        print(f"{status} {photo_filename:30} ({full_name})")


def rename_photos_interactive():
    """
    Interactive script to rename photos in the images directory.

    Helps rename photos to match the required naming convention.
    """
    image_files = list(IMAGES_DIR.glob("*.jpg")) + list(IMAGES_DIR.glob("*.png"))

    if not image_files:
        print("No images found in the images directory")
        return

    print("Photos found in images directory:")
    print("-" * 50)

    for idx, image_path in enumerate(image_files, 1):
        print(f"{idx}. {image_path.name}")

    print("\nRename photos to match player names?")
    print("Example: 'Vaibhav Ahir.jpg' → 'vaibhav_ahir.jpg'")

    response = input("\nProceed? (yes/no): ").lower()

    if response not in ["yes", "y"]:
        print("Cancelled")
        return

    renamed_count = 0
    for image_path in image_files:
        new_name = generate_photo_filename(image_path.stem)
        new_path = IMAGES_DIR / new_name

        if image_path != new_path:
            try:
                os.rename(image_path, new_path)
                print(f"Renamed: {image_path.name} → {new_name}")
                renamed_count += 1
            except Exception as e:
                print(f"Error renaming {image_path.name}: {e}")

    print(f"\nRenamed {renamed_count} files")


def create_placeholder_images():
    """
    Create placeholder images for players without photos.

    Creates colored placeholder images with player initials.
    """
    if not PLAYERS_CSV_PATH.exists():
        print(f"Error: {PLAYERS_CSV_PATH} not found")
        return

    df = pd.read_csv(PLAYERS_CSV_PATH)
    created_count = 0

    colors = [
        "#FF6B6B",
        "#4ECDC4",
        "#45B7D1",
        "#FFA07A",
        "#98D8C8",
        "#F7DC6F",
        "#BB8FCE",
        "#85C1E2",
    ]

    print("Creating placeholder images...")
    print("-" * 50)

    for idx, row in df.iterrows():
        full_name = row["Full Name"]
        photo_filename = generate_photo_filename(full_name)
        photo_path = IMAGES_DIR / photo_filename

        if not photo_path.exists():
            # Create placeholder
            img = Image.new("RGB", (400, 400), color=colors[idx % len(colors)])
            draw = ImageDraw.Draw(img)

            # Get initials
            initials = "".join([word[0].upper() for word in full_name.split()])

            # Draw initials
            try:
                font = ImageFont.truetype("Arial.ttf", 120)
            except:
                font = ImageFont.load_default()

            # Calculate text position
            bbox = draw.textbbox((0, 0), initials, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = (400 - text_width) // 2
            y = (400 - text_height) // 2

            draw.text((x, y), initials, fill="white", font=font)

            img.save(photo_path)
            print(f"✅ Created: {photo_filename} ({initials})")
            created_count += 1
        else:
            print(f"⏭️  Exists: {photo_filename}")

    print(f"\nCreated {created_count} placeholder images")


def check_missing_photos():
    """Check which players are missing photos."""
    if not PLAYERS_CSV_PATH.exists():
        print(f"Error: {PLAYERS_CSV_PATH} not found")
        return

    df = pd.read_csv(PLAYERS_CSV_PATH)
    missing = []

    for _, row in df.iterrows():
        full_name = row["Full Name"]
        photo_filename = generate_photo_filename(full_name)
        photo_path = IMAGES_DIR / photo_filename

        if not photo_path.exists():
            missing.append((full_name, photo_filename))

    if missing:
        print(f"Missing photos for {len(missing)} players:")
        print("-" * 50)
        for name, filename in missing:
            print(f"❌ {name:30} → {filename}")
        print("\nOptions:")
        print("1. Add photos manually to images/ folder")
        print("2. Run create_placeholder_images() to generate placeholders")
    else:
        print("✅ All players have photos!")


def main():
    """Main utility menu."""
    print("=" * 60)
    print("🏏 Auction System - Utility Tools")
    print("=" * 60)
    print()
    print("Select an option:")
    print("1. List required photo filenames")
    print("2. Check for missing photos")
    print("3. Create placeholder images")
    print("4. Rename photos interactively")
    print("5. Exit")
    print()

    choice = input("Enter choice (1-5): ").strip()

    if choice == "1":
        list_required_photos()
    elif choice == "2":
        check_missing_photos()
    elif choice == "3":
        create_placeholder_images()
    elif choice == "4":
        rename_photos_interactive()
    elif choice == "5":
        print("Goodbye!")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
