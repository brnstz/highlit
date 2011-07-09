#!/usr/bin/python

import boto
from boto.s3.key import Key

import os

ACCESS_KEY = "FIXME"
SECRET_KEY = "FIXME"
BUCKET     = "i.highl.it"

class HData:
    def __init__(self):
        self.conn   = boto.connect_s3(ACCESS_KEY, SECRET_KEY)
        self.bucket = self.conn.get_bucket(BUCKET)

    def put_image(self, filename):
        k     = Key(self.bucket)
        k.key = os.path.basename(filename)
        
        k.set_contents_from_filename(filename)
        k.set_acl('public-read')

