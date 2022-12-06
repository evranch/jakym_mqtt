# jakym_mqtt

A simple wrapper allowing control of jakym via MQTT. Put your MQTT broker in "server" at the top.

Writable topics:

- music/youtube - Search for a song title and play it. Or start the command with "pl" to play a Youtube playlist.

The following respond to an empty message:

- music/next
- music/previous
- music/pause/set
- music/play/set

Published topics:

- music/pause
- music/play
- music/state - What's going on in the background
- music/song - Currently playing song

For advanced use:

- music/raw will just dump the payload string right into jakym. Use with care.
