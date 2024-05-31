Just playing around with some fun encoding strategies I thought of. Meant to be used on the classic Touhou Bad Apple music video, but theoretically can be used for any video, I tried to make it at least very easy to extend to work on any video.

For this first implementation, I made it work in a byte-aligned way which isn't the most efficient. But getting bit-packing to work will take a lot more time. But I did write an efficiency calculator based on the horizontal encoding of the video and given that the 512x384 6573 frame video I have goes from a 15.5mb to 10.2mb with byte aligned and theoretically around 8.2mb if I could write the bit-packed version it's really not that great.

Given the video's mostly vertical characters I also tested encoding the video vertically, and that makes the byte aligned version 8.46mb. And the theoretical bit-packed version would be around 7.2mb so the difference in savings there is a smidge less than last time.

Next step is to create a decoder to play the video file I made. We'll see how that goes!

Current byte-aligned file format:
```
File Header
bytes per dimension = 3 bits
bytes per color-count = 3 bits
whether constant first color (1) or per-frame (0) = 1 bit
constant first color, or ignored = 1 bit (with 1 byte color-size they're essentially equivalent)
width dimension
height dimension
REPEATING FRAME DATA:
IF per-frame first color, define now (1 or 0) = 1 byte
length of color (either first color or black) [repeat until end of frame]
```
