from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import random
import math
from collections import defaultdict
import subprocess
from time import time
from twython import Twython
import json
import argparse
import os.path
import pprint

#pp = pprint.PrettyPrinter(indent=4)

class Game(object):
    """GOL universe, size of 160x160"""
    def __init__(self):
        self.universe = defaultdict(int)
        self.generations = 0
        self.alive = True

    def generate(self):
       r = random.Random()
       for i in xrange(160):
           for j in xrange(160):
               prop = random_select(i,j)
               if r.random() < prop:
                   self.universe[(i,j)] = 1

    def save_image(self):
        ig = Image.new('RGB', (160, 160), "white")
        pixels = ig.load()
        for p in self.universe.keys():
            if p[0] < 0 or p[0] > 159 or p[1] < 0 or p[1] > 159:
                continue
            pixels[p[0],p[1]] = (32, 255, 32)
        ig = ig.resize((640, 640) , Image.ANTIALIAS)
        ig.save("images/gol%04d.gif" % self.generations, 'GIF')

    def next(self):
        neighbours = defaultdict(int)
        for p in self.universe.keys():
            neighbours[(p[0]-1,p[1]-1)] += 1
            neighbours[(p[0],p[1]-1)] += 1
            neighbours[(p[0]+1,p[1]-1)] += 1
            neighbours[(p[0]-1,p[1])] += 1
            neighbours[(p[0]+1,p[1])] += 1
            neighbours[(p[0]-1,p[1]+1)] += 1
            neighbours[(p[0],p[1]+1)] += 1
            neighbours[(p[0]+1,p[1]+1)] += 1
        next_universe = defaultdict(int)
        for n in neighbours.keys():
            if self.universe[n] == 1 and 2 <= neighbours[n] <= 3:
                next_universe[n] = 1
            if self.universe[n] == 0 and neighbours[n] == 3:
                next_universe[n] = 1
        self.alive = self.isnextalive(next)
        if len(next_universe) == 0:
            self.alive = False
        if self.generations > 2000:
            self.alive = False
        self.universe = next_universe
        self.generations += 1

    def isnextalive(self,next):
        return True

    def save_json(self,filename):
        if self.alive:
            f = open(filename, "w")
            dump = {"generations": self.generations, "universe": self.universe.keys() }
            f.write(json.dumps(dump))
            f.close()
        else:
            os.remove(filename)

    def load_json(self, filename):
        f = open(filename,"r")
        objs = json.loads("".join(f.readlines()))
        self.init_from_keys(objs["universe"])
        self.generations = objs["generations"]
        f.close()

    def summary(self):
        return "Game of life after %d generations, %d cells alive." % (self.generations, len(self.universe.keys()))


    def init_from_keys(self, keylist):
        self.universe = defaultdict(int)
        for k in keylist:
            self.universe[tuple(k)] = 1

    def save_big_picture(self):
        min_x = min([i[0] for i in self.universe.keys()])
        min_y = min([i[1] for i in self.universe.keys()])
        max_x = max([i[0] for i in self.universe.keys()])
        max_y = max([i[1] for i in self.universe.keys()])

        w = max_x-min_x+1
        h  = max_y-min_y+1

        ig = Image.new('RGB', (w,h), "white")
        pixels = ig.load()
        for p in self.universe.keys():
            pixels[p[0]-min_x, p[1]-min_y] = (32, 255, 32)
        ig = ig.resize((w*4, h*4) , Image.ANTIALIAS)
        ig.save("anims/gol%04d.png" % self.generations, 'PNG')

class TwythonHelper:

    def __init__(self, keyfile):
        f = open(keyfile)
        lines = f.readlines()
        f.close()
        consumerkey = lines[0].split("#")[0]
        consumersecret = lines[1].split("#")[0]
        accesstoken = lines[2].split("#")[0]
        accesssec = lines[3].split("#")[0]

        self.api = Twython(consumerkey, consumersecret, accesstoken, accesssec)


def handle_command_line():
    parser = argparse.ArgumentParser(
        description="Advances game in gamefile 20 genarations and tweets a GIF")
    parser.add_argument("-g", "--gamefile",
                        help="contents of the game", default="gamefile.txt")
    args = parser.parse_args()
    return args


def random_select(x,y):
    dist_from_center = math.log(1.5 +(x-80)**2 + (y-80)**2)
    return 1.0 / dist_from_center


if __name__ == "__main__":
    args = handle_command_line()
    api = (TwythonHelper("keys.keys")).api

    g = Game()
    if os.path.isfile(args.gamefile):
        g.load_json(args.gamefile)
    else:
        g.generate()
    start = g.generations
    g.save_image()
    for x in xrange(100):
        g.next()
        g.save_image()
    end = g.generations
    anim_items =["images/gol%04d.gif" % x for x in xrange(start, end)]
    outfile_name = "anims/animation%.02f.gif" % time() 
    outfile = open(outfile_name, "wb")
    cmd = ["gifsicle", "--delay=30", "--loop"] + anim_items
    subprocess.call(cmd, stdout=outfile)
    outfile.close()
    
    fn = open(outfile_name, "rb")

    api.update_status_with_media(status=g.summary(), media=fn)
    fn.close()

    g.save_json(args.gamefile)
    g.save_big_picture()
