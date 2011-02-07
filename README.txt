==================
infrae.testbrowser
==================

`infrae.testbrowser` is test browser for WSGI applications sharing the
same ideas than `zope.testbrowser`_. It only has lxml and
zope.interface as dependency.

.. contents::

API
===

Browser
-------

``infrae.testbrowser.browser.Browser``
   Test browser. You instantiate a new one by giving your WSGI
   application to test as arguments to the constructor. The
   application will be available via ``localhost``.

Example::

  >>> browser = Browser(MyWSGIApplication)

On the browser you have the following methods:

``open(url, method='GET', query=None, form=None, form_enctype='application/x-www-form-urlencoded')``
   Open the given `url`, with the given `method`. If query is
   provided, it will be encoded in the URL. If form is provided, it
   will be set as payload depending of `form_enctype`
   (`application/x-www-form-urlencoded` or `multipart/form-data`). An
   authentication can be provided in the URL (via
   ``user:password@localhost``). As the host part doesn't really have
   any meaning, you can directly specify a path as URL. It return the
   HTTP status code returned by the application.

``reload()``
   Reload the currently open URL (sending back any posting data).

``login(username, password=_marker)``
   Set an basic authorization header in the request to authenticate
   yourself with the given `username` and `password`. If `password` is
   not provided, `username` is used as password.

``set_request_header(key, value)``
   Add an header called `key` with the value `value` used while
   querying the application.
   Headers are set for all further queries.

``get_request_header(key)``
  Get the value of an header used while querying the
  application. Return None if there is no matching header.

``clear_request_headers()``
  Remove all sets headers used while querying the
  application. Authentication one included.

``get_link(content)``
  Return a link selected via content.

``get_form(name=None, id=None)``
  Return a form selected via its `name` or `id` attribute (at least
  one of them is required).

The following properties are helpful as well:

``url``
  Currently viewed URL, without the hostname part, but with query data
  and so.

``location``
  Currently viewed path.

``history``
  Last previously viewed URLs.

``method``
  Method used to view the current page.

``status``
  HTTP status for the currently viewed page.

``status_code``
  HTTP status code as an integer for the currently viewed page.

``content_type``
  Content type of the currently viewed page.

``headers``
  Dictionary like access to response headers.

``contents``
  Payload of the currently viewed page.

``html``
  If response was an HTML response, LXML parsed tree containing this
  last one.

``options``
  Access to browser options.


Browser options
---------------

The following options are attributes of the options object, example::

    >>> browser.options.handle_errors = False


``follow_redirect``
  Boolean indicating if a redirect must be automatically
  followed. Default to True.

``handle_errors``
  Set the WSGI flag ``wsgi.handleErrors`` in the WSGI
  environment. Default to True.

``cookie_support``
  Boolean indicating if we must support cookie. By default to
  True. **The cookie support is extremely limited for the moment**,
  just setting a cookie works.


Inspect
-------

The browser as an ``inspect`` attribute. You can register an Xpath
expression with it, and query them after on HTML pages::

  >>> browser.inspect.add('feedback', '//div[@class="feedback"]/span')
  >>> self.assertEqual(browser.inspect.feedback, ['Everything ok'])

  >>> browser.inspect.add('feedback', css='div.feedback span')
  >>> self.assertEqual(browser.inspect.feedback, ['Everything ok'])


``add(name, xpath=None, type='link', css=None)``
  Add an expression called `name` that can be used to inspect the HTML
  content of the browser using the `xpath` expression (or the `css`
  one). `type` can be:

  `text`
    The result would be a list containing the text of each matched
    element.

  `normalized-text`
    The result would be a list containing the text where whitespaces
    have been normalized for each matched element.

  `link`
    The result would be a list of links.


Macros
------

Macros let you add listing of action to do on the browser. An example
will speak by itself::

  >>> def create_content(browser, identifier, title):
  ...    form = browser.get_form('addform')
  ...    form.get_control('identifier').value = identifier
  ...    form.get_control('title').value = title
  ...    assert form.inspect.actions['save'].click() == 200

  >>> browser.macros.add('create', create_content)

Now you can create content with your browser::

  >>> browser.macros.create('test', 'Test Content')
  >>> browser.macros.create('othertest', 'Other Test Content')


Links
-----

Links have some useful attributes and methods:

``click()``
  Follow this link in the browser, and return the HTTP status code
  returned by the application.

``url``
  Target URL of the link.

``text``
  Text of the link.

As result of an inspect, links are pretty useful:

  >>> browser.inspect.add('tabs', '//div[@class="tabs"]/a', type="link")
  >>> self.assertEqual(browser.inspect.tabs, ['View', 'Edit'])
  >>> self.assertEqual(browser.inspect.tabs['view'].click(), 200)


Forms
-----

Forms have the following methods and attributes:

``name``
  Name of the form.

``action``
  URL where to form is posted.

``method``
  Method to use to post the form.

``enctype``
  Form enctype to use to post the form.

``accept_charset``
  Charset to which the form data will be encoded before being posted.

``controls``
  Dictionary containing all the controls of the form.

``inspect``
  Inspect attribute, working like the one of the browser. By default,
  ``inspect.actions`` is registered to return all the submit-like
  controls of the form.

``get_control(name)``
  Return the given form control by its name.

``submit(name=None, value=None)``
  Submit the form, potentially add the control name and the given
  value to the submission. This return the HTTP status code returned
  by the application.

Calling ``str(form)`` will only return the HTML code of the form.

Forms support all the known HTTP controls.

Form controls
~~~~~~~~~~~~~

For consistency, all form controls share the attributes:

``name``
  Name of the control.

``type``
  Type of control, like value of type attribute for input and tag name
  in other cases.

``value``
  Value stored in the control.

``multiple``
  Boolean indicating if the control store multiple value.

``options``
  If the value have to be chosen in a list of possible values, those
  are the possibilities.

``checkable``
  Boolean indicating if the control can be checked (i.e. is it a checkbox).

``checked``
  Boolean indicating if the control is checked (and so if the value
  will be sent if the control is checkable).


In addition action controls (like submit buttons, button), have:

``submit()``
  Submit the form with this action. This return the HTTP status code
  returned by the application.

``click()``
  Alias to ``submit()``.

For file control, you have to set as value the filename (i.e path to)
of the file you want to upload.

.. _zope.testbrowser: http://pypi.python.org/pypi/zope.testbrowser
