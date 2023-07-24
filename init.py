import subprocess
import sys
import settings
import importlib
from wakutils import setupJson


def	init():
	install_requirements()
	settings.initGlobal()
	setupJson()


def install_requirements():
	try:
		file_path = "requirements.txt"
		with open(file_path, 'r') as file:
			requirements = [line.strip() for line in file]
		for depedency in requirements:
			try:
				importlib.import_module(depedency)
			except ImportError:
				subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", file_path])
	except subprocess.CalledProcessError as e:
		print("Erreur lors de l'installation des dépendances.")
		sys.exit(1)
