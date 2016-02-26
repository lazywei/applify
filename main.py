import requests
import json
import plistlib
import datetime
import csv

from urllib.parse import urlencode
from lxml import etree


def searchSongs(term):
    query = urlencode({"term": term, "entity": "musicTrack", "media": "music", "country": "TW"})
    resp = requests.get("https://itunes.apple.com/search?{}".format(query))
    results = json.loads(resp.text)
    return list(filter(
        lambda res: res["kind"] == "song" and res["isStreamable"] is True,
        results["results"]))

def buildPlist(playlistName, songs):
    tracks = {}
    track_id = 10000
    for song in songs:
        tracks[str(track_id)] = {
            "Track ID": track_id,
            "Artist": song["artistName"],
            "Album": song["collectionCensoredName"],
            "Disc Number": song["discNumber"],
            "Name": song["trackName"],
            "Play Count": 0,
            "Purchased": True,
            "Sort Album": song["collectionCensoredName"],
            "Sort Artist": song["artistName"],
            "Sort Name": song["trackName"],
            "Track Number": song["trackNumber"],
            "Track Type": "Remote",
            "Kind": "AACaudio file",
            "Bit Rate": 256,
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


def displayCandidates(songs, pageStart, fmtStr):
    nSongs = len(songs)

    for i in range(nSongs):
        song = songs[i]
        print(fmtStr.format(
            i+pageStart, song["trackName"],
            song["artistName"], song["collectionCensoredName"]))

def selectSong(songs, spfSong):
    nSongs = len(songs)
    fmtStr = "{:3}) {:26}|  {:35}|  {:30}" 
    print("{} songs found. Please select from following candidates:".
          format(nSongs))
    print(fmtStr.format("#", "Name", "Artist", "Album"))
    print(fmtStr.format(
        "SPF", spfSong["trackName"],
        spfSong["artistName"], spfSong["collectionName"]))

    page = 0
    pageSize = 10
    while True:

        start = page * pageSize
        end = start + pageSize
        displayCandidates(songs[start:end], start, fmtStr)

        ans = input("Enter candidates' number to select, 'n' for next page," +
                    " 's' to skip this track. (default=0): ")

        if ans.lower() == "s":
            print("All candidates are not matched ... (skip for now) #TODO")
            return None
        elif ans.lower() == "n":
            page += 1
            if page > int(nSongs / pageSize):
                print("No more candidates, skip this track ...")
                return None
        elif ans is '':
            return songs[0]
        else:
            return songs[int(ans)]

def readSpotifyList(playlistName):
    songs = []
    with open("{}.csv".format(playlistName), "r") as csvfile:
        reader = csv.reader(csvfile)
        next(reader) # skip header
        for row in reader:
            songs.append({
                "trackName": row[0], "artistName": row[1],
                "collectionName": row[2],
            })
    return songs

def main(playlistName):
    spfSongs = readSpotifyList(playlistName)

    foundSongs = []

    for spfSong in spfSongs:
    # for songName in songList:
        candidates = searchSongs("{} {} {}".format(
            spfSong["trackName"],
            spfSong["artistName"],
            spfSong["collectionName"]
            ))
        candidates = candidates[:1]

        if len(candidates) == 0:
            print("Can't find {} on Apple Music".format(spfSong["trackName"]))
            continue

        if len(candidates) == 1:
            selectedSong = candidates[0]
        else:
            selectedSong = selectSong(candidates, spfSong)

        if selectedSong is None:
            continue
        else:
            print("\nSelected: {} - {} - {}\n".format(
                selectedSong["trackName"],
                selectedSong["artistName"],
                selectedSong["collectionCensoredName"]
            ))
            foundSongs.append(selectedSong)

    plistStr = buildPlist(playlistName, foundSongs)

    with open("{}.xml".format(playlistName), "w") as f:
        f.write(plistStr)

if __name__ == '__main__':
    main("TGIF")
