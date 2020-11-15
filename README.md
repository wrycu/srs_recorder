# SRS Recorder
This project aims to make debriefing DCS flights easier by providing SRS comms alongside the tacview playback of a flight.
## Setup
In order to correctly determine the start and end time of a DCS mission, we need to install some hooks.
 1. Add the contents of `scripts\export.lua` to the end of your `Saved Games\DCS\Scripts\Export.lua` file
 2. Copy `scripts\srs_recorder.lua` to `Saved Games\DCS\Scripts\`

## Usage
1. After setup, be sure to run `srs.py` BEFORE loading a mission

