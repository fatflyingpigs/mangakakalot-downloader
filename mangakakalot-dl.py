import requests
from bs4 import BeautifulSoup

try:
    from PIL import Image
except:
    pass

import os
import re
from datetime import datetime, timezone

DIRCLEANER1 = re.compile("[^\w\-_\. \&]")
DIRCLEANER2 = re.compile("\s*\:\s*")

SKIP_EXISTING = True
SAVE_ID = True
MAKE_CHAPTER_PDF = True


def clean_directory_name(path):
    path = DIRCLEANER2.sub(" - ", path)
    return DIRCLEANER1.sub("_", path)


def download_chapter(title, chapter):
    a_tag = chapter.find("a")
    chapter_link = a_tag.get("href")
    chapter_title_long = a_tag.get("title")
    chapter_title = a_tag.text
    print(f"{title} -- {chapter_title_long} -- {chapter_title} -- {chapter_link}")
    path = os.path.join(title, clean_directory_name(chapter_title))

    result = requests.get(chapter_link)
    result.raise_for_status()
    page_html = result.text
    soup = BeautifulSoup(page_html, "html.parser")

    if not os.path.exists(path):
        os.mkdir(path)

    # print(soup.prettify())

    img_list = soup.find(
        "div", {"class": "vung-doc", "id": "vungdoc"}
    )  # <div class="vung-doc" id="vungdoc">
    made_files = []
    for img in img_list.find_all("img"):
        img_link = img.get("src")
        img_title = img.get("title", "").strip(" - Mangakakalot.com")
        _, extension = os.path.splitext(img_link)

        img_file_path = clean_directory_name(img_title + extension)
        img_path = os.path.join(path, img_file_path)

        if SKIP_EXISTING and os.path.isfile(img_path):
            print(f"The page {img_title} exists as file {img_path} - SKIPPING")
            made_files.append(img_path)
            continue

        try:
            result = requests.get(img_link)
            result.raise_for_status()
        except:
            print(f"Failed to fetch '{img_title}' from '{img_link}'")

        data = result.content

        with open(img_path, "wb") as img_file:
            img_file.write(data)
        made_files.append(img_path)
        print(f"Downloaded {img_title} from {img_link} and saved as {img_path}")
    if MAKE_CHAPTER_PDF and made_files:
        print("")
        print("Attempting to make chapter PDF")
        try:
            files = [Image.open(file).convert("RGB") for file in made_files]
            pdf_path = os.path.join(path, clean_directory_name(chapter_title) + ".pdf")
            files[0].save(
                pdf_path, save_all=True, append_images=files[1:], resolution=100
            )
            print(f"Made chapter PDF ({len(files)} images)")
            print("")
        except Exception as e:
            print(e)
            print("Failed to make chapter PDF")
            print("")


def download_manga(link):

    # Fix up link options, either the full URL or the manga id
    if link.startswith("mangakakalot.com"):
        link = "https://" + link
    if not link.startswith("https://mangakakalot.com/manga"):
        link = "https://mangakakalot.com/manga/" + link.strip("/")

    result = requests.get(link)
    result.raise_for_status()
    page_html = result.text

    # print(page_html)

    soup = BeautifulSoup(page_html, "html.parser")

    # print(soup.prettify())

    # Might be hacky ?
    title = soup.find_all("span", {"itemprop": "title"})[-1].text
    title = clean_directory_name(title)

    if not os.path.exists(title):
        os.mkdir(title)

    if SAVE_ID:
        data = f"""# {title}
Downloaded from: {link}
Last run: {datetime.now(timezone.utc)}

--- DO NOT EDIT ANYTHING ABOVE THIS LINE (you may delete this line itself) ---
"""
        with open(os.path.join(title, "README.mkdl.md"), "w") as readme:
            readme.write(data)

    print(f"Downloading title '{title}'")
    chapter_list = soup.find("div", {"class": "chapter-list"}).find_all(
        "div", {"class": "row"}
    )[::-1]
    for chapter in chapter_list:
        download_chapter(title, chapter)


if __name__ == "__main__":
    import argparse

    argparser = argparse.ArgumentParser(
        "Mangakakalot downloader",
        description="Example usage './mangakakalot-dl.py tifr98811554781969'",
    )

    argparser.add_argument(
        "--redownload",
        help="Download the image even if the file seem to exist on disk",
        default=False,
        action="store_true",
    )
    argparser.add_argument(
        "--no-save-id",
        help="Do NOT save a .txt file in the root directory to resume this at a later stage",
        default=False,
        action="store_true",
    )
    argparser.add_argument(
        "--path",
        help="Set the pat explicitly, defaults to current working directory",
        default=os.getcwd(),
    )
    argparser.add_argument(
        "--make-pdf",
        help="Make a PDF for each chapter (Requires Pillow)",
        default=False,
        action="store_true",
    )

    cparsers = argparser.add_subparsers(help="Commands available")

    cparser = cparsers.add_parser("download")
    cparser.set_defaults(command="download")
    cparser.add_argument(
        "MANGA_ID", help="The mangakakalot manga id (or just the whole url)", nargs="+"
    )

    cparser = cparsers.add_parser("resume-all")
    cparser.set_defaults(command="resume-all")

    cparser = cparsers.add_parser("download-list")
    cparser.set_defaults(command="download-list")
    cparser.add_argument(
        "LIST",
        help="The file containing newline delimited mangakakalot manga ids (or just the whole url)",
    )

    args = argparser.parse_args()

    oldcwd = os.getcwd()
    os.chdir(os.path.abspath(args.path))
    newcwd = os.getcwd()

    SKIP_EXISTING = not args.redownload
    SAVE_ID = not args.no_save_id
    MAKE_CHAPTER_PDF = args.make_pdf

    if args.command == "download":
        for manga_id in args.MANGA_ID:
            try:
                download_manga(manga_id)
            except Exception as e:
                print(e)
                print(f"Failed to download manga '{manga_id}'")
            print(" ---- ")

    elif args.command == "download-list":
        os.chdir(oldcwd)
        with open(args.LIST, "r") as mangalist:
            mangas = [line.strip() for line in mangalist.readlines()]
        os.chdir(newcwd)
        for manga_id in mangas:
            try:
                download_manga(manga_id)
            except Exception as e:
                print(e)
                print(f"Failed to download manga '{manga_id}'")
            print(" ---- ")

    elif args.command == "resume-all":
        for dir_ in os.listdir():
            if not os.path.isdir(dir_):
                continue
            readme_path = os.path.join(dir_, "README.mkdl.md")
            if os.path.isfile(readme_path):
                with open(readme_path, "r") as readme_file:
                    title = readme_file.readline().strip()
                    title = title[title.find("# ") + 2 :]
                    url = readme_file.readline().strip()
                    url = url[url.find("https://") :]
                    print(
                        f"Found manga that can be resumed: '{title}' -- using url: {url}"
                    )
                try:
                    download_manga(url)
                except Exception as e:
                    print(e)
                    print(f"Failed to download manga '{url}'")
                print(" ---- ")
    else:
        argparser.print_help()
