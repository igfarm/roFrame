
var socket = io.connect(location.hostname + ':' + location.port );
socket.on('connection', function() {
    console.log('Socket connected');

});

function show_row(id) {
        console.log('Showing row:', id);
        let rows = document.getElementsByClassName('mytab');
        for (let i = 0; i < rows.length; i++) {
            rows[i].classList.add('d-none');
        }
        document.getElementById(id).classList.remove('d-none');
    }

// Trigger initial album update
setTimeout(function() {
        console.log('Triggering album update');
        socket.emit('trigger_album_update'); 
    }, 2000);

socket.on('album_update', function(data) {
    console.log('Album update received:', data)

    if (data.url !== undefined) {
        console.log("updating album");

        console.log(data.state);
        if (data.state === 'playing') {
            document.getElementById('album-artist').style.fontSize = '1px';
            document.getElementById('album-title').style.fontSize = '1px';
            document.getElementById('album-track').style.fontSize = '1px';

            document.getElementById('album-info').classList.remove('d-none');
            document.getElementById('album-img').src = data.url;
            document.getElementById('album-artist').innerText = data.artist;
            document.getElementById('album-title').innerText = data.title;
            document.getElementById('album-track').innerText = data.track;

            let size = getFonteSize(document.getElementById('album-artist').innerText, 40, 80);
            document.getElementById('album-artist').style.fontSize = size + 'px';

            let size2 = getFonteSize(document.getElementById('album-title').innerText, 30, 40);
            let size3 = getFonteSize(document.getElementById('album-track').innerText, 30, 40);
            size = Math.min(size2, size3);
            document.getElementById('album-title').style.fontSize = size + 'px';
            document.getElementById('album-track').style.fontSize = size + 'px';
        }
    }

    if (data.state === 'playing' || data.state === 'loading') {
        console.log("showing album");
        show_row('album');
        slideshow.setShowAlbum(true);
    }
    else {
        console.log("showing slideshow");
        slideshow.setShowAlbum(false);
    }
});

socket.on('response', function(data) {
    console.log('Response received:', data);
});

socket.on('disconnect', function() {
    console.log('Socket disconnected');
});

function getFonteSize(text, minFontSize=30, maxFontSize = 100, boxWidth = 380, boxHeight = 160) {
    // Create an off-screen canvas to measure text
    const canvas = document.createElement('canvas');

    canvas.width = document.getElementById('album-info').width;
    canvas.height = document.getElementById('album-info').height/3

    const context = canvas.getContext('2d');

    // Set up our search bounds
    let bestFit = minFontSize;

    while (minFontSize <= maxFontSize) {
        const mid = Math.floor((minFontSize + maxFontSize) / 2);
        // Set the context font. Using sans-serif as required.
        context.font = `${mid}px sans-serif`;
        
        // Measure text width and try to approximate height.
        const metrics = context.measureText(text);
        const textWidth = metrics.width;
        // If available, use actual bounding boxes for height; otherwise, fall back to the font size.
        const textHeight = (metrics.actualBoundingBoxAscent && metrics.actualBoundingBoxDescent)
        ? metrics.actualBoundingBoxAscent + metrics.actualBoundingBoxDescent
        : mid;
        
        // Check if both dimensions fit within the box.
        if (textWidth <= boxWidth && textHeight <= boxHeight) {
            bestFit = mid;         // current font size works; try a larger one
            minFontSize = mid + 1;
        } else {
            maxFontSize = mid - 1;   // too big, try a smaller font size
        }
    }

    bestFit = Math.min(180, bestFit); 
    return bestFit;
}

function on_window_load(
    slideshow_clock_ratio,
    transition_seconds,
    clock_offset,
    clock_size,
) {
    slideshow.init({
        showRow: show_row,
        slideshowClockRatio:  slideshow_clock_ratio ,
        transitionSeconds:  transition_seconds
    });

    // Start the clock
    if (slideshow_clock_ratio > 0) {
        const clockContainer = document.getElementById("clock");
        const canvas = document.createElement("canvas");

        const width =
            window.innerWidth ||
            document.documentElement.clientWidth ||
            document.body.clientWidth;

        const height = window.innerHeight ||
            document.documentElement.clientHeight ||
            document.body.clientHeight;


        if (clock_offset > 0)
            clockContainer.style.setProperty("padding-top", clock_offset + "px");

        canvas.id = "clockCanvas";
        canvas.width = Math.round(Math.min(width, height) * 0.9);
        if (clock_size > 0)
            canvas.width = Math.min(clock_size, canvas.width);


        canvas.height = canvas.width;
        canvas.style.margin = "auto";
/*
        canvas.style.display = "block";
        canvas.style.background = "#333";
        canvas.style.border = "2px solid #fff";
        canvas.style.borderRadius = "50%";
*/

        clockContainer.appendChild(canvas);
        new AnalogClock("clockCanvas");
        console.log('AnalogClock')
    }
}