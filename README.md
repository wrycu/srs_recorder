# SRS Recorder
This project aims to make debriefing DCS flights easier by providing SRS comms alongside the Tacview playback of a flight.

## Setup
* This project relies on `DCS-gRPC` being installed, configured, and running during your session. Please be sure this is done prior to running the recorder or nothing will be recorded. Installation instructions can be found in [their repo](https://github.com/DCS-gRPC/rust-server).
* This project installs a Tacview AddOn which needs to be enabled
    1. Click the gear (AddOns)
    2. Enable/Disable AddOns
    3. `srs-recorder`

## Usage
### Limits
* Note that some aircraft-specific radios (e.g. the Hornet MIDS) may not properly record
* Note that this is intended to be installed on a client machine, not a dedicated server
### Steps
1. Copy `config.ini.example` to `config.ini` and edit values as needed (in particular, the `output` value will likely need adjustment)
2. Run `srs.py` BEFORE slotting into a mission
3. That's it! SRS comms should automatically be synced when loading the matching Tacview recording

## Config
### SRS
**ip**

    IP address of the SRS server.
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
