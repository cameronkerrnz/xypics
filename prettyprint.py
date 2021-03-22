#!/usr/bin/env python

import json
import argparse
import math
import os

def pretty_coord(x, y):

    def pretty(n):
        if n % 1 == 0.5:
            return f"{math.floor(n)} ½"
        else:
            return f"{math.floor(n)}"
    
    return f"({pretty(x)}, {pretty(y)}) "

def render_html(doc, output):
    '''Output an HTML description of the coordinates used.

    Being HTML, the styled text can then be copy-pasted into
    a Google Doc or similar.

    The implementation is deliberately very very simple (ugly, even).

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
    
    output.write('''
    <!DOCTYPE HTML>
    <html>
        <head>
            <title>{name} - by {author}</title>
            <meta charset = "UTF-8" />
        </head>
        <body>
            <h1>{name}</h1>
            <p>by {author}</p>

    '''.format(
        name = doc.get('name', 'Unnamed masterpiece'),
        author = doc.get('author', 'unknown artist')))

    for element in doc.get('elements'):

        output.write('''<p><b>{id}</b>: '''.format(
            id = element.get('id')
        ))

        for coord in element.get('coords'):
            output.write(pretty_coord(coord[0], coord[1]))

        if element.get('type') == 'filled_path':
            output.write(''' Colour <span style="background-color: {colour}">{colour}</span></p>'''.format(
                colour = element.get('fill_color')))

        output.write('''</p>''')

    output.write('''
    </body>
    </html>
    ''')

def html_filename(fn):
    (root, ext) = os.path.splitext(fn)
    return f"{root}.html"

def main():

    parser = argparse.ArgumentParser(
        description='make simple html version of a coordinate picture')
    parser.add_argument(
        'files', metavar='FILENAME', type=str, nargs='+',
        help='JSON file that contains the image to display')
    args = parser.parse_args()

    for input_fn in args.files:
        with open(input_fn, mode='rt', encoding='utf-8') as input:
            with open(html_filename(input_fn), mode='wt', encoding='utf-8') as output:
                document = json.load(input)
                render_html(document, output)

if __name__ == '__main__':
    main()
