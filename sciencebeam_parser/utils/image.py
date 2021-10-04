import PIL.Image


def get_image_with_max_resolution(
    image: PIL.Image.Image,
    max_resolution: int
) -> PIL.Image.Image:
    if max(image.width, image.height) <= max_resolution:
        return image
    if image.width > image.height:
        target_width = max_resolution
        target_height = max(1, round(image.height / image.width * target_width))
    else:
        target_height = max_resolution
        target_width = max(1, round(image.width / image.height * target_height))
    return image.resize((target_width, target_height))
