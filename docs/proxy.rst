Proxies and Selenium
====================

Using a proxy
-------------

Just run ``get_scholarly_instance(use_proxy = True)``. You will obtain
a scholarly instance that uses a proxy. We strongly recommend using ToR. 
Simply install ToR browser and the script will handle the usage.
\*Note: this is a completely optional - opt-in feature'


.. code:: python

        >>> scholarly = get_scholarly_instance(use_proxy = True)
        >>> # If proxy is correctly set up, the following runs through it
        >>> scholarly.search_author('Steven A Cholewiak')


Using Selenium
--------------

Just run ``get_scholarly_instance(use_selenium = True)``. You will
obtain a scholarly instance that uses selenium instead of ``requests``
for web requests. This can be used to manually input captchas if asked
for by Google Scholar. Selenium will open a browser and, if you are using
ToR, the node will be automatically refreshed to avoid captchas.
\*Note: this is a completely optional - opt-in feature'


.. code:: python

        >>> scholarly = get_scholarly_instance(use_selenium = True)
        >>> # You will see a remote controled chrome window
        >>> scholarly.search_author('Steven A Cholewiak')
