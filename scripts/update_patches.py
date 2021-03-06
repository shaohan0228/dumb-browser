#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2020 ByTanuky
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import subprocess
import sys
import re

from ordered_set import OrderedSet

from constants import CHROMIUM_SRC_DIR, PATCHES_DIR, PATCH_LIST_FILE
from utils import get_patch_filename, get_original_filename

GIT_DIFF_PATTERN = 'diff --git '

EXCLUSION_FILES = [
    # locale resources
    'chrome/app/chromium_strings.grd',
    'chrome/app/settings_chromium_strings.grdp',
    'chrome/app/settings_strings.grdp',
    'components/components_chromium_strings.grd',
    # branding resources
    'chrome/app/theme/chromium/BRANDING',
]


def main(args):
    ret = subprocess.check_output(
        ['git', 'checkout'], cwd=CHROMIUM_SRC_DIR).decode('utf-8').split('\n')
    if len(ret) < 3:
        print('No diff available.')
        exit(0)

    ret = ret[:-3]
    total = len(ret)
    print('Updating files...')

    new_patch_list = OrderedSet()

    unified_diff = subprocess.check_output(
        ['git', 'diff', '--ignore-space-at-eol'],
        cwd=CHROMIUM_SRC_DIR
    ).decode('utf-8')

    splitted = unified_diff.split(GIT_DIFF_PATTERN)
    regex = re.compile('(?<=a/)(.*)(?= b/)')

    i = 0
    for entry in splitted:
        if len(entry) == 0:
            continue

        filename = regex.findall(entry)[0]

        if filename in EXCLUSION_FILES:
            total -= 1
            continue

        new_patch_list.add(filename)
        patch_filename = get_patch_filename(filename)

        print('[%d/%d]' % (i, total), filename)

        # write to file
        with open(os.path.join(PATCHES_DIR, patch_filename), 'w', newline='\n') as f:
            f.write(GIT_DIFF_PATTERN)
            f.write(entry)

        i += 1

    # remove old patches
    if os.path.exists(PATCH_LIST_FILE):
        print('Removing old patches...')

        removed_count = 0
        old_patches = os.listdir(PATCHES_DIR)
        for op in old_patches:
            if not op.endswith('.patch'):
                continue

            orig_filename = get_original_filename(op)
            if orig_filename not in new_patch_list:
                os.remove(os.path.join(PATCHES_DIR, op))
                removed_count += 1
        print('Removed %d unused patch(es).' % removed_count)

    print('Writing new patch list...')
    with open(PATCH_LIST_FILE, 'w') as f:
        f.writelines('\n'.join(new_patch_list))

    print('Patches updated.')

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
