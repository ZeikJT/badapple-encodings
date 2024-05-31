import imageio_ffmpeg
import json

COLOR_VALUE_THRESHOLD = (255 * 3) / 2

vid = imageio_ffmpeg.read_frames('BadApple-niconico-rot.m4a')

frames = []

def is_white(r, g, b):
	return bool((r + g + b) > COLOR_VALUE_THRESHOLD)

vid_generator = enumerate(vid)
metadata = next(vid_generator)
print(metadata[1])
width = metadata[1]['size'][0]
height = metadata[1]['size'][1]

total_solid_frames = 0

for i, im in vid_generator:
	state = is_white(im[0], im[1], im[2])
	frame = [state, 0]
	index = 1
	for h in range(height):
		for w in range(width):
			idx = ((h * width) + w) * 3
			if state == is_white(im[idx], im[idx + 1], im[idx + 2]):
				frame[index] += 1
			else:
				state = not state
				frame.append(1)
				index += 1
	frames.append(frame)
	is_solid_frame = len(frame) == 2
	if is_solid_frame:
		total_solid_frames += 1
	print('processed frame %i, %r' % (i, is_solid_frame))
print('solid: %i' % total_solid_frames)
with open('data_vert.json', 'w') as f:
	json.dump({'metadata': {'w': width, 'h': height}, 'data': frames}, f)
