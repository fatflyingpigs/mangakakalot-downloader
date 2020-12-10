#!/usr/bin/env python3
import requests
import shutil
import traceback
from bs4 import BeautifulSoup

try:
	from PIL import Image
except:
	pass

import os
import re
from datetime import datetime, timezone
import time

DIRCLEANER1 = re.compile(r"[^\w\-_ .&]")
DIRCLEANER2 = re.compile(r"\s*:\s*")
DIRCLEANER3 = re.compile(r"^\.")
DIRCLEANER4 = re.compile(r"(\.| - )$")

TRACEBACK = True
SKIP_EXISTING = True
SKIP_EXISTING_CHAPTERS = False
SAVE_ID = True
MAKE_CHAPTER_PDF = True
MAKE_CHAPTER_CBZ = True


def clean_directory_name(path):
	path = DIRCLEANER2.sub(" - ", path)
	path = DIRCLEANER1.sub("_", path)
	path = DIRCLEANER3.sub("_", path)
	path = DIRCLEANER4.sub("", path)
	return path


def get_image_from_link(img_link, headers):
	try:
		backoff = [1, 2, 4, 8]
		boff_i = 0
		while True:
			result = requests.get(img_link, headers=headers)
			if boff_i < len(backoff) and not result.status_code == 200:
				print(
					"Bad status code: {status_code} retrying in {retry_in}".format(
						status_code=result.status_code, retry_in=backoff[boff_i]
					)
				)
				time.sleep(backoff[boff_i])
				boff_i += (
					1
				)  # Eventually throws an index out of bounds exception, so we get out of this look
			else:
				result.raise_for_status()
				return result
	except:
		return None

def to_PDF(jpeg_image_folder):
	if MAKE_CHAPTER_PDF:
		print("\nAttempting to make chapter PDF")
		try:
			made_files = [os.path.join(jpeg_image_folder, file) for file in os.listdir(jpeg_image_folder)]
			files = [Image.open(file).convert("RGB") for file in made_files]
			pdf_path = jpeg_image_folder + ".pdf"
			files[0].save(
				pdf_path, save_all=True, append_images=files[1:], resolution=100
			)
			print("Made chapter PDF ({} images)\n".format(len(files)))
		except Exception as e:
			print(e)
			if TRACEBACK:
				traceback.print_exc()
			print("Failed to make chapter PDF\n")

def to_CBZ(jpeg_image_folder):
	if MAKE_CHAPTER_CBZ:
		print("\nAttempting to make chapter CBZ")
		try:
			made_files = os.listdir(jpeg_image_folder)
			cbz_path = jpeg_image_folder + ".cbz"
			shutil.make_archive(cbz_path, 'zip', jpeg_image_folder)
			shutil.move(cbz_path + '.zip', cbz_path)
			print("Made chapter CBZ ({} images)\n".format(len(made_files)))
		except Exception as e:
			print(e)
			if TRACEBACK:
				traceback.print_exc()
			print("Failed to make chapter PDF\n")

def download_chapter(title, chapter):
	a_tag = chapter.find("a")
	chapter_link = a_tag.get("href")
	chapter_title_long = a_tag.get("title")
	chapter_title = a_tag.text
	print(
		"{title} -- {chapter_title_long} -- {chapter_title} -- {chapter_link}".format(
			title=title,
			chapter_title_long=chapter_title_long,
			chapter_title=chapter_title,
			chapter_link=chapter_link,
		)
	)
	path = os.path.join(title, clean_directory_name(chapter_title))

	proceed = False
	if SKIP_EXISTING_CHAPTERS:
		if MAKE_CHAPTER_PDF and not os.path.isfile(path + '.pdf'):
			proceed = True
		if MAKE_CHAPTER_CBZ and not os.path.isfile(path + '.cbz'):
			proceed = True
		if not MAKE_CHAPTER_PDF and not MAKE_CHAPTER_CBZ and not os.path.exists(path):
			proceed = True

	if not proceed:
		print(
			"Chapter '{chapter_title}' was already found - Skipping".format(
				chapter_title=chapter_title
			)
		)
		return

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
			print(
				"The page {img_title} exists as file {img_path} - SKIPPING".format(
					img_title=img_title, img_path=img_path
				)
			)
			made_files.append(img_path)
			continue

		result = get_image_from_link(img_link, {'referer': 'https://mangakakalot.com/'})
		if result is None:
			print(
				"Failed to fetch '{img_title}' from '{img_link}'".format(
					img_title=img_title, img_link=img_link
				)
			)
			continue

		data = result.content

		with open(img_path, "wb") as img_file:
			img_file.write(data)
		made_files.append(img_path)
		print(
			"Downloaded {img_title} from {img_link} and saved as {img_path}".format(
				img_title=img_title, img_link=img_link, img_path=img_path
			)
		)
	to_PDF(path)
	to_CBZ(path)
	if MAKE_CHAPTER_PDF or MAKE_CHAPTER_CBZ:
		shutil.rmtree(path)

def download_chapter_manganelo(title, chapter):
	a_tag = chapter.find("a")
	chapter_link = a_tag.get("href")
	chapter_title_long = a_tag.get("title")
	chapter_title = a_tag.text
	print(
		"{title} -- {chapter_title_long} -- {chapter_title} -- {chapter_link}".format(
			title=title,
			chapter_title_long=chapter_title_long,
			chapter_title=chapter_title,
			chapter_link=chapter_link,
		)
	)
	path = os.path.join(title, clean_directory_name(chapter_title))

	proceed = False
	if SKIP_EXISTING_CHAPTERS:
		if MAKE_CHAPTER_PDF and not os.path.isfile(path + '.pdf'):
			proceed = True
		if MAKE_CHAPTER_CBZ and not os.path.isfile(path + '.cbz'):
			proceed = True
		if not MAKE_CHAPTER_PDF and not MAKE_CHAPTER_CBZ and not os.path.exists(path):
			proceed = True

	if not proceed:
		print(
			"Chapter '{chapter_title}' was already found - Skipping".format(
				chapter_title=chapter_title
			)
		)
		return

	result = requests.get(chapter_link)
	result.raise_for_status()
	page_html = result.text
	soup = BeautifulSoup(page_html, "html.parser")

	if not os.path.exists(path):
		os.mkdir(path)

	# print(soup.prettify())

	img_list = soup.find(
		"div", {"class": "container-chapter-reader"}
	)  # <div class="vung-doc" id="vungdoc">
	made_files = []
	for img in img_list.find_all("img"):
		img_link = img.get("src")
		img_title = img.get("title", "").strip(" - MangaNelo.com")
		_, extension = os.path.splitext(img_link)

		img_file_path = clean_directory_name(img_title + extension)
		img_path = os.path.join(path, img_file_path)

		if SKIP_EXISTING and os.path.isfile(img_path):
			print(
				"The page {img_title} exists as file {img_path} - SKIPPING".format(
					img_title=img_title, img_path=img_path
				)
			)
			made_files.append(img_path)
			continue

		result = get_image_from_link(img_link, {'referer': 'https://manganelo.com/'})
		if result is None:
			print(
				"Failed to fetch '{img_title}' from '{img_link}'".format(
					img_title=img_title, img_link=img_link
				)
			)
			continue

		data = result.content

		with open(img_path, "wb") as img_file:
			img_file.write(data)
		made_files.append(img_path)
		print(
			"Downloaded {img_title} from {img_link} and saved as {img_path}".format(
				img_title=img_title, img_link=img_link, img_path=img_path
			)
		)
	to_PDF(path)
	to_CBZ(path)
	if MAKE_CHAPTER_PDF or MAKE_CHAPTER_CBZ:
		shutil.rmtree(path)

def download_manga_default(link):

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
		data = """# {title}
Downloaded from: {link}
Last run: {last_run}

--- DO NOT EDIT ANYTHING ABOVE THIS LINE (you may delete this line itself) ---
""".format(
			title=title, link=link, last_run=datetime.now(timezone.utc)
		)

		with open(os.path.join(title, "README.mkdl.md"), "w") as readme:
			readme.write(data)

	print("Downloading title '{title}'".format(title=title))
	chapter_list = soup.find("div", {"class": "chapter-list"}).find_all(
		"div", {"class": "row"}
	)[::-1]
	for chapter in chapter_list:
		download_chapter(title, chapter)


def download_manga_manganelo(link):
	# Fix up link options, either the full URL or the manga id
	if link.startswith("manganelo.com"):
		link = "https://" + link
	if not link.startswith("https://manganelo.com/manga"):
		link = "https://manganelo.com/manga/" + link.strip("/")

	result = requests.get(link)
	result.raise_for_status()
	page_html = result.text

	# print(page_html)

	soup = BeautifulSoup(page_html, "html.parser")

	# print(soup.prettify())

	# Might be hacky ?
	title = soup.find("div", {"class": "story-info-right"}).find("h1").text
	title = clean_directory_name(title)

	if not os.path.exists(title):
		os.mkdir(title)

	if SAVE_ID:
		data = """# {title}
Downloaded from: {link}
Last run: {last_run}

--- DO NOT EDIT ANYTHING ABOVE THIS LINE (you may delete this line itself) ---
""".format(
			title=title, link=link, last_run=datetime.now(timezone.utc)
		)

		with open(os.path.join(title, "README.mkdl.md"), "w") as readme:
			readme.write(data)

	print("Downloading title '{title}'".format(title=title))
	chapter_list = soup.find("ul", {"class": "row-content-chapter"}).find_all("li")[
		::-1
	]
	for chapter in chapter_list:
		download_chapter_manganelo(title, chapter)


def download_manga(link):
	if "manganelo.com" in link:
		return download_manga_manganelo(link)
	else:
		return download_manga_default(link)


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
		"--no-ignore-existing-chapters",
		help="Check every page of a chapter instead of skipping chapters where the directory already exist",
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
	argparser.add_argument(
		"--make-cbz",
		help="Make a CBZ for each chapter",
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
	SKIP_EXISTING_CHAPTERS = not args.no_ignore_existing_chapters
	SAVE_ID = not args.no_save_id
	MAKE_CHAPTER_PDF = args.make_pdf
	MAKE_CHAPTER_CBZ = args.make_cbz

	if args.command == "download":
		for manga_id in args.MANGA_ID:
			try:
				download_manga(manga_id)
			except Exception as e:
				print(e)
				if TRACEBACK:
					traceback.print_exc()
				print("Failed to download manga '{manga_id}'".format(manga_id=manga_id))
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
				if TRACEBACK:
					traceback.print_exc()
				print("Failed to download manga '{manga_id}'".format(manga_id=manga_id))
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
						"Found manga that can be resumed: '{title}' -- using url: {url}".format(
							title=title, url=url
						)
					)
				try:
					download_manga(url)
				except Exception as e:
					print(e)
					if TRACEBACK:
						traceback.print_exc()
					print("Failed to download manga '{url}'".format(url=url))
				print(" ---- ")
	else:
		argparser.print_help()