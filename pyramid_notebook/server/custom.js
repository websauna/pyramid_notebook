define([
  'base/js/namespace',
  'base/js/events',
  'base/js/utils'
], function(IPython, events, utils) {
    "use strict";

    events.on('app_initialized.NotebookApp', function() {

      var base_url = utils.get_body_data('base-url');

      // Remove default close item
      $("#kill_and_exit").remove();

      // Add customized close item
      $("#file_menu").append('<li id="shutdown" title="Shutdown and return to Pyramid"><a href="#">Shutdown</a></li>');

      $(document).on("click", "#shutdown", function() {
        console.log(base_url);
        window.location.href = base_url + "shutdown";
      });

   });
});