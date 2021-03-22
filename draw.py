#!/usr/bin/env python

import turtle
import json
import argparse
import math
import pathlib

# This is made global.
#
program_args = None
file_last_loaded = None

# Hrmmm, this could be considered cheating... maybe make this something
# that can be enabled by command-line option
#
def on_click_print_coords(x, y):
    '''Used with turtle.onscreenclick() to print coordinates of a click'''

    def round_to_half(n):
        '''Round a number to its nearest half returning a string.

        If the decimal portion is < .25, then round down
        Else if the decimal portion is < .75, then round to .5
        Else round up

        A string is returned because we are mostly concerned with
        the representation of it, and I don't want to see .0 in
        the coordinates.
        '''

        if n % 1.0 < 0.25:
            return str(math.floor(n))
        elif n % 1.0 < 0.75:
            return str(math.floor(n)) + '.5'
        else:
            return str(math.ceil(n))

    print("[{x}, {y}], ".format(
        x = round_to_half(x),
        y = round_to_half(y)
    ))


def draw_grid(llx=None, lly=None, urx=None, ury=None):
    '''Given lower-left x, y and upper-right x, y, draw grid lines'''

    # Remember the old speed so we can set it back. No-one will
    # want to watch gridlines draw slowly.
    #
    prev_speed = turtle.speed()
    turtle.speed('fastest')
    prev_tracer = turtle.tracer()
    turtle.tracer(0, 0)

    prev_pensize = turtle.pensize()
    turtle.pensize(0.5)

    for x in range(math.floor(llx)+1, math.ceil(urx)):
        turtle.penup()
        turtle.goto(x, math.floor(lly))
        turtle.color('grey50')
        turtle.write(str(x))
        turtle.goto(x, math.floor(lly) + 0.3)
        turtle.color('grey90')
        turtle.pendown()
        turtle.goto(x, math.ceil(ury))

    for y in range(math.floor(lly)+1, math.ceil(ury)):
        turtle.penup()
        turtle.goto(math.floor(llx), y)
        turtle.color('grey50')
        turtle.write(str(y))
        turtle.goto(math.floor(llx) + 0.3, y)
        turtle.color('grey90')
        turtle.pendown()
        turtle.goto(math.ceil(urx), y)

    turtle.update()
    turtle.speed(prev_speed)
    turtle.tracer(prev_tracer)
    turtle.pensize(prev_pensize)


def check_reload():
    '''Check if the file has changed, and if so, redraw the picture.
    
    Meant to be bound to a timer or event such as mouse or key click.
    Could also be used with the likes of watchdog/inotify, but that
    would pull in non-default libraries and make it platform dependent.
    '''

    global program_args
    global file_last_loaded

    file_last_updated = pathlib.Path(program_args.file).stat().st_mtime

    if file_last_updated > file_last_loaded:
        print(f"Redrawing, as file has changed on disk.")
        draw_picture_from_file()

    # We need to reschedule ourselves if we want to be called again
    turtle.ontimer(check_reload, program_args.reload_interval)

def draw_picture_from_file():
    global program_args
    global file_last_loaded

    file_last_loaded = pathlib.Path(program_args.file).stat().st_mtime

    with open(program_args.file, mode='rt', encoding='utf-8') as file_handle:
        document = json.load(file_handle)
        
        turtle.reset()
        turtle.tracer(0, 0)

        draw_picture(document,
            labels=program_args.draw_labels,
            grid=program_args.draw_grid)

        turtle.hideturtle()
        turtle.update()

def draw_picture(doc, labels=False, grid=False):
    '''Draw a Turtle-based document given a document that describes it.

    The document comes from a JSON document that has the following structure:

    {
        "name": "Jerry, from Tom & Jerry",
        "author": "Conor Kerr",
        "world_coordinates": {
            "llx": 0, "lly": 5, "urx": 20, "ury": 23
        },
        "elements": [
            {
                "id": "A",
                "type": "filled_path",
                "coords": [
                    [3, 15], [1, 19], [1, 20], [1.5, 21], [2, 21.5],
                    [3, 22], [4, 21.5], [5, 20], [5.5, 19], [5, 17.5],
                    [4, 16], [3, 15]
                ],
                "fill_color": "pink" 
            },
            {
                "id": "N",
                "type": "path",
                "coords": [
                    [3, 22], [5, 21.5], [5.5, 20.5], [6, 19.5], [7, 18],
                    [9, 19], [11, 19], [13, 18], [14, 19.5], [14.5, 20.5],
                    [15, 21.5], [17, 22]
                ]
            }
        ]
    }

    At the root of the document, the c(name) and c(author) fields are
    currently not used.

    The c(world_coordinates) dictionary species the lower-left and
    upper-right x,y coordinates as used by turtle.set_worldcoordinates()

    The main element in the document is the c(elements) list. Each
    element of the list is drawn in the order given; so items earlier
    in the list will appear behind items that come later.

    Each element in the c(elements) list is a dictionary of that contains
    the following keys:

      * an c(id), which is just for identifying each element and can be
        useful in diagnostics.

      * a c(type), which currently must be one of "path" or "filled_path".
        The only difference currently is that "filled_path" may specify
        a fill colour and works on the assumption that the shape described
        is enclosed (the start and end coordinate is the same)

      * a c(coords) list of x,y coordinates. Each item is a list (not a
        tuple, but this is only due to the data coming from JSON)
    '''
    
    turtle.getscreen().setworldcoordinates(
        llx = doc.get('world_coordinates').get('llx'),
        lly = doc.get('world_coordinates').get('lly'),
        urx = doc.get('world_coordinates').get('urx'),
        ury = doc.get('world_coordinates').get('ury'))
    
    turtle.title("{name} - by {author}".format(
        name = doc.get('name', 'Unnamed masterpiece'),
        author = doc.get('author', 'unknown artist')))

    # Grid lines on top are more useful when you have filled_paths
    # although they do look less pretty, so we turn off
    # any fill-colour when using the grid; as it makes it
    # easier to spot mistakes.
    #
    if grid is True:
        draw_grid(**doc.get('world_coordinates'))

    turtle.color('black')
    turtle.fillcolor('')

    normal_pensize = turtle.pensize()
    normal_pencolor = turtle.pencolor()

    for element in doc.get('elements'):

        assert element.get('type') in ['path', 'filled_path']

        turtle.penup()
        [start_x, start_y] = element.get('coords')[0]

        if labels is True:
            turtle.penup()
            turtle.goto(start_x, start_y)
            turtle.dot(15, 'yellow')
            turtle.goto(start_x - 0.05, start_y - 0.25)
            turtle.write(element.get('id'))

        turtle.goto(start_x, start_y)
        turtle.pensize(normal_pensize)
        turtle.color(normal_pencolor)
        turtle.pendown()

        turtle.pensize(element.get('pen_size', normal_pensize))
        turtle.color(element.get('pen_color', normal_pencolor))
        
        if element.get('type') == 'filled_path':
            turtle.begin_fill()
            turtle.fillcolor(element.get('fill_color', 'grey90'))

            if grid is True: 
                turtle.fillcolor('')

        for coord in element.get('coords')[1:]:
            turtle.goto(coord[0], coord[1])

        if element.get('type') == 'filled_path':
            turtle.end_fill()

    # Re-draw the labels last so a filled shape doesn't cover it
    if labels is True:
        for element in doc.get('elements'):
            [start_x, start_y] = element.get('coords')[0]
            turtle.penup()
            turtle.goto(start_x, start_y)
            turtle.dot(15, 'yellow')
            turtle.goto(start_x - 0.05, start_y - 0.25)
            turtle.write(element.get('id'))


def main():
    global program_args

    parser = argparse.ArgumentParser(
        description='use turtle to draw a coordinate picture')
    parser.add_argument(
        'file', metavar='FILENAME', type=str,
        help='JSON file that contains the image to display')
    parser.add_argument(
        '--draw-labels', dest='draw_labels', default=False,
        action=argparse.BooleanOptionalAction,
        help="Draw the 'id' of each element")
    parser.add_argument(
        '--draw-grid', dest='draw_grid', default=False,
        action=argparse.BooleanOptionalAction,
        help="Draw grid lines in the background")
    parser.add_argument(
        '--speed', dest='speed', metavar='SPEED', type=str, default='fastest',
        help='Draw speed; either fastest, fast, normal, slow or slowest')
    parser.add_argument(
        '--reload-interval', dest='reload_interval', metavar='ms', type=int, default=1_000,
        help='Check if file should be reloaded every ms milliseconds')
    program_args = parser.parse_args()

    if program_args.speed is not None:
        turtle.speed(speed=program_args.speed)

    turtle.onscreenclick(on_click_print_coords)
    turtle.ontimer(check_reload, program_args.reload_interval)

    draw_picture_from_file()
    turtle.done()

if __name__ == '__main__':
    main()
