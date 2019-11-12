#!/usr/bin/env python3

import urllib.request
import json
import re
import io
import tarfile
import os
import tempfile


def find_latest_release_urls():
    current_page=1
    last_page=1e10

    releases = []
    
    while True:
        releases_response = urllib.request.urlopen('https://api.github.com/repos/johnwason/robotraconteur_travisci_deploy/releases?page=%d' % current_page)
        link_header_text = releases_response.getheader('Link')
        link_last_match=re.search(r'page=(\d+)>;\s+rel="last"',link_header_text)
        if link_last_match is not None:
            last_page=int(link_last_match.group(1))

        releases_text = releases_response.read()
        releases_json = json.loads(releases_text)
        releases.extend(releases_json)
        
        if (current_page >= last_page):
            break

        current_page += 1

    latest_build_number = -1
    for r in releases:
        m = re.match(r"travisci build robotraconteur/robotraconteur (\d+)\.(\d+)", r["name"])
        if m is None:
            continue
        build_major = int(m.group(1))
        
        if (build_major > latest_build_number):
            latest_build_number = build_major

    print("Latest build: %d" % latest_build_number)

    release_urls = []
    for r in releases:
        m = re.match(r"travisci build robotraconteur/robotraconteur (\d+)\.(\d+)", r["name"])
        if m is None:
            continue
        if int(m.group(1)) != latest_build_number:
            continue
        for a in r["assets"]:
            if re.match(r"out\..+",a["name"]) is not None:
                release_urls.append((a["name"],a["url"]))

    return release_urls



def download_asset(asset_url):
    print("Retrieving release asset %s from url: %s" % (asset_url))
    req = urllib.request.Request(asset_url[1], headers={"Accept": "application/octet-stream"})
    response = urllib.request.urlopen(req)
    f = tempfile.TemporaryFile()
    f.write(response.read())
    f.seek(0)
    return f


asset_urls = find_latest_release_urls()
wheels = []
for url in asset_urls:
    temp_f = download_asset(url)    
    z = tarfile.open(fileobj=temp_f, mode="r:gz")
    for f in z.getmembers():
        if (f.name.endswith('.whl')):
            basename = os.path.basename(f.name)
            f.name=basename
            z.extract(f,'')
            wheels.append(basename)
        
print("Wheels downloaded: %s" % ', '.join(wheels))

print("Install using command 'pip install --user --force-reinstall <wheel_name>")
print("Use 'pip3' command for python3 on Ubuntu")
