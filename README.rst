mtg-deck-editor
~~~~~~~~~~~~~~~

MtG Deck Editor is a deck editor for the card game Magic: The Gathering, that automatically fetches and displays pictures for the cards used. MtG Deck Editor is written in Python using GObject Introspection and GTK+ 3.

Features
--------
- search autocompletion (uses DeckBrew API)
- loading and saving decks as plain text files
- sample hand window, including mulligans button
- mana curve plot shows colored mana requirements

Installation
------------
Under Debian GNU/Linux, install major dependencies with:

.. code:: bash

    $ apt-get install gir1.2-gtk-3.0 python-gi-cairo python-matplotlib

Afterwards install this package simply via pip.

.. code:: bash

    $ pip install mtg-deck-editor

Links
-----
- `website (upstream) <http://news.dieweltistgarnichtso.net/bin/mtg-deck-editor.html>`_
- `development version <https://github.com/buckket/mtg-deck-editor>`_
