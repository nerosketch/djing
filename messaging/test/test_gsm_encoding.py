# -*- coding: utf-8 -*-
# Copyright (C) 2011  Sphere Systems Ltd
# Author:  Andrew Bird
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""Unittests for the gsm encoding/decoding module"""

import unittest
import messaging.sms.gsm0338  # imports GSM7 codec

# Reversed from: ftp://ftp.unicode.org/Public/MAPPINGS/ETSI/GSM0338.TXT
MAP = {
#    unichr(0x0000): (0x0000, 0x00),  # Null
    '@': (0x0040, 0x00),
    '£': (0x00a3, 0x01),
    '$': (0x0024, 0x02),
    '¥': (0x00a5, 0x03),
    'è': (0x00e8, 0x04),
    'é': (0x00e9, 0x05),
    'ù': (0x00f9, 0x06),
    'ì': (0x00ec, 0x07),
    'ò': (0x00f2, 0x08),
    'Ç': (0x00c7, 0x09),  #   LATIN CAPITAL LETTER C WITH CEDILLA
    chr(0x000a): (0x000a, 0x0a),  # Linefeed
    'Ø': (0x00d8, 0x0b),
    'ø': (0x00f8, 0x0c),
    chr(0x000d): (0x000d, 0x0d),  # Carriage return
    'Å': (0x00c5, 0x0e),
    'å': (0x00e5, 0x0f),
    'Δ': (0x0394, 0x10),
    '_': (0x005f, 0x11),
    'Φ': (0x03a6, 0x12),
    'Γ': (0x0393, 0x13),
    'Λ': (0x039b, 0x14),
    'Ω': (0x03a9, 0x15),
    'Π': (0x03a0, 0x16),
    'Ψ': (0x03a8, 0x17),
    'Σ': (0x03a3, 0x18),
    'Θ': (0x0398, 0x19),
    'Ξ': (0x039e, 0x1a),
    chr(0x00a0): (0x00a0, 0x1b),  #  Escape to extension table (displayed
                                     #  as NBSP, on decode of invalid escape
                                     #  sequence)
    'Æ': (0x00c6, 0x1c),
    'æ': (0x00e6, 0x1d),
    'ß': (0x00df, 0x1e),
    'É': (0x00c9, 0x1f),
    ' ': (0x0020, 0x20),
    '!': (0x0021, 0x21),
    '"': (0x0022, 0x22),
    '#': (0x0023, 0x23),
    '¤': (0x00a4, 0x24),
    '%': (0x0025, 0x25),
    '&': (0x0026, 0x26),
    '\'': (0x0027, 0x27),
    '{': (0x007b, 0x1b28),
    '}': (0x007d, 0x1b29),
    '*': (0x002a, 0x2a),
    '+': (0x002b, 0x2b),
    ',': (0x002c, 0x2c),
    '-': (0x002d, 0x2d),
    '.': (0x002e, 0x2e),
    '\\': (0x005c, 0x1b2f),
    '0': (0x0030, 0x30),
    '1': (0x0031, 0x31),
    '2': (0x0032, 0x32),
    '3': (0x0033, 0x33),
    '4': (0x0034, 0x34),
    '5': (0x0035, 0x35),
    '6': (0x0036, 0x36),
    '7': (0x0037, 0x37),
    '8': (0x0038, 0x38),
    '9': (0x0039, 0x39),
    ':': (0x003a, 0x3a),
    ';': (0x003b, 0x3b),
    '[': (0x005b, 0x1b3c),
    chr(0x000c): (0x000c, 0x1b0a),  # Formfeed
    ']': (0x005d, 0x1b3e),
    '?': (0x003f, 0x3f),
    '|': (0x007c, 0x1b40),
    'A': (0x0041, 0x41),
    'B': (0x0042, 0x42),
    'C': (0x0043, 0x43),
    'D': (0x0044, 0x44),
    'E': (0x0045, 0x45),
    'F': (0x0046, 0x46),
    'G': (0x0047, 0x47),
    'H': (0x0048, 0x48),
    'I': (0x0049, 0x49),
    'J': (0x004a, 0x4a),
    'K': (0x004b, 0x4b),
    'L': (0x004c, 0x4c),
    'M': (0x004d, 0x4d),
    'N': (0x004e, 0x4e),
    'O': (0x004f, 0x4f),
    'P': (0x0050, 0x50),
    'Q': (0x0051, 0x51),
    'R': (0x0052, 0x52),
    'S': (0x0053, 0x53),
    'T': (0x0054, 0x54),
    'U': (0x0055, 0x55),
    'V': (0x0056, 0x56),
    'W': (0x0057, 0x57),
    'X': (0x0058, 0x58),
    'Y': (0x0059, 0x59),
    'Z': (0x005a, 0x5a),
    'Ä': (0x00c4, 0x5b),
    'Ö': (0x00d6, 0x5c),
    'Ñ': (0x00d1, 0x5d),
    'Ü': (0x00dc, 0x5e),
    '§': (0x00a7, 0x5f),
    '¿': (0x00bf, 0x60),
    'a': (0x0061, 0x61),
    'b': (0x0062, 0x62),
    'c': (0x0063, 0x63),
    'd': (0x0064, 0x64),
    '€': (0x20ac, 0x1b65),
    'f': (0x0066, 0x66),
    'g': (0x0067, 0x67),
    'h': (0x0068, 0x68),
    '<': (0x003c, 0x3c),
    'j': (0x006a, 0x6a),
    'k': (0x006b, 0x6b),
    'l': (0x006c, 0x6c),
    'm': (0x006d, 0x6d),
    'n': (0x006e, 0x6e),
    '~': (0x007e, 0x1b3d),
    'p': (0x0070, 0x70),
    'q': (0x0071, 0x71),
    'r': (0x0072, 0x72),
    's': (0x0073, 0x73),
    't': (0x0074, 0x74),
    '>': (0x003e, 0x3e),
    'v': (0x0076, 0x76),
    'i': (0x0069, 0x69),
    'x': (0x0078, 0x78),
    '^': (0x005e, 0x1b14),
    'z': (0x007a, 0x7a),
    'ä': (0x00e4, 0x7b),
    'ö': (0x00f6, 0x7c),
    'ñ': (0x00f1, 0x7d),
    'ü': (0x00fc, 0x7e),
    'à': (0x00e0, 0x7f),
    '¡': (0x00a1, 0x40),
    '/': (0x002f, 0x2f),
    'o': (0x006f, 0x6f),
    'u': (0x0075, 0x75),
    'w': (0x0077, 0x77),
    'y': (0x0079, 0x79),
    'e': (0x0065, 0x65),
    '=': (0x003d, 0x3d),
    '(': (0x0028, 0x28),
    ')': (0x0029, 0x29),
}

GREEK_MAP = {  # Note: these might look like Latin uppercase, but they aren't
    'Α': (0x0391, 0x41),
    'Β': (0x0392, 0x42),
    'Ε': (0x0395, 0x45),
    'Η': (0x0397, 0x48),
    'Ι': (0x0399, 0x49),
    'Κ': (0x039a, 0x4b),
    'Μ': (0x039c, 0x4d),
    'Ν': (0x039d, 0x4e),
    'Ο': (0x039f, 0x4f),
    'Ρ': (0x03a1, 0x50),
    'Τ': (0x03a4, 0x54),
    'Χ': (0x03a7, 0x58),
    'Υ': (0x03a5, 0x59),
    'Ζ': (0x0396, 0x5a),
}

QUIRK_MAP = {
    'ç': (0x00e7, 0x09),
}

BAD = -1


class TestEncodingFunctions(unittest.TestCase):

    def test_encoding_supported_unicode_gsm(self):

        for key in list(MAP.keys()):
            # Use 'ignore' so that we see the code tested, not an exception
            s_gsm = key.encode('gsm0338', 'ignore')

            if len(s_gsm) == 1:
                i_gsm = ord(s_gsm)
            elif len(s_gsm) == 2:
                i_gsm = (ord(s_gsm[0]) << 8) + ord(s_gsm[1])
            else:
                i_gsm = BAD  # so we see the comparison, not an exception

            # We shouldn't generate an invalid escape sequence
            if key == chr(0x00a0):
                self.assertEqual(BAD, i_gsm)
            else:
                self.assertEqual(MAP[key][1], i_gsm)

    def test_encoding_supported_greek_unicode_gsm(self):
        # Note: Conversion is one way, hence no corresponding decode test

        for key in list(GREEK_MAP.keys()):
            # Use 'replace' so that we trigger the mapping
            s_gsm = key.encode('gsm0338', 'replace')

            if len(s_gsm) == 1:
                i_gsm = ord(s_gsm)
            else:
                i_gsm = BAD  # so we see the comparison, not an exception

            self.assertEqual(GREEK_MAP[key][1], i_gsm)

    def test_encoding_supported_quirk_unicode_gsm(self):
        # Note: Conversion is one way, hence no corresponding decode test

        for key in list(QUIRK_MAP.keys()):
            # Use 'replace' so that we trigger the mapping
            s_gsm = key.encode('gsm0338', 'replace')

            if len(s_gsm) == 1:
                i_gsm = ord(s_gsm)
            else:
                i_gsm = BAD  # so we see the comparison, not an exception

            self.assertEqual(QUIRK_MAP[key][1], i_gsm)

    def test_decoding_supported_unicode_gsm(self):
        for key in list(MAP.keys()):
            i_gsm = MAP[key][1]
            if i_gsm <= 0xff:
                s_gsm = chr(i_gsm)
            elif i_gsm <= 0xffff:
                s_gsm = chr((i_gsm & 0xff00) >> 8)
                s_gsm += chr(i_gsm & 0x00ff)

            s_unicode = s_gsm.decode('gsm0338', 'strict')
            self.assertEqual(MAP[key][0], ord(s_unicode))

    def test_is_gsm_text_true(self):
        for key in list(MAP.keys()):
            if key == chr(0x00a0):
                continue
            self.assertEqual(messaging.sms.gsm0338.is_gsm_text(key), True)

    def test_is_gsm_text_false(self):
        self.assertEqual(
            messaging.sms.gsm0338.is_gsm_text(chr(0x00a0)), False)

        for i in range(1, 0xffff + 1):
            if chr(i) not in MAP:
                # Note: it's a little odd, but on error we want to see values
                if messaging.sms.gsm0338.is_gsm_text(chr(i)) is not False:
                    self.assertEqual(BAD, i)
