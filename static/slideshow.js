const slideshow = (function () {
  let currentIndex = 0;
  let slides = [];
  let totalSlides = 0;
  let shuffledIndices = [];
  let showAlbum = false;
  let slideshowClockRatio = 0;
  let transitionSeconds = 0;
  let showRow = null;
  let lastShown = "slideshow";

  function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]];
    }
  }

  function initShuffledIndices() {
    shuffledIndices = [...Array(totalSlides).keys()];
    shuffleArray(shuffledIndices);
  }

  function setShowAlbum(state) {
    showAlbum = state;
    if (!showAlbum) {
      showRow(lastShown);
    }
  }

  function showNextSlide() {
    if (showAlbum) {
      return;
    }

    console.log("slideshowClockRatio: " + slideshowClockRatio);

    if (Math.random() < slideshowClockRatio) {
      console.log("showing clock");
      lastShown = "clock";
      showRow(lastShown);
    } else {
      console.log("showing next slide");
      lastShown = "slideshow";
      showRow(lastShown);
      slides[shuffledIndices[currentIndex]].classList.remove("active");
      currentIndex++;
      if (currentIndex >= totalSlides) {
        currentIndex = 0;
        shuffleArray(shuffledIndices);
      }
      slides[shuffledIndices[currentIndex]].classList.add("active");
    }
  }

  function init(config) {
    slideshowClockRatio = config.slideshowClockRatio;
    transitionSeconds = config.transitionSeconds;
    showRow = config.showRow;

    slides = document.querySelectorAll(".slide");
    totalSlides = slides.length;

    initShuffledIndices();
    slides[shuffledIndices[0]].classList.add("active");
    showNextSlide();
    setInterval(showNextSlide, transitionSeconds * 1000);
  }

  return {
    init: init,
    showNextSlide: showNextSlide,
    setShowAlbum: setShowAlbum,
  };
})();
