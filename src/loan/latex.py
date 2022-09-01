
import datetime
import glob
import logging
import os
from pathlib import Path
import shutil
import subprocess

from .utility import (
    Config,
    parse_date
)

log = logging.getLogger('latex')
log.setLevel('INFO')


def compile_latex(user, date):
    """
    Compile LaTeX to generate pdf statement
    """
    latex_path = Config.PATH / 'latex'
    target_path = Config.TARGET_PATH / user.capitalize()
    target_path.mkdir(parents=True, exist_ok=True)
    file_name = parse_date(date).strftime('%Y_%m_%d.pdf')

    with subprocess.Popen(
        ["pdflatex", "main.tex"], stdout=subprocess.PIPE, universal_newlines=True, cwd=latex_path
    ) as process:
        while True:
            output = process.stdout.readline()
            log.debug(output.strip())
            # Check for process completion
            return_code = process.poll()
            if return_code is not None:
                log.info(f'Latex return code {return_code}.')
                # Process has finished, read rest of the output
                for output in process.stdout.readlines():
                    log.debug(output.strip())
                break
    dest = target_path / file_name
    process = subprocess.run(["mv", "main.pdf", str(dest)], cwd=latex_path, check=True)
    log.info(f'New statements {file_name} in {target_path}')
    clean_latex(latex_path)


def clean_latex(main_path):
    """Cleat latex auxilliary files"""

    def remove(path_list):
        for path in path_list:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

    remove(glob.glob(str(main_path / "*.aux")))
    remove(glob.glob(str(main_path / "auto")))
    remove(glob.glob(str(main_path / "*.fdb_latexmk")))
    remove(glob.glob(str(main_path / "*.fls")))
    remove(glob.glob(str(main_path / "main.log")))
    remove(glob.glob(str(main_path / "*.out")))
    remove(glob.glob(str(main_path / ".pdf-view-restore")))
    remove(glob.glob(str(main_path / "macro.tex")))
    remove(glob.glob(str(main_path / "array.tex")))
    log.info('Latex file have been cleaned.')


def parse_latex_date(start_date, stop_date):
    stop_date = parse_date(stop_date)
    if start_date is None:
        if stop_date.day == 1:
            if stop_date.month == 1:
               start_date = datetime.date(stop_date.year - 1, 12, 1)
            else:
               start_date = datetime.date(stop_date.year, stop_date.month - 1, 1)
        else:
            start_date = datetime.date(stop_date.year, stop_date.month, 1)
    else:
        start_date = parse_date(start_date)
    return start_date, stop_date