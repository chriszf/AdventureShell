#/usr/bin/env python

import os, stat, sys

class Readable(object):
    def __init__(self, filename):
	f = open(filename)
	self.description = f.read()
	f.close()
	self.name = filename[:-4].replace("_", " ")
	self.filename = filename

    def __str__(self):
	return "%s (readable)"%self.name

    def read(self):
	print self.description


class Exit(object):
    def __init__(self, dirname):
	# Special case ".."
	if dirname == "..":
	    self.name = "back"
	    prev_dir = os.path.basename(os.path.split(os.getcwd())[0])
	    n, self.target_room = self.parse_dirname(prev_dir)
	else:	    
	    self.name, self.target_room = self.parse_dirname(dirname)
	    self.target_room = self.target_room.replace("_", " ")
	self.dirname = dirname

    @staticmethod
    def parse_dirname(dirname):

	if dirname == "outside":
	    return (None, "Outside")

	name, target = dirname.split("-")
	return (name, target.replace("_", " "))

    def go(self):
	os.chdir(self.dirname)

    def __str__(self):
	return "%s [to %s]"%(self.name, self.target_room)

class File(object):
    def __init__(self, filename):
	self.name = filename
	self.stat = os.stat(filename)
	self.is_dir = stat.S_ISDIR(self.stat.st_mode)
	self.executable = os.access(filename, os.X_OK)

    def to_obj(self):
	# Take an object, turn it into a class according to the filetype
	if self.is_dir:
	    return Exit(self.name)

	types = {".txt": Readable}
	suffix = self.name[-4:]
	obj_type = types[suffix]

	if obj_type:
	    return obj_type(self.name)

	return None

    def __str__(self):
	return "%s - %s - %s"%(self.name, self.is_dir, self.executable)

class Room(object):
    def __init__(self, name, description, contents, exits):
	self.description = description
	self.exits = exits or []
	if name != "outside":
	    self.exits.insert(0, Exit(".."))
	    direction, name = name.split("-")

	self.name = name.replace("_", " ")
	self.contents = contents
	pass

    def find_by_name(self, name):
	for item in self.contents:
	    if item.name == name:
		return item

    def find_exit_by_name(self, name):
	for item in self.exits:
	    if item.name == name:
		return item
	
    def __str__(self):
	return \
"""%s
%s
Exits: %s
You see:
%s
"""%(self.name, self.description, ", ".join([str(exit) for exit in self.exits]) or "None", "\n".join(["\t%s"%str(item) for item in self.contents]) or "Nothing")

def parse_dir():
    cur_dir = os.path.basename(os.getcwd()) 
    filenames = os.listdir(".")
    if "description.txt" in filenames:
	filenames.remove("description.txt")


    room_objs = [File(filename).to_obj() for filename in filenames]
    # Split up the objects
    exits = []
    contents = []

    for item in room_objs:
	if type(item) == Exit:
	    exits.append(item)
	else:
	    contents.append(item)

    # Open the description
    description = "The room is pitch black."
    try:
	f = open("description.txt")
	description = f.read()
	f.close()
    except:
	pass

    return Room(cur_dir, description, contents, exits)

ACTIONS = {}

def action(*args):
    if type(args[0]) == str:
	def wrapped(fn):
	    ACTIONS[fn.func_name] = fn
	    for name in args:
		ACTIONS[name] = fn

	    return fn

    else:
	fn = args[0]
	ACTIONS[fn.func_name] = fn
	return fn

    return wrapped

@action
def look(context, target):
    loc = context['location']
    #print loc.contents
    print loc

@action("quit")
def exit(context, target):
    print "Thanks for playing 'adventure shell', goodbye!"
    sys.exit(0)

@action
def read(context, target):
    target = " ".join(target)
    try:
	readable = context['location'].find_by_name(target)
	print readable
	readable.read()

    except Exception, e:
	print "I couldn't find anything to read."

@action
def cat(context, target):
    cmd = "cat " + " ".join(target)
    os.system(cmd)

@action
def cd(context, target):
    try:
	os.chdir(" ".join(target))
    except:
	print "-advshell error: No such file or directory"

@action
def ls(context, target):
    cmd = "ls " + " ".join(target)
    os.system(cmd)

@action
def go(context, target):
    target = " ".join(target)
    try:
	exit = context['location'].find_exit_by_name(target)
	exit.go()
	new_loc = parse_dir()
	context['location'] = new_loc
	print new_loc
    except Exception, e:
	print "I'm sorry, I couldn't figure out how to go '%s'."%target
	

def eval_line(line, context):
    try:
	tokens = line.split()
	action_name = tokens[0]
	target = []
	if len(tokens) > 1:
	    target = tokens[1:]

	action = ACTIONS[action_name]
	action(context, target)
	
    except Exception, e:
	print "I don't understand that."


def main():
    cur_dir = os.chdir("outside")
    room = parse_dir()
    print room
    context = {"location": room}

    # repl
    while True:
	line = raw_input(">")
	eval_line(line, context)

if __name__ == "__main__":
    main()
