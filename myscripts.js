function playVideo(element) {
    const thumbnail = element;
    const video = thumbnail.nextElementSibling;
  
    thumbnail.style.display = 'none'; // Hide the thumbnail
    video.style.display = 'block';    // Show the video
    video.play();                     // Start playing the video
  }
  