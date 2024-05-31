import json
import math
import sys

MAX_DIMENSION_BITS = 3
MAX_DIMENSION_BYTES = pow(2, MAX_DIMENSION_BITS) -1
MAX_COLOR_BITS = 3
MAX_COLOR_BYTES = pow(2, MAX_COLOR_BITS) - 1
MAX_COLOR_VALUE = pow(2, 8 * MAX_COLOR_BYTES) - 1

with open('data_vert.json', 'r') as file:
	video_json = json.load(file)
metadata = video_json['metadata']

width = metadata['w']
height = metadata['h']
print('%i x %i (%i frames)' % (width, height, len(video_json['data'])))

def get_byte_size(num):
	return (num.bit_length() + 7) // 8

def color_bytes_list(num, byte_size):
	byte_list = bytearray()
	bit_mask = pow(2, byte_size * 8) - 1
	fill_space = byte_size
	#print('color_bytes_list', bit_mask, num)
	while num > 0:
		#print('masked_value', num & bit_mask)
		byte_list += (num & bit_mask).to_bytes(byte_size, 'big')
		num = num >> 8 * byte_size
		fill_space -= byte_size
		if num > 0:
			byte_list += bytearray(byte_size)
	while fill_space > 0:
		byte_list = bytearray(1) + byte_list
		fill_space -= 1
	return byte_list

largest_dimension = width if width > height else height
largest_dimension_bytes = get_byte_size(largest_dimension)
if largest_dimension_bytes > MAX_DIMENSION_BYTES:
	# Shouldn't happen with JSON input, but good to sanity check in case inputs change
	print('dimension exceeds representable number')
	exit()

bit_spread = {}
byte_spread = {}

# Use json
for frame in video_json['data']:
	for num in frame[1:]:
		# For bit calcs
		bit_size = num.bit_length()
		if bit_size in bit_spread:
			bit_spread[bit_size].append(num)
		else:
			bit_spread[bit_size] = [num]
		# For byte calcs
		byte_size = get_byte_size(num)
		if byte_size in byte_spread:
			byte_spread[byte_size].append(num)
		else:
			byte_spread[byte_size] = [num]

def calculate_bits(max_bits):
	bits_used = 0
	max_value = pow(2, max_bits) - 1
	for count,numbers in bit_spread.items():
		if max_bits >= count:
			bits_used += max_bits * len(numbers)
		else:
			for number in numbers:
				unit_cost = (number.bit_length() + (max_bits - 1)) // max_bits
				bits_used += (max_bits * unit_cost) + (max_bits * (unit_cost - 1))
	return bits_used

def calculate_optimal(name, spread, bit_multiplier=1):
	for count,numbers in sorted(spread.items(), key=lambda item: item[0]):
		print(count, name, len(numbers))
	optimal = 0
	optimal_used = 0
	for count in range(1, max(spread.keys())+1):
		used = calculate_bits(count * bit_multiplier) // bit_multiplier
		if optimal_used == 0 or optimal_used > used:
			optimal = count
			optimal_used = used
		print('%s used if max color is %i %s' % (name, count, name), used)
	print('optimal %s:' % (name), optimal)
	return optimal

# Would be nice to do bit packing, but for now we'll stick with full bytes for simplicity
optimal_bit_size = calculate_optimal('bits', bit_spread)
optimal_byte_size = calculate_optimal('bytes', byte_spread, 8)

with open('badapple_vert.bin', 'wb') as out:
	# Current File Header
	# bytes per dimension = 3 bits
	# bytes per color-count = 3 bits
	# whether constant first color (1) or per-frame (0) = 1 bit
	# constant first color, or ignored = 1 bit
	# width dimension
	# height dimension
	out.write(bytearray([(largest_dimension_bytes << 5) | (optimal_byte_size << 2)]))
	out.write(width.to_bytes(largest_dimension_bytes, 'big'))
	out.write(height.to_bytes(largest_dimension_bytes, 'big'))
	# FRAME DATA:
	# IF per-frame first color, define now (1 or 0) = 1 byte
	# length of color (either first color or black) [repeat until end of frame]
	for i,frame in enumerate(video_json['data']):
		#print('processing frame %i' % i)
		out.write(frame[0].to_bytes(1, 'big'))
		for num in frame[1:]:
			out.write(color_bytes_list(num, optimal_byte_size))

##########################################
# Ideal bit-packed File header, maybe another time
# bit count per dimension = 4 bits
# color-run-length bit count = 5 bits
# whether constant first color or per-frame = 1 bit
# IF constant first color, define now = 1 bit (or 0 bit)
# FRAME DATA:
# IF per-frame first color, define now = 1 bit (or 0 bit)
# length of color
# [repeat until end of frame reached]
