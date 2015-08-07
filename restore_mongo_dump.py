#!/usr/bin/env python3
__author__ = 'Yuriy Chuhaienko'

import sys
from pathlib import Path
import subprocess
import time
import shutil


class Restorer:
    def __init__(self, db_name, extension_pattern='*gz'):
        self.db_name = db_name
        self.extension_pattern = extension_pattern
        self.cur_path = Path(sys.path[0])
        self.tmp_dir_name = 'tmp_dump'
        self.filelist = []
        self.file_choice = None
        self.dump_path = None

    def run(self):
        """ Main logic """
        if not self.db_name:
            self.print_usage('You did not tell database name for restore')

        try:
            self.filelist = self.getfilelist()
        except Exception as exc:
            self.print_usage('Cannot read dir content', '\n', exc)

        if len(self.filelist) == 0:
            self.print_usage('There are no archives at', self.cur_path)

        self.file_choice = self.get_path_choice(self.filelist)

        tmp_dump_path = None
        try:
            tmp_dump_path = self.extract_arch()
        except Exception as exc:
            self.print_usage('Cannot extract archive', str(self.file_choice), '\n', exc)

        db_path = None
        try:
            db_path = self.find_db(tmp_dump_path)
        except Exception:
            self.print_usage('Cannot find dump for {0} at archive {1}'.format(self.db_name, self.file_choice))

        try:
            self.restore_db(db_path)
        except Exception as exc:
            self.print_usage('Was errors during restoring\n', exc)

    def getfilelist(self):
        """ Get list of files from current directory with allowed extensions """
        self._print('Scanning current directory', str(self.cur_path), '...', sep=True)
        files = list(self.cur_path.glob(self.extension_pattern))
        files.sort(key=lambda v: v.stat().st_mtime)  # sort by create date
        return files

    def get_path_choice(self, path_list, only_name=True, show_data=True):
        """ Propose to user to choice one path from path_list. Return path user choose """
        self._print('{0} entities:'.format(len(path_list)))
        for i, file in enumerate(path_list):
            if show_data:
                ftime = time.strftime('%Y-%m-%d', time.localtime(file.stat().st_mtime))
                fsize = (file.stat().st_size / 1024 / 1024)
                self._print('  {0:>3}  {1} {2:>6.2f} MiB  {3}'.format(i, ftime, fsize, file.name if only_name else file))
            else:
                self._print('  {0:>3}  {1}'.format(i, file.name if only_name else file))
        inp = ''
        while True:
            inp = input('Please choose item to process [{0}]: '.format(i))
            if inp == '':
                inp = i
                break
            try:
                inp = int(inp)
                if 0 <= inp <= i:
                    break
                else:
                    self._print('Numbers from {0} to {1}'.format(0, i))
            except Exception:
                self._print('Only numbers!')
        self._print('You choose {0}'.format(path_list[inp]))
        return path_list[inp]

    def extract_arch(self):
        """ Extract archive to current directory / self.tmp_dir_name. Return path to dir """
        self._print('Extracting', self.file_choice,  '...', sep=True)
        tmp_dump_path = self.file_choice.parent / self.tmp_dir_name
        if tmp_dump_path.exists():
            if tmp_dump_path.is_dir():
                shutil.rmtree(str(tmp_dump_path))
            else:
                tmp_dump_path.unlink()
        shutil.unpack_archive(str(self.file_choice), str(tmp_dump_path))
        return tmp_dump_path

    def find_db(self, dir_path):
        """ Search DB dump files at dir_path """
        paths = list(set(path.parent.relative_to(dir_path) for path in dir_path.rglob('*.bson') if path.parent.name == self.db_name))
        dump_choice = self.get_path_choice(paths, only_name=False, show_data=False)
        return dir_path / dump_choice

    def restore_db(self, path):
        """ Restore db from dump is at path """
        self._print('Restoring', path, '...', sep=True)
        cmds = [
            'mongo ' + self.db_name + ' --eval "db.dropDatabase()"',
            'mongorestore --drop ' + str(path),
        ]
        self.run_commands(cmds)

    def run_commands(self, cmds):
        """ Helper for run shell commands """
        for cmd in cmds:
            try:
                self._print('RUNNING ', cmd, '...')
                subprocess.call(cmd, stderr=sys.__stdout__, shell=True)
            except subprocess.CalledProcessError:
                pass

    @staticmethod
    def _print(*args, sep=False):
        """ Helper for print """
        if sep:
            print('---   ---   ---')
        print(*args)

    @staticmethod
    def print_usage(*error_to_print):
        if error_to_print:
            print('\n', *error_to_print)
            print()
        print('Usage:')
        print(sys.argv[0], 'DB_NAME')
        print('where DB_NAME is name of MongoDB database to restore from archive\n')
        sys.exit(1)


if __name__ == '__main__':
    db_name = sys.argv[1] if 1 < len(sys.argv) else None
    obj = Restorer(db_name)
    obj.run()
    print('END')
