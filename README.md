scholarly.py
===========

scholarly.py is a module that allows you to retrieve author and publication information from [Google Scholar](https://scholar.google.com) in a friendly, Pythonic way.

Changes
-------

Note that because of the nature of web scraping, this project will be in **perpetual beta**.

### v0.1

* Initial release.

Requirements
------------

Requires [bibtexparser](https://pypi.python.org/pypi/bibtexparser/) and [Beautiful Soup](https://pypi.python.org/pypi/beautifulsoup4/).


Installation
------------
Use `pip`:

    pip install scholarly

Or clone the package:

    git clone https://github.com/OrganicIrradiation/scholarly.git


Usage
-----
Because `scholarly` does not use an official API, no key is required. Simply:

```python
import scholarly

print scholarly.search_author('Steven A. Cholewiak').next()
```

### Methods
* `search_author` -- Search for an author by name and return a generator of Author objects.

<pre><code>
    >>> search_query = scholarly.search_author('Manish Singh')
    >>> print search_query.next()
    {'_filled': False,
     'affiliation': u'Rutgers University, New Brunswick, NJ',
     'citedby': 2179,
     'email': u'@ruccs.rutgers.edu',
     'id': '9XRvM88AAAAJ',
     'interests': [u'Human perception',
                   u'Computational Vision',
                   u'Cognitive Science'],
     'name': u'Manish Singh',
     'url_citations': '/citations?user=9XRvM88AAAAJ&hl=en',
     'url_picture': '/citations/images/avatar_scholar_150.jpg'}
</code></pre>

* `search_keyword` -- Search by keyword and return a generator of Author objects.

<pre><code>
    >>> search_query = scholarly.search_keyword('Haptics')
    >>> print search_query.next()
    {'_filled': False,
     'affiliation': u'Stanford University',
     'citedby': 17867,
     'email': u'@cs.stanford.edu',
     'id': '4arkOLcAAAAJ',
     'interests': [u'Robotics', u'Haptics', u'Human Motion'],
     'name': u'Oussama Khatib',
     'url_citations': '/citations?user=4arkOLcAAAAJ&hl=en',
     'url_picture': '/citations/images/avatar_scholar_150.jpg'}
</code></pre>

* `search_pubs_query` -- Search for articles/publications and return generator of Publication objects.

<pre><code>
    >>> search_query = scholarly.search_pubs_query('The perception of physical stability of 3d objects The role of parts')
    >>> print search_query.next()
    {'_filled': False,
     'bib': {'abstract': u'Research on 3D shape has focused largely on the perception of local geometric properties, such as surface depth, orientation, or curvature. Relatively little is known about how the visual system organizes local measurements into global shape representations.  ...',
             'author': u'SA Cholewiak and M Singh and R Fleming\u2026',
             'title': u'The perception of physical stability of 3d objects: The role of parts',
             'url': 'http://www.journalofvision.org/content/10/7/77.short'},
     'id_scholarcitedby': '8373403526432059892',
     'source': 'scholar',
     'url_scholarbib': '/scholar.bib?q=info:9HH8oSRONHQJ:scholar.google.com/&output=citation&hl=en&ct=citation&cd=0'}
</code></pre>


Example
-----
Let's say I want to find out which papers cite an author's most cited paper.  First, we will retrieve an author's information and fill in the missing details:

```
    >>> search_query = scholarly.search_author('Steven A Cholewiak')
    >>> author = search_query.next().fill()
    >>> print author
    {'_filled': True,
     'affiliation': u'Postdoctoral Fellow, University of Giessen',
     'citedby': 72,
     'email': u'@psychol.uni-giessen.de',
     'id': '4bahYMkAAAAJ',
     'interests': [u'3D Shape',
                   u'Shape from Texture',
                   u'Shape from Shading',
                   u'Naive Physics',
                   u'Haptics'],
     'name': u'Steven A. Cholewiak',
     'publications': [<__main__.Publication object at 0x10f08ee50>,
                      <__main__.Publication object at 0x10f08eed0>,
                      <__main__.Publication object at 0x10f08ef50>,
                      <__main__.Publication object at 0x10f08efd0>,
                      <__main__.Publication object at 0x10f0a3090>,
                      <__main__.Publication object at 0x10f0a3110>,
                      <__main__.Publication object at 0x10f0a3190>,
                      <__main__.Publication object at 0x10f0a3210>,
                      <__main__.Publication object at 0x10f0a3290>,
                      <__main__.Publication object at 0x10f0a3310>,
                      <__main__.Publication object at 0x10f0a3390>,
                      <__main__.Publication object at 0x10f0a3410>,
                      <__main__.Publication object at 0x10f0a3490>,
                      <__main__.Publication object at 0x10f0a3510>,
                      <__main__.Publication object at 0x10f0a3590>,
                      <__main__.Publication object at 0x10f0a3610>,
                      <__main__.Publication object at 0x10f0a3690>,
                      <__main__.Publication object at 0x10f0a3710>,
                      <__main__.Publication object at 0x10f0a3790>,
                      <__main__.Publication object at 0x10f0a3810>,
                      <__main__.Publication object at 0x10f0a3890>,
                      <__main__.Publication object at 0x10f0a3910>,
                      <__main__.Publication object at 0x10f0a3990>,
                      <__main__.Publication object at 0x10f0a3a10>,
                      <__main__.Publication object at 0x10f0a3a90>,
                      <__main__.Publication object at 0x10f0a3b50>,
                      <__main__.Publication object at 0x10f0a3bd0>,
                      <__main__.Publication object at 0x10f0a3c50>],
     'url_citations': '/citations?user=4bahYMkAAAAJ&hl=en',
     'url_picture': '/citations?view_op=view_photo&user=4bahYMkAAAAJ&citpid=1'}
```

Here are the titles of the author's publications:

```
    >>> print [pub.bib['title'] for pub in author.publications]
    [u'A frequency-domain analysis of haptic gratings',
     u'Haptic identification of stiffness and force magnitude',
     u'Perception of intentions and mental states in autonomous virtual agents',
     u'Frequency analysis of the detectability of virtual haptic gratings',
     u'The perception of physical stability of 3d objects: The role of parts',
     u'Visual perception of the physical stability of asymmetric three-dimensional objects',
     u'Inferring the intentional states of autonomous virtual agents',
     u'Discrimination of real and virtual surfaces with sinusoidal and triangular gratings using the fingertip and stylus',
     u'The tipping point: Visual estimation of the physical stability of three-dimensional objects',
     u'The Dark Secrets of Dirty Concavities',
     u'Limits on the estimation of shape from specular surfaces',
     u'Predicting 3D shape perception from shading and texture flows',
     u'What happens to a shiny 3D object in a rotating environment?',
     u'Effects of varied spatial scale on perception of shape from shiny surfaces',
     u'Visually disentangling shading and surface pigmentation when the two are correlated',
     u'Perceptual regions of interest for 3D shape derived from shading and texture flows',
     u'Intra-and intermanual curvature aftereffect can be obtained via tool-touch',
     u'Towards a unified explanation of shape from shading and texture',
     u'Visual adaptation to physical stability of objects',
     u'Perception of Physical Stability of Asymmetrical Three-Dimensional Objects',
     u'Curvature aftereffect and visual-haptic interactions in simulated environments',
     u'On the edge: Perceived stability and center of mass of 3D objects',
     u'Perceiving intelligent action: Experiments in the interpretation of intentional motion',
     u'Living within a virtual environment populated by intelligent autonomous agents',
     u'Pain: Physiological mechanisms',
     u'Cutaneous perception',
     u'Perceptual estimation of variance in orientation and its dependence on sample size',
     u'Haptic stiffness identification and information transfer']
```

Here is the first publication:

```
    >>> pub = author.publications[0].fill()
    >>> print pub
    {'_filled': True,
     'bib': {'abstract': u'The detectability and discriminability of virtual haptic gratings were analyzed in the frequency domain. Detection (Exp. 1) and discrimination (Exp. 2) thresholds for virtual haptic gratings were estimated using a force-feedback device that simulated sinusoidal and square-wave gratings with spatial periods from 0.2 to 38.4 mm. The detection threshold results indicated that for spatial periods up to 6.4 mm (ie, spatial frequencies> 0.156 cycle/mm), the detectability of square-wave gratings could be predicted quantitatively from  ...',
             'author': u'Steven A Cholewiak and Kwangtaek Kim and Hong Z Tan and Bernard D Adelstein',
             'eprint': 'http://www.researchgate.net/publication/220413442_A_Frequency-Domain_Analysis_of_Haptic_Gratings/file/32bfe50f6a36736dc8.pdf',
             'number': u'1',
             'pages': u'3-14',
             'publisher': u'IEEE',
             'title': u'A frequency-domain analysis of haptic gratings',
             'url': 'http://ieeexplore.ieee.org/xpls/abs_all.jsp?arnumber=5210096',
             'volume': u'3',
             'year': 2010},
     'id_citations': '4bahYMkAAAAJ:u5HHmVD_uO8C',
     'id_scholarcitedby': '13781805114531538289',
     'source': 'citations',
     'url_citations': '/citations?view_op=view_citation&citation_for_view=4bahYMkAAAAJ:u5HHmVD_uO8C'}
```

Want to see the papers that cited that first publication?

```
    >>> print [citation.bib['title'] for citation in pub.citedby()]
    [u'Tactile and haptic illusions',
     u'Generating haptic texture models from unconstrained tool-surface interactions',
     u'Performance metrics for haptic interfaces',
     u"What you can't feel won't hurt you: Evaluating haptic hardware using a haptic contrast sensitivity function",
     u'Perceptual properties of vibrotactile material texture: Effects of amplitude changes and stimuli beneath detection thresholds',
     u'One hundred data-driven haptic texture models and open-source methods for rendering on 3d objects',
     u'Virtual Active Touch: Perception of Virtual Gratings Wavelength through Pointing-Stick Interface',
     u'Spectrum-based vibrotactile footstep-display for crinkle of fragile structures',
     u'Application of psychophysical techniques to haptic research',
     u'Just noticeable differences of low-intensity vibrotactile forces at the fingertip',
     u'Dynamic simulation of tool-mediated texture interaction',
     u'Improving the prediction of haptic impression user ratings using perception-based weighting methods: experimental evaluation',
     u'Spectrum-based synthesis of vibrotactile stimuli: active footstep display for crinkle of fragile structures',
     u'Discrimination of real and virtual surfaces with sinusoidal and triangular gratings using the fingertip and stylus',
     u'Development of a Multiple Contact Haptic Display with Texture-Enhanced Graphics',
     u'Modeling and Rendering Realistic Textures from Unconstrained Tool-Surface Interactions',
     u'The Physical Basis of Perceived Roughness in Virtual Sinusoidal Textures',
     u'Springer Series on Touch and Haptic Systems',
     u'Discrimination of Real and Virtual Surfaces with Sinusoidal and Triangular Gratings Using the Fingertip and Stylus',
     u'A Multilevel Customized Training Platform for Machining in Internet Environment',
     u'ROUGHNESS DISCRIMINATION OF TEXTURED GRATINGS',
     u'Virtual Active Touch: Perception of Virtual Gratings Wavelength through Pointing-Stick Interface',
     u'Distinguishability of periodic haptic stimuli in the frequency domain',
     u'Web-based virtual workplace environment for improving safety',
     u'Relationship between tactual roughness judgment and surface morphology of fabric by fingertip touching method',
     u'The human perception of haptic vibrations',
     u'Lossy Data Compression of Vibrotactile Material-Like Textures',
     u'Haptics as an Interaction Modality',
     u'\u57fa\u4e8e\u9891\u8c31\u5206\u6790\u7684\u7ec7\u7269\u7c97\u7cd9\u611f']
```


License
-------

The original code that this project was forked from was released by [Bello Chalmers](https://github.com/lbello/chalmers-web) under a 'Do What the Fuck You Want to Public License'. In keeping with this mentality, all code is released under the [Unlicense](http://unlicense.org/).