import binascii
from collections import OrderedDict
from datetime import datetime
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import urllib.request as urlreq
from zipfile import ZipFile


class UserError(Exception):
    pass


def detect_current_version(dir_with_sources):
    release_notes_file = dir_with_sources/'docs'/'user_manual'/'release_notes.md'
    current_version = None
    with open(release_notes_file) as f:
        for line in f:
            match = re.match(r'### taserver (v[^ ]*)\n', line)
            if match:
                current_version = match.group(1)
                break

    with open(dir_with_sources/'common'/'pendingcallbacks.py', 'rb') as f:
        windows_newlines = f.readline().endswith(b'\r\n')

    return windows_newlines, current_version


def get_available_releases():
    result = urlreq.urlopen('https://api.github.com/repos/Griffon26/taserver/releases')
    releases = json.load(result)
    release_tags_with_id = OrderedDict([(release['tag_name'], release['id']) for release in releases])
    return release_tags_with_id


release_cache = {}
def get_and_cache_release_file_with_root(reftype, ref):
    if (reftype, ref) not in release_cache:
        result = urlreq.urlopen(f'https://api.github.com/repos/Griffon26/taserver/git/refs/{reftype}/{ref}')
        obj = json.load(result)
        tree_sha = obj['object']['sha']

        result = urlreq.urlopen(f'https://api.github.com/repos/Griffon26/taserver/git/trees/{tree_sha}?recursive=1')
        obj = json.load(result)
        paths = [item['path'] for item in obj['tree'] if item['type'] == 'blob']

        # https://github.com/Griffon26/taserver/archive/v2.3.1.zip
        result = urlreq.urlopen(f'https://github.com/Griffon26/taserver/archive/{ref}.zip')
        ref_suffix = ref if reftype == 'heads' else ref[1:]
        common_root = f'taserver-{ref_suffix}/'
        release_cache[(reftype, ref)] = (common_root, result.read())

    return release_cache[(reftype, ref)]



def get_file_crcs_for_release(reftype, ref):
    common_root, release_file_content = get_and_cache_release_file_with_root(reftype, ref)
    with ZipFile(io.BytesIO(release_file_content)) as release_zip:
        crcs = {Path(info.filename).relative_to(common_root): info.CRC for info in release_zip.infolist() if not info.is_dir()}

    return crcs


def calculate_crc(file_path, convert_newlines):
    with open(file_path, 'rb') as f:
        data = f.read()

    try:
        data.decode()
        is_text = True
    except UnicodeError:
        is_text = False

    if is_text and convert_newlines:
        data = data.replace(b'\r\n', b'\n')
    crc = binascii.crc32(data)

    return crc


def get_files_that_are_different(dir_with_sources, windows_newlines, file_crcs):
    files = [file_path for file_path, crc in file_crcs.items()
             if calculate_crc(dir_with_sources / file_path, windows_newlines) != file_crcs[file_path]]

    return files


def check_size_of_dir_to_backup(dir_with_sources):
    size = 0
    for root, dirs, files in os.walk(dir_with_sources):
        size += sum(os.path.getsize(Path(root)/f) for f in files)

    if size > 250 * 1024 * 1024:
        size_in_MB = int(size / (1024 * 1024))
        raise UserError(f'Refusing to upgrade because the size of the backup would be quite large ({size_in_MB} MB).\n'
                        'Did you install Tribes Ascend into the taserver directory?')


def make_backup_dir_name(dir_with_sources):
    dir_with_sources = dir_with_sources.resolve()
    parent_dir = dir_with_sources.parent
    dir_name = dir_with_sources.parts[-1]
    backup_dir_name = datetime.now().strftime(f'{dir_name}_backup_%Y-%m-%d_%H-%M-%S')
    return parent_dir/backup_dir_name


def check_that_backup_dir_does_not_exist(backup_dir):
    if backup_dir.exists():
        raise UserError(f'Backup dir {backup_dir} already exists. Aborting upgrade.')


def make_backup(dir_with_sources):
    check_size_of_dir_to_backup(dir_with_sources)
    backup_dir = make_backup_dir_name(dir_with_sources)
    check_that_backup_dir_does_not_exist(backup_dir)
    print(f'Backing up {dir_with_sources} to {backup_dir}...')
    shutil.copytree(dir_with_sources, backup_dir)
    print('Backup complete')


def extract_files_from_release(reftype, ref, files_to_extract, windows_newlines):
    print('Extracting files to be updated...')
    common_root, release_file_content = get_and_cache_release_file_with_root(reftype, ref)
    with ZipFile(io.BytesIO(release_file_content)) as release_zip:
        for filename in files_to_extract:
            print(f'  {filename}')
            with open(filename, 'wb') as f:
                data = release_zip.read((common_root / filename).as_posix())
                if windows_newlines:
                    data = data.replace(b'\n', b'\r\n')
                f.write(data)


def main():
    dir_with_sources = Path(__file__).parent
    windows_newlines, current_version = detect_current_version(dir_with_sources)
    print(f'It looks like your current version is: {current_version}')

    old_release_file_crcs = get_file_crcs_for_release('tags', current_version)
    files_that_differ_from_old_release = get_files_that_are_different(dir_with_sources, windows_newlines, old_release_file_crcs)
    print(f'The following files contain changes compared to version {current_version}:')
    for file_path in files_that_differ_from_old_release:
        print(f'  {file_path}')

    available_releases = get_available_releases()
    print(f'Which release do you want to switch to?')
    print(f"{1:>4}: master (warning: don't upgrade master unless you need to, because it will break downgrading)")
    for i, available_version in enumerate(available_releases):
        print(f'{i + 2:>4}: {available_version}')
    release_index = -1
    while release_index not in range(len(available_releases) + 2):
        response = input('Please make your choice (leave empty to exit): ')
        try:
            release_index = 0 if response == '' else int(response)
        except ValueError:
            pass

    if release_index == 0:
        return
    elif release_index == 1:
        reftype = 'heads'
        selected_release = 'master'
    else:
        reftype = 'tags'
        selected_release = list(available_releases.keys())[release_index - 2]
    print(f'Selected release: {selected_release}')
    new_release_file_crcs = get_file_crcs_for_release(reftype, selected_release)

    files_that_differ_between_releases = {filename: crc for filename, crc in new_release_file_crcs.items()
                                          if (filename in old_release_file_crcs and
                                              old_release_file_crcs[filename] != new_release_file_crcs[filename]) or
                                             (filename not in old_release_file_crcs)}

    files_that_are_not_already_up_to_date = get_files_that_are_different(dir_with_sources, windows_newlines, files_that_differ_between_releases)

    if files_that_are_not_already_up_to_date:
        make_backup(dir_with_sources)
        extract_files_from_release(reftype, selected_release, files_that_are_not_already_up_to_date, windows_newlines)

        conflicting_files = set(files_that_differ_from_old_release).intersection(files_that_are_not_already_up_to_date)
        if conflicting_files:
            print('Manually changed files that were overwritten (you can find their originals in the backup dir):')
            for file_path in conflicting_files:
                print(f'  {file_path}')
            print('Please apply your changes again to these files if applicable.')
        else:
            print('No manually changed files were overwritten')
    else:
        print(f"You're already up-to-date with release {selected_release}")

    print('Update complete')


if __name__ == '__main__':
    try:
        main()
    except UserError as e:
        print(f'ERROR: {e}', file=sys.stderr)
