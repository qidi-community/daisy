#!/usr/bin/python3
import tensorflow as tf
import requests
import numpy as np
import os
from PIL import Image

class Daisy:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object("gcode")

        # printer.cfg inputs
        self.stream_url = config.get('stream_url')
        self.model_path = config.get('model_path')
        self.img_height = config.getint('img_height', 550)
        self.img_width = config.getint('img_width', (self.img_height // 9 * 16))
        self.debug = config.getboolean('debug', False)
        self.cancel_on_error = config.getboolean('cancel_on_error', True)
        self.cancel_on_nok = config.getboolean('cancel_automatically', True)
        self.enable_xy_conditioning = config.getboolean('enable_xy_conditioning', False)
        self.clear_view_x = config.getint('clear_view_x', 0)
        self.clear_view_y = config.getint('clear_view_y', 0)

        # internal use variables
        self.class_labels = ["plate found", "missing plate", "print left"]

        # Register the custom G-code commands
        self.gcode.register_command("CHECK_WEBCAM", self.cmd_check_webcam, desc="Check if there is an object on the bed or if the plate was forgotten")


    def cmd_check_webcam(self, gcmd):
        def cancel_print():
            self.gcode.respond_info(f"Daisy triggered a print cancellation.")
            print_manager = self.printer.lookup_object("print")
            print_manager.cancel_print()

        def xy_conditioning():
            self.gcode.respond_info(f"Daisy triggered a XY homing for a better view of the area.")

            toolhead = self.printer.lookup_object('toolhead')
            curtime = self.printer.get_reactor().monotonic()
            kin_status = toolhead.get_kinematics().get_status(curtime)

            # conditionally home XY axis if they aren't homed
            if 'x' not in kin_status['homed_axes'] and 'y' not in kin_status['homed_axes']:
                self.gcode.run_script_from_command('G28 XY')

            # move to the spot with the clear view
            self.gcode.run_script_from_command("G1 X%d Y%d".format(self.clear_view_x, self.clear_view_y))


        def capture_image():
            # Capture the image from crowsnest/webcamd
            response = requests.get(self.stream_url, stream=True)
            response.raise_for_status()  # Raise an exception for bad responses
            img = Image.open(response.raw).resize((self.img_width, self.img_height))
            response.raise_for_status()  # Raise an exception for bad responses
            if img is not None:
                if self.debug:
                    self.gcode.respond_info(f"Current bed image captured")
            else:
                self.gcode.respond_info("Error: Failed to capture image")
                if self.cancel_on_error:
                    cancel_print()
            return img


        def run_inference(interpreter, img):
            # Get input and output details
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()

            input_data = np.expand_dims(np.array(img, dtype=np.float32) / 255.0, axis=0)

            # Set the input tensor
            interpreter.set_tensor(input_details[0]['index'], input_data)

            # here happens inference
            interpreter.invoke()

            # Get the output tensor
            output_data = interpreter.get_tensor(output_details[0]['index'])

            # Get predicted label
            predicted_label = np.argmax(output_data)
            confidence = np.max(output_data)

            return predicted_label, confidence

        try:

            # condition XY if it's enabled
            if self.enable_xy_conditioning:
                xy_conditioning()

            # Load the TFLite model
            interpreter = tf.lite.Interpreter(model_path=self.model_path)
            interpreter.allocate_tensors()

            predicted_label, confidence = run_inference(interpreter, capture_image())

            # if the model returned low confidence level, perform xy conditioning and redo
            if confidence < 0.9:
                xy_conditioning()
                predicted_label, confidence = run_inference(interpreter, capture_image())

            # the label for 0 is the desired empty plate
            if predicted_label != 0:
                self.gcode.respond_info(f"Daisy detected a problem: " + self.class_labels[predicted_label])
                if self.cancel_on_nok:
                    cancel_print()
            else:
                self.gcode.respond_info(f"Daisy detected no issues!")
                return


        except Exception as e:
            self.gcode.respond_info(f"Internal error in the ai plate detection plugin: {str(e)}")
            if self.cancel_on_error:
                cancel_print()

def load_config(config):
    return Daisy(config)