import os
import argparse
import subprocess
from pdf2image import convert_from_path


def pdf_to_images_and_ocr(pdf_path, lang="eng", pages=1000):

    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]


    imgs_folder = os.path.join("imgs", pdf_name)
    parsed_folder = os.path.join("results", pdf_name, f"parse_{lang}")

    os.makedirs(imgs_folder, exist_ok=True)
    os.makedirs(parsed_folder, exist_ok=True)

    images = convert_from_path(pdf_path, first_page=1, last_page=pages)

    # Process each image with Tesseract OCR
    for i, image in enumerate(images):
        image_path = os.path.join(imgs_folder, f"page_{i+1}.png")
        image.save(image_path, "PNG")
        ocr_output_path = os.path.join(parsed_folder, f"page_{i+1}")

        subprocess.run(["tesseract", image_path, ocr_output_path, "-l", lang])

    print(
        f"Images are saved in {imgs_folder} and OCR results are saved in {parsed_folder}"
    )


# Set up argument parsing
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert each page of a PDF to an image and extract text using Tesseract OCR."
    )
    parser.add_argument("pdf_path", type=str, help="Path to the PDF file.")
    parser.add_argument(
        "-l",
        "--lang",
        type=str,
        default="eng",
        help="Language(s) for Tesseract OCR (default: eng).",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=1000,
        help="Maximum number of pages to process (default: 1000).",
    )

    args = parser.parse_args()

    pdf_to_images_and_ocr(args.pdf_path, args.lang, args.pages)
