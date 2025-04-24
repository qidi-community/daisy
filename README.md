# Oopsie-daisies... I forgot to put my build plate on!

Under construction, here be dragons...

This klipper plugin aims to help you prevent gouged beds, cracked nozzles and bent X axis rods by taking a peek at your webcam first and erroring out if it sees you have a missing plate or a print left forgotten in the printer.

minimal set of instructions:
```sh
cd ~
git clone https://github.com/qidi-community/daisy
./daisy/install.sh
```

upload the .tflite model to your printer config folder (look in releases of the repo)

put this into printer.cfg
```ini
[daisy]
stream_url: http://localhost/webcam/snapshot
model_path: /home/mks/printer_data/config/daisy.tflite
```

restart the printer, try using `CHECK_WEBCAM`.
