function playPause() {
    var video = document.getElementById('video-player');
    if (video.paused) {
        video.play();
    } else {
        video.pause();
    }
}