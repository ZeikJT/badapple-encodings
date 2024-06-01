import json
import math
import sys

MAX_DIMENSION_BITS = 3
MAX_DIMENSION_BYTES = pow(2, MAX_DIMENSION_BITS) -1
MAX_COLOR_BITS = 3
MAX_COLOR_BYTES = pow(2, MAX_COLOR_BITS) - 1
MAX_COLOR_VALUE = pow(2, 8 * MAX_COLOR_BYTES) - 1

with open(sys.argv[1], 'r') as file:
    video_json = json.load(file)
metadata = video_json['metadata']

width = metadata['w']
height = metadata['h']
fps = metadata['fps']
print('%i x %i (%i frames)' % (width, height, len(video_json['data'])))

def get_byte_size(num):
    return (num.bit_length() + 7) // 8

def color_bytes_list(num, byte_size):
    byte_list = bytearray()
    max_value = pow(2, byte_size * 8) - 1
    fill_space = byte_size
    #print('color_bytes_list', bit_mask, num)
    num_byte_size = math.ceil(num.bit_length() / 8)
    if num_byte_size <= byte_size:
        byte_list += num.to_bytes(byte_size, 'big')
    else:       
        while num > 0:
            #print('masked_value', num & bit_mask)
            if num > max_value:
                byte_list += max_value.to_bytes(byte_size, 'big')
                byte_list += bytearray(byte_size)
                num -= max_value
            else:
                byte_list += num.to_bytes(byte_size, 'big')
                num = 0
    return byte_list

largest_dimension = width if width > height else height
largest_dimension_bytes = get_byte_size(largest_dimension)
if largest_dimension_bytes > MAX_DIMENSION_BYTES:
    # Shouldn't happen with JSON input, but good to sanity check in case inputs change
    print('dimension exceeds representable number')
    exit()

def calculate_bits(max_bits, spread):
    bits_used = 0
    max_value = pow(2, max_bits) - 1
    for count,numbers in spread.items():
        if max_bits >= count:
            bits_used += max_bits * len(numbers)
        else:
            for number in numbers:
                unit_cost = math.ceil(number / max_value)
                bits_used += (max_bits * unit_cost) + (max_bits * (unit_cost - 1))
    return bits_used

def find_optimal_bytes():
    bit_spread = {}

    def calculate_optimal(name, spread, bit_multiplier=1):
        # for count,numbers in sorted(spread.items(), key=lambda item: item[0]):
        #   print(count, 'bits', len(numbers))
        optimal = 0
        optimal_used = 0
        max_bits = max(spread.keys())
        for count in range(1, math.ceil(max_bits / bit_multiplier) + 1):
            used = calculate_bits(count * bit_multiplier, spread) // bit_multiplier
            if optimal_used == 0 or optimal_used > used:
                optimal = count
                optimal_used = used
            #print('%s used if max color is %i %s' % (name, count, name), used // bit_multiplier)
        #print('optimal %s:' % (name), optimal)
        return [optimal, optimal_used]

    print('calculating per-frame color size')
    # Use json
    per_frame_used = len(video_json['data']) # Starts here because this is the per-frame 1 byte cost of including a color size
    per_frame_optimal = {}
    for i,frame in enumerate(video_json['data']):
        #print('processing frame %i' % (i))
        per_frame_bits = {}
        for num in frame[1:]:
            # For bit calcs
            bit_size = num.bit_length()
            if bit_size in bit_spread:
                bit_spread[bit_size].append(num)
            else:
                bit_spread[bit_size] = [num]
            if bit_size in per_frame_bits:
                per_frame_bits[bit_size].append(num)
            else:
                per_frame_bits[bit_size] = [num]
        [optimal_bytes, optimal_bytes_used] = calculate_optimal('bytes', per_frame_bits, 8)
        per_frame_used += optimal_bytes_used
        per_frame_optimal[i] = optimal_bytes

    print('per-frame color size usage: %i bytes' % (per_frame_used))

    # Would be nice to do bit packing, but for now we'll stick with full bytes for simplicity
    # calculate_optimal('bits', bit_spread)
    print('calculate optimal constant color size')
    [optimal_const_bytes, optimal_const_bytes_used] = calculate_optimal('bytes', bit_spread, 8)
    print('optimal constant color size is %i bytes, usage: %i bytes' % (optimal_const_bytes, optimal_const_bytes_used))
    if optimal_const_bytes_used > per_frame_used:
        return [0, per_frame_optimal]
    else:
        return [optimal_const_bytes,{}]

[optimal_byte_size, per_frame_optimal] = find_optimal_bytes()

print("Optimal constant byte size: %i" % (optimal_byte_size))

with open(sys.argv[2] or 'output.bin', 'wb') as out:
    # Current File Header
    # bytes per dimension = 3 bits
    # bytes per color (if 0 do per-frame) = 3 bits
    # whether constant first color (1) or per-frame (0) = 1 bit [note that per frame starts with black]
    # constant first color, or ignored = 1 bit
    # width dimension
    # height dimension
    # frame rate = 1 byte
    out.write(bytearray([(largest_dimension_bytes << 5) | (optimal_byte_size << 2)]))
    out.write(width.to_bytes(largest_dimension_bytes, 'big'))
    out.write(height.to_bytes(largest_dimension_bytes, 'big'))
    out.write(fps.to_bytes(1, 'big'))
    # FRAME DATA:
    # IF per-frame byte per color, define now = 1 byte
    # IF per-frame first color, define now (1 or 0) = 1 byte
    # length of color (either first color or black) [repeat until end of frame]
    for i,frame in enumerate(video_json['data']):
        #print('processing frame %i' % i)
        out.write(frame[0].to_bytes(1, 'big')) # per-frame color
        optimal_bytes = optimal_byte_size
        if optimal_bytes == 0:
            optimal_bytes = per_frame_optimal[i]
            out.write(optimal_bytes.to_bytes(1, 'big'))
        for num in frame[1:]:
            out.write(color_bytes_list(num, optimal_bytes))

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
