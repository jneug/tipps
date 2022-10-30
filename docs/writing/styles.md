# Weitere Stile benutzen

Die Standardvorlagen für Tipps bauen auf dem CSS-Gerüst [Bulma](https://bulma.io) auf. Bulma bietet verschiedene Gestaltungselemente, die auch direkt auf Tipp-Seiten genutzt werden können.

Beispielsweise kann ein Absatz in eine [Box](https://bulma.io/documentation/elements/box/) gesetzt werden, wenn die Klasse `.box` benutzt wird. Dazu wird die Klasse eingeramt in `{:` und `}` in der Zeile direkt nach dem Absatz notiert: `{: .box }`.

``` title="Beispiel"
Weit hinten, hinter den Wortbergen, fern der Länder Vokalien und Konsonantien
leben die Blindtexte. Abgeschieden wohnen sie in Buchstabhausen an der Küste
des Semantik, eines großen Sprachozeans.
{: .box }
```

Weit hinten, hinter den Wortbergen, fern der Länder Vokalien und Konsonantien leben die Blindtexte. Abgeschieden wohnen sie in Buchstabhausen an der Küste des Semantik, eines großen Sprachozeans.
{: .box .tipps }

Interessant sind zum Beispiel die Stile in der Kategorie "Helpers", wie die [Typografischen anpassungen](https://bulma.io/documentation/helpers/typography-helpers/) oder die [Farben](https://bulma.io/documentation/helpers/color-helpers/). 

Komplexere Elemente, deren Code direkt mit HTML-Tags übernommen werden muss, sind die [Progress Bars](https://bulma.io/documentation/elements/progress/) oder [Nachrichten-Elemente](https://bulma.io/documentation/components/message/).

``` title="Beispiel"
<div class="message is-primary">
	<span class="message-header">Hello World</span>

	<p class="message-body">
	Weit hinten, hinter den Wortbergen, fern der Länder Vokalien und 
	Konsonantien leben die Blindtexte. Abgeschieden wohnen sie in 
	Buchstabhausen an der Küste des Semantik, eines großen Sprachozeans.
	</p>
</div>
```
Mit etwas HTML-Kenntnissen lassen sich so ganze neue Einsatzzwecke für **Tipps** finden. Zum Beispiel könnten mehrere Tipps zu einer Art Lernpfad zusammengesetzt werden, indem eine Navigation eingefügt wird:

```html title="Beispiel"
<progress class="progress is-primary" value="3" max="10">Schritt 3 von 10</progress>
<nav class="pagination is-center" role="navigation" aria-label="pagination">
  <a class="pagination-previous">Letzter Schritt</a>
  <a class="pagination-next">Nächster Schritt</a>
</nav>
```
