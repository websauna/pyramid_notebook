define(
  [
  'base/js/namespace',
  'base/js/promises',
  'base/js/utils'
  ], function (Jupyter, promises, utils) {
    promises.app_initialized.then(function (appname) {
      if (appname === 'NotebookApp') {
        var base_url = utils.get_body_data('base-url');

                // Remove default close item
                $("#close_and_halt").remove();

                // Add customized close item
                $("#file_menu").append('<li id="shutdown" title="Shutdown and return to Pyramid"><a href="#">Shutdown</a></li>');

                $(document).on("click", "#shutdown", function () {
                  console.log(base_url);
                  window.location.href = base_url + "shutdown";
                });
              }
            });
  });
