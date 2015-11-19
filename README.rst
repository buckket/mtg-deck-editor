mtg-deck-editor
~~~~~~~~~~~~~~~

MtG Deck Editor is a deck editor for the card game Magic: The Gathering, that automatically fetches and displays pictures for the cards used. MtG Deck Editor is written in Python using GObject Introspection and GTK+ 3.

Features
--------
- Search autocompletion (uses DeckBrew API)
- Loading and saving decks as plain text files
- Sample hand window, including mulligans button
- Mana curve plot shows colored mana requirements

Screenshot
----------
.. image:: https://uncloaked.net/~loom/stuff/mtg_deck_editor.png

Installation
------------
1) Under Debian GNU/Linux, install major dependencies with:

.. code:: bash

    $ apt-get install gir1.2-gtk-3.0 python-gi-cairo python-matplotlib

2) Afterwards install this package simply via pip.

.. code:: bash

    $ pip install mtg-deck-editor

3) Now run ``mtg-deck-editor``. :)

Links
-----
- `website (upstream) <http://news.dieweltistgarnichtso.net/bin/mtg-deck-editor.html>`_
- `development version <https://github.com/buckket/mtg-deck-editor>`_
