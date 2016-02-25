import requests
import json
import plistlib
import datetime

from urllib.parse import urlencode
from lxml import etree


def searchSongs(term):
    query = urlencode({"term": term, "entity": "musicTrack", "media": "music"})
    resp = requests.get("https://itunes.apple.com/search?{}".format(query))
    results = json.loads(resp.text)
    return list(filter(lambda res: res["kind"] == "song", results["results"]))

def buildPlist(playlistName, songs):
    tracks = {}
    track_id = 10000
    for song in songs:
        tracks[str(track_id)] = {
                "Track ID": track_id,
                "Artist": song["artistName"],
                "Album": song["collectionName"],
                "Disc Number": song["discNumber"],
                "Name": song["trackName"],
                "Play Count": 0,
			    "Purchased": True,
                "Sort Album": song["collectionName"],
                "Sort Artist": song["artistName"],
                "Sort Name": song["trackName"],
                "Track Number": 9,
                "Track Type": "Remote",
        }
        track_id += 2

    playlistItems = [{"Track ID": track["Track ID"]}
                     for (_, track) in tracks.items()]

    pl = {
        "Application Version": "12.3.2.35",
        "Date": datetime.datetime.now(),
        "Features": "5",
        "Major Version": "1",
        "Minor Version": "1",
        "Show Content Ratings": True,
        "Tracks": tracks,
        "Playlists": [{
            "All Items": True,
            "Description": "",
            "Name": playlistName,
            "Playlist ID": 100001,
            "Playlist Items": playlistItems,
        }],
    }
    plistStr = plistlib.dumps(pl)

    # Here comes the tricky and dirty part: we need to manipulate the xml nodes
    # order manually to make the "Playlist" come after "Tracks".
    plist = etree.fromstring(plistStr)
    parent = plist.getchildren()[0]
    children = plist.getchildren()[0].getchildren()

    for i in range(len(children)):
        if children[i].text == "Playlists":
            playlistKey = children[i]
            playlistArr = children[i+1]
            parent.remove(playlistKey)
            parent.remove(playlistArr)
            parent.append(playlistKey)
            parent.append(playlistArr)
            break

    return etree.tostring(
        plist, pretty_print=True, encoding="UTF-8", xml_declaration=True,
        doctype='<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
    ).decode("utf-8")

def sanitize(songName):
    return songName

def selectSong(songs):
    print()
    print("===")
    print()

    print("{} songs found. Please select from following candidates:".
          format(len(songs)))
    print("  {:30}|  {:30}|  {:15}|".format("Name", "Album", "Artist"))
    for song in songs:
        ans = input("  {:30}|  {:30}|  {:15}|  [Y/n]: ".format(
            song["trackName"], song["collectionName"], song["artistName"]))
        if ans.lower() == "y" or ans is '':
            return song
    return None

def main(playlistName):
    songList = ["I Took a Pill in Ibiza (SeeB Remix)", "Pure Grinding"]

    foundSongs = []

    for songName in songList:
        candidates = searchSongs(sanitize(songName))

        if len(candidates) == 0:
            print("Can't find {} on Apple Music".format(songName))
            continue

        selectedSong = selectSong(candidates)

        if selectedSong is None:
            print("All candidates are not matched ... (skip for now) #TODO")
            continue

        foundSongs.append(selectedSong)

    plistStr = buildPlist(playlistName, foundSongs)

    with open("{}.xml".format(playlistName), "w") as f:
        f.write(plistStr)

if __name__ == '__main__':
    main("TGIF")
