# SRS Recorder
This project aims to make debriefing DCS flights easier by providing SRS comms alongside the Tacview playback of a flight.

## Setup
In order to correctly determine the start and end time of a DCS mission, we need to install some hooks.
 1. Add the contents of `scripts\export.lua` to the end of your `Saved Games\DCS\Scripts\Export.lua` file
 2. Copy `scripts\srs_recorder.lua` to `Saved Games\DCS\Scripts\`

## Usage
1. Copy `config.ini.example` to `config.ini` and edit values as needed (in particular, the `output` value will likely need adjustment)
2. Run `srs.py` BEFORE slotting into a mission
3. When a mission is done, load the resulting `wav` files into Tacview using the `media` players
    * **NOTE**: The MediaPlayers in TacView *MUST* be pinned for audio to play with the track 

## Config
### SRS
**ip**

    IP address of the SRS server. Note that currently only 127.0.0.1 is supported.
**port**

    port SRS is listening on. SRS defaults to 5002, so unless the server changed it this should be fine.
**nick**

    Username to send to SRS. Displayed to the server admin (and no one else so far as I know).
**rx**

    Path to a file to play as the receiving audio effect. Defaults to the normal SRS sound, but can be anything..
**version**

    Version to report to the SRS server. 
**guid**

    GUID to use to report to the SRS server. Not sure what the purpose of this is.
### Recorder
**opus_dll**

    Path to an Opus DLL capable of decoding Opus packets. Defaults to the file used by SRS.
    You should not change this unless you're sure that you know what you're doing... and that I do.
    In short, probably don't change this unless you installed SRS to a non-default location.

**freq**

    A list of frequencies to record. Each frequency must be a number.
    The format is expected as:
        305.000 (for 305.000Mhz)
