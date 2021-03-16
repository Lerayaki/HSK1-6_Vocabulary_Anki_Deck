import urllib.request
import json
import random
import genanki

class AppURLopener(urllib.request.FancyURLopener):
    version = "Mozilla/5.0"

class HanziWord(object):
    def __init__(self, hanzi, pinyin, meaning):
        self.hanzi = hanzi
        self.pinyin = pinyin
        self.meaning = meaning

contentCharset = None
hanziDict = {}

def contentLoader():
    global contentCharset

    for level in range(1,7):
        url = 'https://hsk.academy/en/hsk-{}-vocabulary-list'.format(level)
        print('Loading {} ...'.format(url))
        
        opener = AppURLopener()
        response = opener.open(url)
        contentCharset = response.headers.get_content_charset()
        content = response.read().decode(contentCharset)

        fname = "raw-hsk-{}-vocabulary-list".format(level)
        print('Writing content to {} ...'.format(fname))

        f = open(fname, "w", encoding=contentCharset)
        f.write(content)
        f.close()

def processContent():
    global contentCharset
    global hanziDict

    for level in range(1,7):
        currentLevelList = []
        nwords = 0
        fname = "raw-hsk-{}-vocabulary-list".format(level)
        line = None
        print('Extracting data from {} ...'.format(fname))
        f = open("raw-hsk-{}-vocabulary-list".format(level), "r", encoding=contentCharset)
        while True:
            line = f.readline()
            if line=='':
                break
            if "<tbody>" in line:
                while "</tbody>" not in line:
                    line = f.readline()
                    if "<tr>" in line:
                        hanzi = None
                        pinyin = None
                        meaning = None

                        while "</tr>" not in line:
                            line = f.readline()

                            if "<span>" in line:
                                hanzi = line.split("<span>")[1].split("</span>")[0]
                                line = f.readline()
                                pinyin = line.replace(' ', '').replace('\n', '')
                                while "<td>" not in line:
                                    line = f.readline()
                                meaning = line.split("<td>")[1].split("</td>")[0]
                                if "CL" in meaning:
                                    meaning = meaning.split("CL")[0].strip()
                                    if meaning[-1] == ';':
                                        meaning = meaning[:-1]
                                meaning = meaning.split(";")
                        
                        nwords = nwords+1
                        print("HSK{}: {} words loaded...".format(level, nwords), end='\r')
                        currentLevelList.append(HanziWord(hanzi, pinyin, meaning))
        print()
        hanziDict['HSK{}'.format(level)] = currentLevelList
        
def exportAPKG():
    global hanziDict

    for levelList in hanziDict:# Filename of the Anki deck to generate
        deck_filename = "{}.apkg".format(levelList)

        # Title of the deck as shown in Anki
        anki_deck_title = levelList

        # Name of the card model
        anki_model_name = "HSK"
        # Create the deck model

        model_id = random.randrange(1 << 30, 1 << 31)

        style = """
        .card {
        font-family: arial;
        font-size: 24px;
        text-align: center;
        color: black;
        background-color: white;
        }
        .hanzi {
        font-size: 64px;
        }
        """

        anki_model = genanki.Model(
            model_id,
            anki_model_name,
            fields=[{"name": "hanzi"}, {"name": "pinyin"}, {"name": "meaning"}],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": '<p class="hanzi">{{hanzi}}</p>',
                    "afmt": '{{FrontSide}}<hr id="answer"><p class="pinyin">{{pinyin}}</p><p class="meaning">{{meaning}}</p>',
                },
                {
                    "name": "Card 2",
                    "qfmt": '<p class="meaning">{{meaning}}</p>',
                    "afmt": '{{FrontSide}}<hr id="answer"><p class="hanzi">{{hanzi}}</p><p class="pinyin">{{pinyin}}</p>',
                },
            ],
            css=style,
        )

        # The list of flashcards
        anki_notes = []

        for word in hanziDict[levelList]:
            anki_note = genanki.Note(
                model=anki_model,
                # simplified writing, pinyin, meaning
                fields=[word.hanzi, word.pinyin, ','.join(word.meaning)],
            )
            anki_notes.append(anki_note)
        
        # Shuffle flashcards
        random.shuffle(anki_notes)

        anki_deck = genanki.Deck(model_id, anki_deck_title)
        anki_package = genanki.Package(anki_deck)

        # Add flashcards to the deck
        for anki_note in anki_notes:
            anki_deck.add_note(anki_note)

        # Save the deck to a file
        anki_package.write_to_file(deck_filename)

        print("Created deck with {} flashcards".format(len(anki_deck.notes)))


contentLoader()
processContent()
exportAPKG()
