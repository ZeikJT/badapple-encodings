// Adapted from https://gist.github.com/addyosmani/5434533
function limitLoop(fps, fn) {
    let then = Date.now()
    const interval = 1000 / fps
 
    return (function loop(time){
        requestAnimationFrame(loop)
 
        const now = Date.now()
        const delta = now - then
 
        if (delta >= interval) {
            then = now - (delta % interval)
            fn()
        }
    }(0))
}

function uintFromBigEndian(uint8array, start, end) {
    let num = 0
    for (; start < end; start++) {
        num = num << 8
        num += uint8array[start]
    }
    return num
}

async function getByteReader(path) {
    const video_data = new Uint8Array(await fetch(path).then((response) => response.arrayBuffer()))
    let readIndex = 0;
    function read(byte_count) {
        if (byte_count == 0) throw new Error('trying to read 0 bytes?')
        if (byte_count == 1) {
            return video_data[readIndex++]
        }
        return uintFromBigEndian(video_data, readIndex, readIndex += byte_count)
    }
    return read
}

const WHITE = '#FFF'
const BLACK = '#000'
const COLOR_MAP = [
    BLACK,
    WHITE,
]

;(async function() {
    const read = await getByteReader('badapple_horiz.bin')
    const header = read(1)
    const dimension_size = header >> 5
    const fixed_color_size = (header >> 2) & 0b111
    const is_fixed_bg_color = (header >> 1) & 0b1
    const fixed_bg_color = header & 0b1
    const width = read(dimension_size)
    const height = read(dimension_size)
    const fps = read(1)
    //console.log(dimension_size, fixed_color_size, is_fixed_bg_color, fixed_bg_color, width, height, fps)
    const canvasElement = document.createElement('canvas')
    canvasElement.setAttribute('width', width)
    canvasElement.setAttribute('height', height)
    canvasElement.style.position = 'absolute'
    canvasElement.style.left = '50%'
    canvasElement.style.top = '50%'
    canvasElement.style.marginLeft = `-${width/2}px`
    canvasElement.style.marginTop = `-${height/2}px`
    const canvas2d = canvasElement.getContext("2d")
    document.body.appendChild(canvasElement)
    limitLoop(fps, () => {
        let colorIndex = is_fixed_bg_color ? fixed_bg_color : read(1)
        const color_byte_size = fixed_color_size || read(1)
        let x = 0
        let y = 0
        do {
            canvas2d.fillStyle = COLOR_MAP[colorIndex]
            let pixels = read(color_byte_size)
            while (x + pixels > width) {
                canvas2d.fillRect(x, y, width - x, 1)
                pixels -= width - x
                x = 0
                y += 1
            }
            if (pixels) {
                canvas2d.fillRect(x, y, pixels, 1)
                x += pixels
                if (x === width) {
                    x = 0
                    y += 1
                }
            }
            colorIndex = 1 - colorIndex
        } while (y < height)
    })
}())
