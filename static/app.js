var socket = io.connect(location.hostname + ":" + location.port);

function show_row(id) {
  console.log("Showing row:", id);
  let rows = document.getElementsByClassName("mytab");
  for (let i = 0; i < rows.length; i++) {
    rows[i].classList.add("d-none");
  }
  if (id !== null) document.getElementById(id).classList.remove("d-none");
}


function getFonteSize(
  text,
  minFontSize = 30,
  maxFontSize = 100,
  boxWidth = 380,
  boxHeight = 160,
) {
  // Create an off-screen canvas to measure text
  const canvas = document.createElement("canvas");

  canvas.width = document.getElementById("album-info").width;
  canvas.height = document.getElementById("album-info").height / 3;

  const context = canvas.getContext("2d");

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
    const textHeight =
      metrics.actualBoundingBoxAscent && metrics.actualBoundingBoxDescent
        ? metrics.actualBoundingBoxAscent + metrics.actualBoundingBoxDescent
        : mid;

    // Check if both dimensions fit within the box.
    if (textWidth <= boxWidth && textHeight <= boxHeight) {
      bestFit = mid; // current font size works; try a larger one
      minFontSize = mid + 1;
    } else {
      maxFontSize = mid - 1; // too big, try a smaller font size
    }
  }

  bestFit = Math.min(180, bestFit);
  return bestFit;
}

function updateScalingVariables(xSize = 1024, ySize = 600) {
  const root = document.documentElement;

  console.log("xsize: " + xSize);
  console.log("ysize: " + ySize);

  // Swap dimensions for portrait mode
  if (screen.width < screen.height) {
    const temp = xSize;
    xSize = ySize;
    ySize = temp
  }

  // Get screen resolution in real pixels
  const xPixel = screen.width * window.devicePixelRatio;
  const yPixel = screen.height * window.devicePixelRatio;

  // Aspect correction for non-square pixels
  const pixelAspect = xPixel / yPixel;
  const physicalAspect = xSize / ySize;
  const aspectAdjustment = pixelAspect / physicalAspect;

  // Get actual screen dimensions in CSS pixels
  const screenWidth = window.innerWidth;
  const screenHeight = window.innerHeight;
  const screenAspect = screenWidth / screenHeight;
  const imageAspect = pixelAspect / aspectAdjustment;

  // Compute zoom to fill screen
  const scaleZoom = screenAspect > imageAspect
    ? screenWidth / (screenHeight * imageAspect)
    : screenHeight / (screenWidth / imageAspect);

  // Update CSS variables
  root.style.setProperty('--aspect-adjustment', aspectAdjustment);
  root.style.setProperty('--scale-zoom', scaleZoom);
  root.style.setProperty('--scale-x', aspectAdjustment * scaleZoom);
  root.style.setProperty('--scale-y', scaleZoom);

  console.log("Aspect ratio: " + root.style.getPropertyValue('--aspect-adjustment'));
  console.log("Scale zoom: " + root.style.getPropertyValue('--scale-zoom'));
  console.log("Scale x: " + root.style.getPropertyValue('--scale-x'));
  console.log("Scale y: " + root.style.getPropertyValue('--scale-y'));
}

function on_window_load(
  slideshow_clock_ratio,
  transition_seconds,
  clock_offset,
  clock_size,
) {
  slideshow.init({
    showRow: show_row,
    slideshowClockRatio: slideshow_clock_ratio,
    transitionSeconds: transition_seconds,
  });

  socket.on("connection", function () {
    console.log("Socket connected");

    // Trigger initial album update
    setTimeout(function () {
      console.log("Triggering album update");
      socket.emit("trigger_album_update");
    }, 2000);
  });

  socket.on("album_update", function (data) {
    console.log("Album update received:", data);

    if (data.url !== undefined) {
      console.log("updating album");

      console.log(data.state);
      if (data.state === "playing") {
        document.getElementById("album-artist").style.fontSize = "1px";
        document.getElementById("album-title").style.fontSize = "1px";
        document.getElementById("album-track").style.fontSize = "1px";

        document.getElementById("album-info").classList.remove("d-none");
        document.getElementById("album-img").src = data.url;
        document.getElementById("album-artist").innerText = data.artist;
        document.getElementById("album-title").innerText = data.title;
        document.getElementById("album-track").innerText = data.track;

        let size = getFonteSize(
          document.getElementById("album-artist").innerText,
          40,
          80,
        );
        document.getElementById("album-artist").style.fontSize = size + "px";

        let size2 = getFonteSize(
          document.getElementById("album-title").innerText,
          30,
          40,
        );
        let size3 = getFonteSize(
          document.getElementById("album-track").innerText,
          30,
          40,
        );
        size = Math.min(size2, size3);
        document.getElementById("album-title").style.fontSize = size + "px";
        document.getElementById("album-track").style.fontSize = size + "px";
      }
    }

    if (data.display_state !== undefined && data.display_state === false) {
      show_row(null);
    } else if (data.state === "playing" || data.state === "loading") {
      console.log("showing album");
      show_row("album");
      slideshow.setShowAlbum(true);
    } else {
      console.log("showing slideshow");
      slideshow.setShowAlbum(false);
    }
  });

  socket.on("response", function (data) {
    console.log("Response received:", data);
  });

  socket.on("disconnect", function () {
    console.log("Socket disconnected");
  });


  // Start the clock
  if (slideshow_clock_ratio > 0) {
    const clockContainer = document.getElementById("clock");
    const canvas = document.createElement("canvas");

    const width =
      window.innerWidth ||
      document.documentElement.clientWidth ||
      document.body.clientWidth;

    const height =
      window.innerHeight ||
      document.documentElement.clientHeight ||
      document.body.clientHeight;

    if (clock_offset > 0)
      clockContainer.style.setProperty("padding-top", clock_offset + "px");

    canvas.id = "clockCanvas";
    canvas.width = Math.round(Math.min(width, height) * 0.9);
    if (clock_size > 0) canvas.width = Math.min(clock_size, canvas.width);

    canvas.height = canvas.width;
    canvas.style.margin = "auto";

    clockContainer.appendChild(canvas);
    new AnalogClock("clockCanvas");
    console.log("AnalogClock");
  }
}
