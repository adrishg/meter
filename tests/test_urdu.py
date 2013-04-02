import sys, os

topdir = os.path.join(os.path.dirname(__file__), '..')
topdir = os.path.abspath(topdir)
#sys.path.insert(0, topdir)

from parser import Parser

def test_urdu_meter_tokenizer():
    p = Parser('settings/urdu-meter.yaml')

    # The parser has a 'tokenize' function
    s = "naqsh faryaadii hai kis kii sho;xii-e ta;hriir kaa"
    t = p.tokenize(s)

    assert t == ['n', 'a', 'q', 'sh', ' ', 'f', 'a', 'r', 'y', 'aa', 'd', 'ii', ' ', \
                 'h', 'ai', ' ', 'k', 'i', 's', ' ', 'k', 'ii', ' ', 'sh', 'o', ';x', 'ii', '-e', ' ', \
                 't', 'a', ';h', 'r', 'ii', 'r', ' ', 'k', 'aa']

def test_urdu_meter_parser():
    p = Parser('settings/urdu-meter.yaml') # this is the setting file used in step 1.

    s = "naqsh faryaadii hai kis kii sho;xii-e ta;hriir kaa"
    x = p.parse(s)
    assert x == "csccbcsccvcvbcvbcscbcvbcvcv<ii+z>zbcsccvcbcv"
