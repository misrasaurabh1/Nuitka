#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Python tests originally created or extracted from other peoples work. The
#     parts were too small to be protected.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
def localImporter1():
    import os

    return os

def localImporter1a():
    import os as my_os_name

    return my_os_name


def localImporter2():
    from os import path

    return path

def localImporter2a():
    from os import path as renamed

    return renamed

print "Direct module import", localImporter1()
print "Direct module import using rename", localImporter1a()

print "From module import", localImporter2()
print "From module import using rename", localImporter2a()

from os import *

print "Star import gave us", path

import os.path as myname

print "As import gave", myname

def localImportFailure():
    try:
        from os import path, lala, listdir
    except Exception as e:
        print type(e), repr(e)

    try:
        print listdir
    except UnboundLocalError:
        print " and listdir was not imported",

    print "but path was", path

print "From import that fails in the middle",
localImportFailure()

def nonPackageImportFailure():
    try:
        # Not allowed without being a package, should raise ValueError
        from . import whatever
    except Exception as e:
        print type(e), repr(e)

print "Package import fails in non-package:",
nonPackageImportFailure()
