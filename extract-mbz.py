#!/usr/bin/python3
# COLGATE - DWheeler - WheelerDA @ GitHub
# 2014-07-18 - Initial release 0.5 Alpha minus
# 2024 - Ported to Python 3

###########################################################################
##                                                                       ##
## Moodle .mbz Extract Utility
##                                                                       ##
## python 3 compatible version                                           ##
##                                                                       ##
###########################################################################
##                                                                       ##
## NOTICE OF COPYRIGHT                                                   ##
##                                                                       ##
## This program is free software; you can redistribute it and/or modify  ##
## it under the terms of the GNU General Public License as published by  ##
## the Free Software Foundation; either version 3 of the License, or     ##
## (at your option) any later version.                                   ##
##                                                                       ##
## This program is distributed in the hope that it will be useful,       ##
## but WITHOUT ANY WARRANTY; without even the implied warranty of        ##
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         ##
## GNU General Public License for more details:                          ##
##                                                                       ##
##          http://www.gnu.org/copyleft/gpl.html                         ##
##                                                                       ##
###########################################################################

import xml.etree.ElementTree as etree
import fnmatch
import shutil
import os
import re
import datetime
import time
import sys
from slugify import slugify
import zipfile
import tarfile

# Functions ###########################################################################

def locate(pattern, root=os.curdir):
    '''Locate all files matching supplied filename pattern in and below
    supplied root directory.'''
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files, pattern):
            yield os.path.join(path, filename)


def createOutputDirectories(destinationRoot):
    if os.path.exists(destinationRoot):
        print("\n$$$$ Directory " + sourceDir + " (" + destinationRoot + ") already exists! Overwriting existing files\n")
    else:
        os.mkdir(destinationRoot)

    for subdir in ("user", "assignment", "resource", "forum", "legacy", "course"):
        if not os.path.exists(os.path.join(destinationRoot, subdir)):
            os.mkdir(os.path.join(destinationRoot, subdir))


def initializeLogfile(logfileName):
    logFileSpec = os.path.join(destinationRoot, logfileName)

    global logfile
    logfile = open(logFileSpec, "w", encoding="utf-8")
    if logfile.mode == 'w':
        logfile.write("Moodle Extract\n")
        logfile.write("Course: " + shortname + " (" + fullname + ")\n")
        logfile.write(" Format: " + format + "\n")
        logfile.write(" Sections: " + topics + "\n")
        logfile.write("Extract started: " + timeStamp + "\n")
        logfile.write("------------------------\n")
        print("Extract Log File: {0}".format(logFileSpec))
    else:
        print("Error: unable to open {0} for writing".format(logFileSpec))


def add_unique_postfix(fn):
    if not os.path.exists(fn):
        return fn

    path, name = os.path.split(fn)
    name, ext = os.path.splitext(name)

    make_fn = lambda i: os.path.join(path, '%s(%d)%s' % (name, i, ext))

    for i in range(2, sys.maxsize):
        uni_fn = make_fn(i)
        if not os.path.exists(uni_fn):
            return uni_fn

    return None


def make_slugified_filename(filename):
    path, name = os.path.split(filename)
    name, ext = os.path.splitext(filename)
    return os.path.join(path, "%s%s" % (slugify(str(name)), ext))


def unzip_mbz_file(mbz_filepath):
    base_dir = os.path.dirname(mbz_filepath)
    mbz_filename, extension = os.path.splitext(os.path.basename(mbz_filepath))
    unzip_folder = mbz_filename
    i = 1
    while unzip_folder in os.listdir(base_dir):
        unzip_folder = "%s_%d" % (mbz_filename, i)
        i += 1

    fullpath_to_unzip_dir = os.path.join(base_dir, unzip_folder)
    if not os.path.exists(fullpath_to_unzip_dir):
        os.mkdir(fullpath_to_unzip_dir)

    with open(mbz_filepath, 'rb') as f:
        header = f.read(4)

    if header[:2] == b'PK':
        with zipfile.ZipFile(mbz_filepath, 'r') as myzip:
            myzip.extractall(fullpath_to_unzip_dir)

    elif header[:2] == b'\x1f\x8b':
        tar = tarfile.open(mbz_filepath)
        tar.extractall(path=fullpath_to_unzip_dir)
        tar.close()

    else:
        print("Can't figure out what type of archive file this is")
        return -1

    return fullpath_to_unzip_dir


# /Functions ###########################################################################

print("\n##################\nextract-mbz.py\nextract moodle content from mbz backup (python v3)\n")
pipe = "|"
nl = "\n"
nArgs = len(sys.argv)
conflicted = 0

if nArgs < 2:
    print("usage: extract <path to Moodle backup mbz file> \n")
    sys.exit()

if sys.argv[1] == '?':
    print("help:")
    print("\tusage: extract <path to Moodle backup mbz file>")
    print("\n\tcurrent objects extracted: Files, URLs")
    print("\tcurrent file types extracted: pdf|png|gif|zip|rtf|sav|mp3|mht|por|xlsx?|docx?|pptx?\n")
    sys.exit()

mbz_filepath = str(sys.argv[1])

if not os.path.exists(mbz_filepath):
    print("\nERROR: " + mbz_filepath + " does not appear to exist\n")
    sys.exit()

source = unzip_mbz_file(mbz_filepath)
sourceDir = source

if not os.path.exists(os.path.join(source, 'course', 'course.xml')):
    print("\nERROR: " + source + " does not appear to contain unzipped mbz contents (couldn't locate course.xml)\n")
    sys.exit()

if not os.path.exists(os.path.join(source, 'moodle_backup.xml')):
    print("\nERROR: " + source + " does not appear to contain unzipped mbz contents (couldn't locate moodle_backup.xml)\n")
    sys.exit()


pattern = re.compile(r'^\s*(.+\.(?:pdf|png|gif|jpg|jpeg|zip|rtf|sav|mp3|mht|por|xlsx?|docx?|pptx?))\s*$', flags=re.IGNORECASE)

# Get Course Info
courseTree = etree.parse(os.path.join(source, 'course', 'course.xml'))
shortname = courseTree.getroot().find('shortname').text
fullname = courseTree.getroot().find('fullname').text
crn = courseTree.getroot().find('idnumber').text
format = courseTree.getroot().find('format').text
topics = courseTree.getroot().find('numsections').text

destinationRoot = os.path.join(str(source), slugify(str(shortname)))
createOutputDirectories(destinationRoot)

# Copy HTML support files to extracted folder
script_dir = os.path.dirname(os.path.realpath(__file__))
shutil.copy(os.path.join(script_dir, "tachyons.css"), destinationRoot)

# Get Moodle backup file info
backupTree = etree.parse(os.path.join(source, 'moodle_backup.xml'))
backupTreeRoot = backupTree.getroot()
activities = backupTreeRoot.find("information").find("contents").find("activities")

ts = time.time()
timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d-%H%M')
timeStampSeconds = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d-%H%M-%S')

print("Extracting backup of " + shortname + " @ " + timeStamp + " to " + destinationRoot + "\n")

initializeLogfile("extract_log.txt")

html_header = '''
<head>
    <title>Moodle Backup Extract</title>
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
    <link rel="stylesheet" type="text/css" href="tachyons.css">
</head>'''


##########################
# Process each section
webFilename = "%s.html" % slugify(str(shortname))
webFileSpec = os.path.join(destinationRoot, webFilename)

urlfile = open(webFileSpec, "w", encoding="utf-8")
if urlfile.mode == 'w':
    urlfile.write("<html>%s<body><blockquote>" % html_header)
    urlfile.write("<h3>Moodle Backup Extract..." + timeStamp + "</h3>")
    urlfile.write("<h2 class='man'>%s</h2><h4 class='man'>%s</h4>" % (fullname, shortname))
    logfile.write("\n============\nCourse Sections\n=============\n")
    print("Course Sections: {0}".format(webFileSpec))
else:
    print("Error: unable to open {0} for writing".format(webFileSpec))

print("===\nProcessing course sections...")

itemCount = 0

for s in backupTreeRoot.findall("./information/contents/sections")[0].findall("section"):

    section_title = s.find("title").text
    print("\nNow processing section id: %s (%s)" % (s.find("sectionid").text, section_title))

    if section_title == str(itemCount):
        if itemCount == 0:
            section_title = "Section Header"
        else:
            section_title = "Section %s" % section_title

    HTMLOutput = "<h2 class='mbn'>%s</h2>" % section_title

    section_file_root = etree.parse(os.path.join(source, s.find("directory").text, "section.xml"))
    section_summary = section_file_root.find("summary").text
    if section_summary:
        section_summary = section_summary.replace("@@PLUGINFILE@@", "./course")
        HTMLOutput += "<p>%s</p>" % section_summary
    HTMLOutput += "<ul class='man'>"

    if section_file_root.find("sequence").text:
        section_sequence = section_file_root.find("sequence").text.split(',')
    else:
        section_sequence = []

    section_file_dir = os.path.join(destinationRoot, "section_%03d" % itemCount)

    for item in section_sequence:
        item_xpath = ".//*[moduleid='%s']" % item

        try:
            item_title = activities.find(item_xpath).find("title").text
            modulename = activities.find(item_xpath).find("modulename").text
        except Exception:
            continue

        print("Found %s (item #: %s) titled %s" % (modulename, item, item_title))

        if modulename == "resource":
            resourceTree = etree.parse(os.path.join(source, 'activities', 'resource_%s' % item, 'inforef.xml'))
            file_listing = resourceTree.findall("fileref/file")
            files = etree.parse(os.path.join(source, 'files.xml'))

            for f in file_listing:
                file_id = f.find("id").text
                filename = files.find("file[@id='%s']/filename" % file_id).text

                if filename != "." and filename != "":
                    if not os.path.exists(section_file_dir):
                        os.makedirs(section_file_dir)
                    filename = make_slugified_filename(str(filename))
                    contenthash = files.find("file[@id='%s']/contenthash" % file_id).text

                    destination = add_unique_postfix(os.path.join(section_file_dir, filename))
                    file = os.path.join(source, "files", contenthash[:2], contenthash)

                    shutil.copyfile(file, destination)

                    file_url = "./section_%03d/%s" % (itemCount, filename)
                    item_title = "<a href='%s'>%s</a>" % (file_url, item_title)

        elif modulename == "url":
            urlTree = etree.parse(os.path.join(source, 'activities', 'url_%s' % item, 'url.xml'))
            url = urlTree.find("url/externalurl").text
            print("Url id %s" % url)
            item_title = "<a href='%s' target='_blank'>%s</a>" % (url, item_title)

        elif modulename == "page":
            page_title = activities.find(item_xpath).find("title").text
            page_xml_file = activities.find(item_xpath).find("directory").text

            page_tree = etree.parse(os.path.join(source, page_xml_file, 'page.xml'))
            page_content = page_tree.find("page/content").text

            if not os.path.exists(section_file_dir):
                os.makedirs(section_file_dir)

            page_title = page_title.replace("/", "-")
            pageFilename = make_slugified_filename("%s.html" % str(page_title))
            pageFilePath = os.path.join(section_file_dir, pageFilename)
            pageFilePath = add_unique_postfix(pageFilePath)

            pagefile = open(pageFilePath, "w", encoding="utf-8")
            if pagefile.mode == 'w':
                pagefile.write("<html>%s<body><blockquote>" % html_header)
                pagefile.write("<h2>%s (%s)</h2>" % (fullname, shortname))
                pagefile.write("<h1>%s</h1>" % page_title)
                pagefile.write(page_content)
                pagefile.close()

            page_url = "./section_%03d/%s" % (itemCount, pageFilename)
            item_title = "<a href='%s'>%s</a>" % (page_url, page_title)

        elif modulename == "folder":
            folder_title = activities.find(item_xpath).find("title").text
            folder_xml_file = activities.find(item_xpath).find("directory").text

            folder_tree = etree.parse(os.path.join(source, folder_xml_file, 'folder.xml'))
            folder_desc = folder_tree.find("folder/intro").text

            resourceTree = etree.parse(os.path.join(source, folder_xml_file, 'inforef.xml'))
            file_listing = resourceTree.findall("fileref/file")
            files = etree.parse(os.path.join(source, 'files.xml'))

            folder_html = "<div><ul>"
            for f in file_listing:
                file_id = f.find("id").text
                original_filename = files.find("file[@id='%s']/filename" % file_id).text

                if original_filename != "." and original_filename != "":
                    if not os.path.exists(section_file_dir):
                        os.makedirs(section_file_dir)
                    filename = make_slugified_filename(original_filename)
                    contenthash = files.find("file[@id='%s']/contenthash" % file_id).text

                    destination = add_unique_postfix(os.path.join(section_file_dir, filename))
                    file = os.path.join(source, "files", contenthash[:2], contenthash)

                    shutil.copyfile(file, destination)

                    file_url = "./section_%03d/%s" % (itemCount, filename)
                    folder_html += "<li><a href='%s'>%s</a></li>" % (file_url, original_filename)

            folder_html += "</ul></div>"
            item_title = "%s (folder)%s" % (folder_title, folder_html)

        else:
            item_title += " (%s)" % modulename

        HTMLOutput += "<li>%s</li>" % item_title

    logOutput = section_title + nl
    HTMLOutput += "</ul>"

    urlfile.write(HTMLOutput)
    logfile.write(logOutput)
    itemCount += 1

if itemCount == 0:
    urlfile.write("<p>No sections found!</p>")
    print("No sections found!")

logfile.write("Extracted sections = {0}".format(itemCount))
urlfile.close()


# #########################
# Process Course Files

fileTree = etree.parse(os.path.join(source, 'files.xml'))
root = fileTree.getroot()

itemCount = 0
print("\nProcessing Course Files...")
logfile.write("\n============\nCourse Files\n=============\n")

for rsrc in root:
    fhash = rsrc.find('contenthash').text
    fname = rsrc.find('filename').text
    fcontext = rsrc.find('component').text

    logfile.write("{0} -- {1} -- {2}\n".format(fname, fhash, fcontext))
    hit = pattern.search(fname)

    if hit:
        itemCount += 1
        files = list(locate(fhash, source))
        logfile.write("|FILES\n")

        if fcontext == "user":
            destination = os.path.join(destinationRoot, "user")
        elif fcontext in ("mod_resource", "mod_folder"):
            destination = os.path.join(destinationRoot, "resource")
        elif fcontext == "legacy":
            destination = os.path.join(destinationRoot, "legacy")
        elif fcontext in ("mod_assignment", "assignsubmission_file"):
            destination = os.path.join(destinationRoot, "assignment")
        elif fcontext == "mod_forum":
            destination = os.path.join(destinationRoot, "forum")
        elif fcontext == "course":
            destination = os.path.join(destinationRoot, "course")
        else:
            destination = destinationRoot

        for x in files:
            if os.path.exists(os.path.join(destination, fname)):
                print(" $$$$ File conflict!!!!! " + destination + fname)
                conflicted += 1
                shutil.copyfile(x, os.path.join(destination, fname + "-" + str(conflicted)))
            else:
                shutil.copyfile(x, os.path.join(destination, fname))
    else:
        logfile.write("NO FILES|\n")

print("Extracted files = {0}".format(itemCount))
logfile.write("\nExtracted files = {0}\n".format(itemCount))

urlfile.close()
logfile.close()

# sym link
symLink = shortname.lower() + "-" + timeStampSeconds

if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
    print("Creating symlink for *nix systems...")
    if os.path.exists(symLink):
        print("symlink " + symLink + " already exists! CHECK!\n")
    else:
        print("Creating symlink " + symLink + " -> " + destinationRoot)
        os.symlink(destinationRoot, symLink)

# clean up (remove) subdirectories not used
for subdir in ("forum", "legacy", "assignment", "user", "resource", "course"):
    if not os.listdir(os.path.join(destinationRoot, subdir)):
        os.rmdir(os.path.join(destinationRoot, subdir))
