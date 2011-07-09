#!/usr/bin/python

import web 
import sys
import os
import simplejson as json
import cgi
import Image
import urllib
import mimetypes
import md5
import time
import warnings
import hdata

from subprocess import check_call
from base       import BaseEnc
from re         import match

# Constants
CONVERT   = "/usr/bin/convert"
CP        = "/bin/cp"

#ROOT      = "/home/bseitz/t/trunk/highlit"
ROOT      = "/usr/local/highlit"
DB_FILE   = ROOT + "/data/highlit.db"
IMGDIR    = ROOT + "/data/img/"
FIMGDIR   = ROOT + "/data/fimg/"
TMPDIR    = ROOT + "/data/tmp/"

IMG_SERVER = "http://i.highl.it"
IMG_URI    = "/static/img/"
FIMG_URI   = "/static/fimg/"

CODER   = BaseEnc()
DB      = web.database(dbn='sqlite', db=DB_FILE)
R       = web.template.render('templates/', base='base')
RS      = web.template.render('templates/', base='simplebase')

MAX_WIDTH = 700.0

URLS = (
    '/app/upload', 'Upload',
    '/app/crop',   'Crop',
    '/app/select', 'Select',
    '/app/final',  'Final',

    '/',           'Index',
)

# If something goes past this max, the server just doesn't respond, so
# we don't get a nice error message.
# 16MB max upload
cgi.maxlen = 2**24

# This is the maximum we will actually operate on.  If it's above this, we
# return an error and delete. 8MB 
MAX_FILE = 2**23

# Interface to Amazon S3 datastore
HD = hdata.HData()

class Final:
    def GET(self):
        i = web.input()
        image_info = image_info_from_enc_id(i.enc_id, FIMGDIR, FIMG_URI) 
    
        filename   = "%s.%s" % (image_info['enc_id'], image_info['ext'])

        public_uri = "%s/%s" % (IMG_SERVER, filename)

        scale = compute_scale(image_info['width'], image_info['height'])
        scaled_x = image_info['width'] * scale
        scaled_y = image_info['height'] * scale

        # We don't need this file anymore, it's on Amazon
        os.remove(FIMGDIR + filename)

        return RS.final(public_uri, scaled_x, scaled_y)

class Select:
    def GET(self):
        i = web.input()
        image_info = image_info_from_enc_id(i.enc_id)

        if image_info['auth'] != i.auth:
            raise Exception("Invalid auth key")

        scale    = compute_scale(image_info['width'], image_info['height'])
        scaled_x = int(image_info['width'] * scale)
        scaled_y = int(image_info['height'] * scale)

        return RS.select(image_uri(image_info), i.enc_id, 
            image_info['ext'], i.auth, scaled_x, scaled_y)


class Index:
    def GET(self):
        return R.index()

class Upload:
    def POST(self):
        try:
            i = web.input(upfile = {})

            # Determine file ext by reading mime magic on a tmp file
            tmp_file = self.create_tmp_file(i)
            img_info = image_info_from_path(tmp_file)
        
            # Now that we know it's an image file, create an id for it
            id     = self.insert_image_to_db(img_info['ext'], img_info['auth'])
            enc_id = CODER.encode(id)

            # Use the enc_id for the filename, and rename tmp_file to here
            real_file = os.path.join(IMGDIR, "%s.%s" % (enc_id, img_info['ext']))
            os.rename(tmp_file, real_file)

            return json.dumps({ 
                "enc_id"     : enc_id,
                "img_uri"    : IMG_URI + os.path.basename(real_file),
                "ext"        : img_info['ext'],
                "width"      : img_info['width'],
                "height"     : img_info['height'],
                "select_uri" : select_uri(enc_id, img_info['auth']).replace("&", "%26"),
                "auth"       : img_info['auth'],
            })

        except Exception:
            web.webapi.debug(sys.exc_info()[0])
            web.webapi.debug(sys.exc_info()[1])
            web.webapi.debug(sys.exc_info()[2])
            return json.dumps({
                "error" : "Unknown error",
            })



    def create_tmp_file(self, i):
        tmp_file = os.tempnam(TMPDIR)
        tmp_fh   = open(tmp_file, "w")

        tmp_fh.write(i.upfile.value)
        tmp_fh.close()

        # If file's too big, delete it and raise exception
        statinfo = os.stat(tmp_file)
        if statinfo.st_size > MAX_FILE:
            os.remove(tmp_file)
            raise Exception("file's too big")

        return tmp_file
        
        
    def insert_image_to_db(self, ext, auth):
        id = DB.insert('images', ext=ext, auth=auth)
        return id


class Crop:
    def GET(self):
        i = web.input()
        try:
            image_info = image_info_from_enc_id(i.enc_id)
            if image_info['auth'] != i.auth:
                raise Exception("Invalid auth key")

            final_file = self.convert_image(image_info['width'], image_info['height'], i)
            HD.put_image(final_file)
            id = self.update_image_with_crop_info(i)

            jdata = json.dumps({ 
                "final_uri": final_uri(i.enc_id),
                "enc_id"   : CODER.encode(id),
                "fimg_uri" : IMG_SERVER + "/" + os.path.basename(final_file),
                "left"     : i.left,
                "top"      : i.top
            })
            
            return jdata

        except Exception:
            web.webapi.debug(sys.exc_info()[0])
            web.webapi.debug(sys.exc_info()[1])
            web.webapi.debug(sys.exc_info()[2])
            return json.dumps({
                "error" : "Unknown error",
            })


    def make_img_path(self, dir, i):
        return os.path.join(dir, "%s.%s" % (i.enc_id, i.ext))

    def convert_image(self, orig_width, orig_height, i):
        in_file   = self.make_img_path(IMGDIR, i)
        c_file    = os.tempnam(TMPDIR)
        d_file    = os.tempnam(TMPDIR) 
        f_file    = self.make_img_path(FIMGDIR, i)

        scale = compute_scale(int(orig_width), int(orig_height))
        scaled_left   = int(int(i.left) / scale)
        scaled_top    = int(int(i.top) / scale)
        scaled_width  = int(int(i.width) / scale)
        scaled_height = int(int(i.height) / scale)
        
        geometry = "%sx%s+%s+%s" % (scaled_width, scaled_height, scaled_left, scaled_top)

        # Make cropped file
        if i.style == "lighten":
            # Do a simple crop
            check_call([CONVERT, in_file, '-crop', geometry, c_file])
        else:
            # Do a crop while drawing a circle
            stroke_width = 2
            mid_x = int((int(scaled_width) / 2)) 
            mid_y = int((int(scaled_height) / 2))
            draw_val = "ellipse %d,%d %d,%d 0,360" % (
                mid_x, mid_y, mid_x - stroke_width, mid_y - stroke_width
            )
            check_call([CONVERT, in_file, '-crop', geometry, '-fill', 
                'none', '-stroke', i.style, '-strokewidth', str(stroke_width), 
                '-draw', draw_val, c_file])

        if i.style == "lighten":
            # Make darkened file 
            check_call([CONVERT, in_file, '-matte', '-fill', "#000a", '-draw', 
                "rectangle 0,0,%s,%s" % (orig_width, orig_height), d_file])
        else:
            # Don't darken, just copy
            check_call([CP, in_file, d_file])


        # Make final file
        check_call([CONVERT, d_file, '-draw', 
            "image SrcOver %s,%s 0,0 '%s'" % (scaled_left, scaled_top, c_file), f_file])

        os.remove(c_file)
        os.remove(d_file)

        return f_file


    def update_image_with_crop_info(self, i):
        id = CODER.decode(i.enc_id)

        scale = compute_scale(int(i.width), int(i.height))
        scaled_left = int(int(i.left) / scale)
        scaled_top  = int(int(i.top) / scale)
 
        DB.update('images', where="id = $id", height = i.height, width= i.width, top = scaled_top, left = scaled_left, vars=locals())

        return id

def image_info_from_enc_id(enc_id, imgdir=IMGDIR, img_uri=IMG_URI):
    id = CODER.decode(enc_id)
    myvars = dict(id=id)
    ext = ''

    results = DB.select('images', myvars, where="id = $id")
    for res in results:
        ext  = res['ext']
        auth = res['auth']

    file_path = "%s%s.%s" % (imgdir, enc_id, ext)
    info = image_info_from_path(file_path)

    # Overload auth with info from db
    info['auth'] = auth

    return info

def image_uri(image_info, img_uri=IMG_URI):
    return "%s%s.%s" % (img_uri, image_info['enc_id'], image_info['ext'])
   

def image_info_from_path(file_path):
    im   = Image.open(file_path)
    ext  = file_ext(file_path, im.format)
    w, h = im.size
    
    name_ext = os.path.basename(file_path).split('.')

    authmd5 = md5.new()
    authmd5.update(file_path + str(time.time()))
    auth = authmd5.hexdigest()

    return {
        "enc_id" : name_ext[0],
        "ext"    : ext,
        "width"  : w,
        "height" : h,
        "auth"   : auth,
    }


def file_ext(file_path, format):
    format_to_type = (
        (r"^JPEG", "jpg"),
        (r"^PNG",  "png"),
        (r"^GIF",  "gif"),
    )

    for f in format_to_type:
        m = match(f[0], format)
        if (m):
            return f[1]

    # If none of these match, we don't support it and we should cleanup 
    os.remove(file_path)
    raise Exception("unsupported image format") 

def select_uri(enc_id, auth):
    return "/app/select?" + urllib.urlencode({
        "enc_id" : enc_id, 
        "auth"   : auth,
    }) 

def final_uri(enc_id):
    return "/app/final?" + urllib.urlencode({"enc_id" : enc_id}) 

def compute_scale(width, height):
    if width > MAX_WIDTH:
        return MAX_WIDTH / width
    else:
        return 1

if __name__ == "__main__":
    warnings.filterwarnings('ignore', 'tempnam', RuntimeWarning) 
    app = web.application(URLS, globals())
    app.run()

