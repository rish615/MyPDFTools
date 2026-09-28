from PIL import Image

def images_to_pdf(image_paths, output_path):

    images=[]

    for path in image_paths:

        img=Image.open(path)

        if img.mode!="RGB":
            img=img.convert("RGB")

        images.append(img)

    first=images.pop(0)

    first.save(
        output_path,
        save_all=True,
        append_images=images
    )