# micro-jpeg-visualizer

##Intro

This a a JPEG visualizer in just ~~280~~ 250 lines in easy to read Python 3.0 code.

##Features

- No external libraries were used
- Friendly code can be easily ported to any other languages and embedded devices
- It works with JPG's that are made of 8x8 blocks and 3 channels (Y, Cr, Cb).
- Other formats are easy to add though.
- Its slow, due to the IDTC, which is done by brute force
- I'm sharing the code hoping this may help others.

Feel free to drop me a mail if you find this useful :-)

##Funny Facts

- I used notepad and debugged it using print's
- I used python because it was the handiest thing I had
- I wrote it just learn something hard
- It took me 3 evenings to finish it up
- the most difficult part was handling the run length encoding that I had to reverse engineer myself.
- What an amazing feeling to see such a simple piece of code displaying a pic!

##Credits

by Raul Aguaviva

This project wouldn't have been possible without the hard work of these folks:

- Calvin Hass for his excellent web page http://www.impulseadventure.com/
- The editors of the wikipedia JPEG article.
