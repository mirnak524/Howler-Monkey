# Howler Monkey  
A small desktop overlay made using Qt Widgets that takes input from the default microphone and displays a monkey who gets angier as you get louder.

**Highlights**
- Live mic monitoring
- Four monkey moods
- Arc meter that lights up with the volume to convey volume in more direct manner
- Frameless, draggable, and transparent to be as unobtrusive as possible

 ![demo](assets\howler-monkey.gif)

## How it Works
A background thread captures audio (44.1 kHz, 16-bit mono) and computes the RMS of each 1024-sample chunk. The RMS is converted to a decibel value so it can be used for volume. The widget polls the latest reading every 50 ms and:
1. Normalizes it to 0-1 (between `db_min` and `db_max`)
2. Selects the appropriate monkey image based on thresholds
3. Lights up the matching number of segments
