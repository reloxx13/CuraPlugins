# -*- coding: utf-8 -*-

import json
import re

from ..Script import Script


class VaryTempWithHeight(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        # Create settings as an object
        settings = {
            'name': 'Vary Temp With Height',
            'key': 'VaryTempWithHeight',
            'metadata': {},
            'version': 2,
            'settings': {
                'feet_height': {
                    'label': 'Feet height',
                    'description': (
					'Start Increment after feet.'
					),
                    'unit': 'mm',
                    'type': 'float',
                    'default_value': 1.90
                },
				'start_temperature': {
                    'label': 'Start Temperature',
                    'description': 'Initial nozzle temperature',
                    'unit': '°C',
                    'type': 'int',
                    'default_value': 225
                },
                'height_increment': {
                    'label': 'Height Increment',
                    'description': (
                        'Adjust temperature each time height param '
                        'changes by this much'
                    ),
                    'unit': 'mm',
                    'type': 'int',
                    'default_value': 10
                },
                'temperature_increment': {
                    'label': 'Temperature Decrement',
                    'description': (
                        'Decrease temperature by this much with each '
                        'height increment'
                    ),
                    'unit': '°C',
                    'type': 'int',
                    'default_value': 5
                }
            }
        }

        # Dump to json string
        json_settings = json.dumps(settings)
        return json_settings

    def execute(self, data):
        # Grab settings variables
        start_temp = self.getSettingValueByKey('start_temperature')
        height_inc = self.getSettingValueByKey('height_increment')
        temp_inc = self.getSettingValueByKey('temperature_increment')
        feet_height = self.getSettingValueByKey('feet_height')

        # Set our command regex
        cmd_re = re.compile((
            r'G[0-9]+\.?[0-9]* (?:F[0-9]+\.?[0-9]* )?X[0-9]+\.?[0-9]* '
            r'Y[0-9]+\.?[0-9]* Z([0-9]+\.?[0-9]*)'
        ))

        # Set initial state
        output = []
        new_temp = start_temp
        started = False
        z = 0.0

        for layer in data:
            output_line = ''
            for line in layer.split('\n'):
                # If we see LAYER:0, this means we are in the main layer code
                if 'LAYER:0' in line:
                    started = True

                # output any comment lines or pre-start lines
                # without modification
                if line.startswith(';') or not started:
                    output_line += '%s\n' % line
                    continue

                # Find the X,Y,Z Line (ex. G0 X60.989 Y60.989 Z1.77)
                match = cmd_re.search(line)

                # If we've found our line
                if match is not None:
                    output_line += ';TYPE:CUSTOM\n'
                    # Grab the z value
                    new_z = float(match.groups()[0])

                    # If our z value has changed
                    if new_z != z:
                        z = new_z - feet_height
                        if z == 0:
                            output_line += ';TEMP CHANGE\n'
                            output_line += 'M104 S%d\n' % start_temp
                        if z > 0:
                            # Determine new temperature
                            if z % height_inc == 0:
							    # If we hit a spot where we need to change the
								# temperature, then write the gcode command
                                new_temp = new_temp - temp_inc
                                output_line += ';TEMP CHANGE\n'
                                output_line += 'M104 S%d\n' % new_temp
                # output the current line
                output_line += '%s\n' % line
            # Append the current possibly modified layer to the output
            output.append(output_line)
        return output
