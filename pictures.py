import os
import exifread
import re
import sys
#import requests
import json
from rgeocoder import ReverseGeocoder
import argparse
import hashlib
import datetime

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
    
def get_pic_GPS(pic_dir):
    md5_dict = {}
    imagename = ['PNG', 'JPG', 'JEPG', 'GIF']
    items = os.listdir(pic_dir)
    for item in items:
        path = os.path.join(pic_dir, item)
        if os.path.isdir(path):
            get_pic_GPS(path)
        elif any(path.upper().endswith(i) for i in imagename):
            if args.delete_duplicated == True:
                md5result = md5(path)
                if md5result in md5_dict.keys():
                    os.remove(path)
                    print("!!! removeing duplicate: " + path)
                    continue
                else:
                    md5_dict[md5result] = path
            if args.remane == True:
                date,city = imageread(path)
                print("city: %s date: %s"%(city,date))
                if args.create_folder == True:
                    new_folder = city + '_' + date.split('-')[0]
                    if args.folder.endswith('/'):
                        new_path = args.folder + new_folder
                    else:
                        new_path = args.folder + '/' + new_folder
                    if not os.path.exists(new_path):
                        os.mkdir(new_path)
            else:
                new_path = os.path.dirname(path)
            basename = os.path.basename(path)
            match = re.search(r'(\d+\_\d+\_\d+_\d+_\d+_)',basename)
            if match:
                new_filename = basename.replace(match.group(1),'_'.join(match.group(1).split("_")[:2]) + '_' + city + '_')
            else:
                new_filename = date + "_" + city + basename
                        
            os.rename(path,new_path + '/' + new_filename)    



def convert_to_decimal(*gps):
    if '/' in gps[0]:
        deg = gps[0].split('/')
        if deg[0] == '0' or deg[1] == '0':
            gps_d = 0
        else:
            gps_d = float(deg[0]) / float(deg[1])
    else:
        gps_d = float(gps[0])
    if '/' in gps[1]:
        minu = gps[1].split('/')
        if minu[0] == '0' or minu[1] == '0':
            gps_m = 0
        else:
            gps_m = (float(minu[0]) / float(minu[1])) / 60
    else:
        gps_m = float(gps[1]) / 60
    if '/' in gps[2]:
        sec = gps[2].split('/')
        if sec[0] == '0' or sec[1] == '0':
            gps_s = 0
        else:
            gps_s = (float(sec[0]) / float(sec[1])) / 3600
    else:
        gps_s = float(gps[2]) / 3600

    decimal_gps = gps_d + gps_m + gps_s
    if gps[3] == 'W' or gps[3] == 'S' or gps[3] == "83" or gps[3] == "87":
        return str(decimal_gps * -1)
    else:
        return str(decimal_gps)

def imageread(path):
    print(path)
    f = open(path, 'rb')
    GPS = {}
    Data = ""
    try:
        tags = exifread.process_file(f)
    except:
        return
    #print(tags)
    '''
    for tag in tags:               
        print(tag,":",tags[tag])
    '''

    if 'GPS GPSLatitudeRef' in tags:

        GPS['GPSLatitudeRef'] = str(tags['GPS GPSLatitudeRef'])
        # print(GPS['GPSLatitudeRef'])
    else:
        GPS['GPSLatitudeRef'] = 'N'  

    if 'GPS GPSLongitudeRef' in tags:
        GPS['GPSLongitudeRef'] = str(tags['GPS GPSLongitudeRef'])
        # print(GPS['GPSLongitudeRef'])
    else:
        GPS['GPSLongitudeRef'] = 'E'  

    if 'GPS GPSAltitudeRef' in tags:
        GPS['GPSAltitudeRef'] = str(tags['GPS GPSAltitudeRef'])

    if 'GPS GPSLatitude' in tags:
        lat = str(tags['GPS GPSLatitude'])
        if lat == '[0, 0, 0]' or lat == '[0/0, 0/0, 0/0]':
            return

        deg, minu, sec = [x.replace(' ', '') for x in lat[1:-1].split(',')]
        GPS['GPSLatitude'] = convert_to_decimal(deg, minu, sec, GPS['GPSLatitudeRef'])

    if 'GPS GPSLongitude' in tags:
        lng = str(tags['GPS GPSLongitude'])
        # print(lng)
        if lng == '[0, 0, 0]' or lng == '[0/0, 0/0, 0/0]':
            return

        deg, minu, sec = [x.replace(' ', '') for x in lng[1:-1].split(',')]
        GPS['GPSLongitude'] = convert_to_decimal(deg, minu, sec, GPS['GPSLongitudeRef'])

    if 'GPS GPSAltitude' in tags:
        GPS['GPSAltitude'] = str(tags["GPS GPSAltitude"])

    if 'Image DateTime' in tags:
        GPS["DateTime"] = str(tags["Image DateTime"])
        #print("Image DateTime " + GPS["DateTime"])
    elif "EXIF DateTimeOriginal" in tags:
        GPS["DateTime"] = str(tags["EXIF DateTimeOriginal"])
        #print("EXIF DateTimeOriginal " + GPS["DateTime"])
    #if 'Image Make' in tags:
        #print('Camera Maker:', tags['Image Make'])
    #if 'Image Model' in tags:
        #print('Camera:', tags['Image Model'])
    #if 'Image ExifImageWidth' in tags:
        #print('Size:', tags['EXIF ExifImageWidth'],tags['EXIF ExifImageLength'])

    if 'GPSLatitude' in GPS:
        city = convert_gps_to_address(float(GPS['GPSLatitude']), float(GPS['GPSLongitude']))
        #print("city:" + city)
    else:
        city = 'Earth'
    if not "DateTime" in GPS.keys():
        GPS["DateTime"] = str(datetime.datetime.fromtimestamp(os.path.getctime(path)))
    if city == '':
        city = 'Earth'
    return GPS["DateTime"].split(' ')[0].replace(':','-'),city


def convert_gps_to_address(lat, lng ):
    rg = ReverseGeocoder()
    r = rg.nearest(lat, lng)
    city = r.admin1
    return city


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--folder", type=str, required=True, help="dirctory contains all of pictures, eg './images/'")
    parser.add_argument("-r", "--remane", action='store_true', help='if reanme the picture like yyyy-mm-dd_city_something.jpg')
    parser.add_argument("-d", "--delete_duplicated", action='store_true', help='if remote duplicated pictures')
    parser.add_argument("-c", "--create_folder", action='store_true', help='if create folder city_yyyy and move pictures matching to such folders')
    args = parser.parse_args()
    get_pic_GPS(args.folder)
