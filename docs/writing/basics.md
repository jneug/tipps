# Tipps verfassen

Tipps werden ald Text im [Markdown](https://de.wikipedia.org/wiki/Markdown) Format verfasst. 

!!! note
	
	Markdown ist eine vereinfachte Auszeichnungssprache, die von John Gruber und Aaron Swartz entworfen und im Dezember 2004 mit Version 1.0.1 spezifiziert wurde. Ein Ziel von Markdown ist eine leicht lesbare Ausgangsform bereits vor der Konvertierung. Da es sich bei Markdown-Dokumenten um reine Textdateien handelt, können sie mit einem einfachen Texteditor bearbeitet werden.

Markdown bietet Auszeichnungen für Überschriften, Fett- oder Kursivdruck, Links und vieles mehr. Darüber hinaus wurde die Sprache im Laufe der Zeit um weitere Elemente, wie Tabellen, erweitert. Markdown in **Tipps** wurde um eine Vielzahl von Funktionen angereichert, mit denen sich unter anderem mathematisch Formeln oder Diagramme erstellen lassen.

## Die wichtigsten Elemente

### Überschriften

Überschriften verschiedener Ebenen werden mit `#` eingeleitet:

```
# H1
## H2
### H3
```

### Textformatierungen

`**fetter Text**` wird zu **fetter Text**.

`_kursiver Text_` wird zu _kursiver Text_. (Alternativ `*kursiver Text*`.)

### Zitate

Zeilen, die mit `>` starten, werden als Zitate interpretiert.

```
> Zitate können auf
>> Merheren Ebenen dargestellt
```

### Listen

Nummerierte Listen:
```
1. Erstes Element
2. Zweites Element
3. Drittes Element
```

Aufzählungen:
```
- A
- B
- C
```

Die Listen können auch verschachtelt werden:

- A
    - A.1
    - A.2
- B
    1. B.1
    2. B.2
        - B.2.1
- C

### Quelltexte

Codewörter im Text werden mit "Backticks" umrahmt: `code`

Größere Quelltexte werden mit drei "Backticks" umrahmt. Nach den ersten drei kann optional eine Programmiersprache für die Hervorhebung angegeben werden:

```java
public class Word {

    private String english;
    private String german;

    public Word( String pEnglish, String pGerman ) {
        english = pEnglish;
        german = pGerman;
    }

    public String getGerman() {
        return german;
    }

    public String getEnglish() {
        return english;
    }

}
```

### Horizontale Trennlinie

```
---
```
----

### Links

```
[Helmholtz Git](https://git.ngb.schule)
[Wiki](https://informatik-box.de)
```
[Helmholtz Git](https://git.ngb.schule)
[Wiki](https://informatik-box.de)

### Bilder

Bilder können mit einer URL direkt aus dem Internet eingebunden werden, oder aus dem Unterordner `./medien`:

```
![Bild über Informatik](./medien/computer-science.jpg)
```

![Bild über Informatik](./medien/computer-science.jpg)


### Tabellen

Die Syntax für Tabellen ist etwas umständlich. Daher ist es leichter diese mit einem Tool wie dem [Markdown Table Editor and Generator](https://tableconvert.com/markdown-generator) zu erstellen und den Code in die Dateien einzufügen.

```markdown
| Eins | Links | Mittig | Rechts |
|------|:------|:------:|-------:|
| 0    | 1     | 2      | 3      |
```

| Eins | Links | Mittig | Rechts |
|------|:------|:------:|-------:|
| 0    | 1     | 2      | 3      |



## Weiterführende Links

Neben der grundlegenden Syntax gibt es noch eine Reihe erweiterter Auszeichnungselemente, die aber je nach verwendetem Standard unterschiedlich unterstützt werden. Darunter sind auch [Tabellen](https://www.markdownguide.org/extended-syntax/#tables) und [Fußnoten](https://www.markdownguide.org/extended-syntax/#footnotes).

- [Markdown Übersicht](./medien/Markdown-CheatSheet-Deutsch.pdf) (PDF)
- [The Markdown Guide](https://www.markdownguide.org) (Englisch)
- [Zettlr Dokumentation](https://docs.zettlr.com/de/) (Hilfen zum Markdown Editor)
- [Markdown Tabellen Editor](https://www.tablesgenerator.com/markdown_tables)
