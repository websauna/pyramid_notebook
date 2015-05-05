

def get_or_create_notebook_process(username, **kwargs):
    """Gets a Notebook session for logged in user.

    :param kwargs: Extra IPython Notebook start arguments

    :return:
    """



def ipython_proxy(request):
    """Pyramid view which proxies all HTTP request to IPython Notebook process.

    Make access right check.
    """
