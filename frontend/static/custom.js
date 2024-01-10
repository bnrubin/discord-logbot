var $gallery = $('#gallery').imagesLoaded(function() {
  $gallery.masonry('layout');
});

setTimeout(function () {
  var msnry = new Masonry('#gallery');
  msnry.layout();
}, 100);

setTimeout(function () {
  var msnry = new Masonry('#gallery');
  msnry.layout();
}, 300);

setTimeout(function () {
  var msnry = new Masonry('#gallery');
  msnry.layout();
}, 1000);

setTimeout(function () {
  var msnry = new Masonry('#gallery');
  msnry.layout();
}, 5000);

new VenoBox({
  selector: '.venobox',
  fitview: true
});

