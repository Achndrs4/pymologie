from collections import namedtuple
from collections import Counter
import csv

Wortherkunft = namedtuple("Wortherkunft", ["Stamm","Sprache","Zeitraum"])

class pymologie:
    def __init__(self):
        self.cache()
        
    def cache(self):
        self.data = dict()
        with open('src/resources/etymologie.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if (term := row[0]) not in self.data:
                    self.data[term] = list()
                self.data[term].append(Wortherkunft(*row[1:]))

    def suchen(self, wort:str) -> str:
        try:
            herkünfte = self.data[wort]
            return_string = "\n"
            gesehene_sprachen = set()
            offset = 1
            for herkunft in herkünfte:
                if herkunft.Sprache in gesehene_sprachen:
                    offset = 1
                    return_string += "\n"
                    gesehene_sprachen.clear()
                gesehene_sprachen.add(herkunft.Sprache)
                return_string += (" " * offset) + "{stamm} {sprache}({zeitraum})".format(stamm = herkunft.Stamm , sprache = herkunft.Sprache , zeitraum = herkunft.Zeitraum) + "\n"
                offset += 1   
            return return_string
        except KeyError:
            return "nichts gefunden"

    def liste_suchen(self, wort:str) -> list:
        try:
            return[tuple(term) for term in self.data[wort]]
        except KeyError:
            return None
            
    def analysieren(self, wörter:str) -> Counter:
        sprache_anzahl = Counter()
        wort_anzahl = 0
        for wort in wörter:
            if wort in self.data:
                sprachen = [herkunft.Sprache for herkunft in self.data[wort]]
                sprache_anzahl.update(sprachen)
                wort_anzahl += 1
        return sprache_anzahl
    