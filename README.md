# Oopsie-daisies... I forgot to put my build plate on!

Under construction, here be dragons...

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
