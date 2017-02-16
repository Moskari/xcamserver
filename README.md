# xcamserver

## Synopsis

This Python 3 package is makes the xevacam camera control library a (local) web server controllable via REST API. Camera frames are streamed to sockets.


## Usage
Start server with `python run.py`


REST API
Every command returns metadata json.
-------
/init  ; POST Initializes camera and sets up server for streaming.
/start ; POST Starts the camera and begins streaming data to socket.
/stop  ; POST Stops the camera.
/close ; POST Closes camera and server.
/meta  ; GET  Returns current state and camera properties in json.
-------
METADATA fields:
-------
byte order     ; Byte order of data words. 1 for MSB first and 0 for LSB.
data type      ; String for stream pixel data type. I.e. u2 = unsigned 16 bit int.
error          ; Error description string, otherwise nul
frame_size     ; Size of frame in bytes.
height         ; Height of the image in pixels.
width          ; Width of the image in pixels.
interleave     ; How data is interleaved in case of spectral data. bil, bsq or bip. For line scanner it is bil.
status         ; Current status of the server. CLOSED, STOPPED, STARTING, RUNNING.
stream_address ; Address to the stream.


## Installation

Tested only with Python 3.5 (Windows). Flask and xevacam are required.

Install with pip:
`pip install <directory path to setup.py>`


## License

The MIT License (MIT)

**Disclaimer**
The author disclaims all responsibility for possible damage to equipment and/or people. Use the software with your own risk.
