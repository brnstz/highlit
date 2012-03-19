#!/usr/bin/python

import sys

from optparse import OptionParser

# This array acts as a mapping from decimal values to encoded characters
DEC_TO_ENC = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

MAX_BASE = len(DEC_TO_ENC)

# Reverse the mapping from encoded characters to decimal values
ENC_TO_DEC = dict([(DEC_TO_ENC[x], x) for x in range(0, MAX_BASE)])

class BaseEnc:
    
    def __init__(self, base = MAX_BASE):
        if base > MAX_BASE:
            raise Exception (
                "Invalid base.  %s is greater than max base of %s" % 
                (base, MAX_BASE)
            )    

        self.base = base

    def decode(self, enc_str):
        """
        Convert enc_str from self.base to a decimal num.
        """
        # Ensure enc_str is a string
        enc_str = str(enc_str)

        power = len(enc_str) - 1
        dec_num = 0

        # For every character in the encoded string, compute its decimal
        # value relative to its position
        for char in enc_str:
            dec_num += int(ENC_TO_DEC[char]) * (self.base ** power)
            power -= 1

        return dec_num

    def encode(self, dec_num, enc_str = ''):
        """
        Convert dec_num from decimal to a string encode in self.base
        """
        # Ensure dec_num is an integer
        dec_num = int(dec_num) 

        # If our decimal number is less than the encoding base, we can simply
        # return the direct translation
        if dec_num < self.base:
            return DEC_TO_ENC[dec_num]

        # Otherwise, we compute the quotient and remainder and continue
        # calculation
        q  = dec_num // self.base
        r  = dec_num % self.base

        # If we still have a larger quotient, call recursively and prepend
        # to our encoded string
        if q >= self.base:
            return self.encode(q, enc_str) + DEC_TO_ENC[r]
        
        # Otherwise, we can compute our final encoded string
        else:
            return DEC_TO_ENC[q] + DEC_TO_ENC[r] + enc_str


def options_args():
    """
    Create an option parser, and return the options plus the extra args. 
    Extra args are the numbers to decode or encode.
    """
    parser = OptionParser()
    parser.add_option("-e", "--encode", action="store_true")
    parser.add_option("-d", "--decode", action="store_true")
    parser.add_option("-b", "--base", default=MAX_BASE)

    options, args = parser.parse_args()

    if options.encode and options.decode:
        parser.error("Can't use --encode and --decode")

    if not (options.encode or options.decode):
        parser.error("Must use either --encode or --decode")

    return options, args 
    

if __name__ == "__main__":
    options, args = options_args()
    
    coder = BaseEnc(base = int(options.base))

    if options.encode:
        for arg in args:
            print coder.encode(arg)

    elif options.decode:
        for arg in args:
            print coder.decode(arg)
    
