define([
  'base/js/namespace',
  'base/js/events'
], function(IPython, events) {
   events.on('app_initialized.NotebookApp', function() {

     // Executed when shell is open
     $("#kill_and_exit").remove();

     $("#file_menu").append('<li id="shutdown" title="Shutdown and return to Pyramid"><a href="#">Shutdown</a></li>');

     $(document).on("click", "#shutdown", function() {
       alert("Foobar");
     });

   });
});