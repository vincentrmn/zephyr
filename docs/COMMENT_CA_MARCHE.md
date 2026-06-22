# Zéphyr — comment ça marche (explications claires)

> Document d'explication **non technique-spécialiste**. Niveau ingénieur
> généraliste, pas ingénieur énergéticien. Sert de base pour présenter l'outil
> (mail aux associés, démo, onboarding testeurs).
>
> Rappel cadre : Zéphyr est un outil de **pré-étude / aide à la décision
> interne**. **Ce n'est pas une étude thermique opposable.** Il dit *vite* si la
> VNC vaut le coup sur un bâtiment, avec un ROI en ordre de grandeur — pas un
> chiffre de bureau d'études.

---

## En une phrase

Zéphyr **simule** le comportement thermique d'un bâtiment heure par heure sur une
année (avec la vraie météo) à l'aide d'un **modèle physique simplifié**, puis en
tire un **verdict de faisabilité VNC** et un **ROI chiffré** (VNC vs VMC
double-flux), le tout avec des **fourchettes** et des hypothèses explicites.

---

## 1. Est-ce une STD ? Une régression ? Quel modèle ?

**C'est une "STD allégée" : un modèle physique réduit. Ce n'est ni une vraie STD,
ni une régression statistique / IA.**

| | Vraie STD (IDA ICE) | **Zéphyr (5R1C)** | Régression / IA |
|---|---|---|---|
| Nature | Simulation physique détaillée | Simulation physique **simplifiée** | Modèle ajusté sur des exemples |
| Temps de calcul | Heures | **Secondes** | Instantané |
| Données nécessaires | Beaucoup, expert | Quelques paramètres | Un gros jeu d'entraînement |
| Généralise ? | Oui (physique) | **Oui (physique)** | Seulement près des exemples vus |
| Rôle ici | **Référence de validation** | **Le moteur** | Écarté (Phase ultérieure) |

**Le modèle, par analogie électrique (que tout ingénieur connaît) :** on
représente chaque pièce par un petit **circuit RC** —
- des **résistances** = les déperditions (murs, fenêtres, ventilation) ;
- une **capacité** = l'**inertie thermique** (la masse béton qui stocke et
  déphase la chaleur).

On "branche" la météo réelle dessus et on calcule la température heure par heure.
Son petit nom normalisé : **5R1C** (5 résistances, 1 capacité — ISO 13790/52016).
On y ajoute :
- un **nœud de sol** : le plancher bas voit la terre (~stable, ~10 °C), pas l'air
  extérieur — sinon le bâtiment "gèle" à tort en hiver dans le calcul ;
- un **nœud de masse structurelle partagé** : un gros "**volant d'inertie**"
  (dalles/cloisons béton) qui relie les pièces, lisse les variations et
  **redistribue** la chaleur (une pièce ensoleillée réchauffe une pièce aveugle).

**Pourquoi pas de l'IA / régression ?** Parce qu'on n'a **pas assez** de STD pour
entraîner un modèle qui généralise honnêtement. Et un modèle physique a un énorme
avantage : il **obéit aux mêmes lois partout**, donc il s'applique à un bâtiment
qu'il n'a "jamais vu". L'IA est repoussée à plus tard, *si* un jour on a un produit
déterministe qui marche **et** un gros jeu de données.

---

## 2. Comment être sûr des résultats là où on n'aura PAS de STD ?

C'est la question centrale. Quatre garde-fous :

1. **Le modèle est physique, pas "ajusté au cas".** Ses entrées sont des
   grandeurs **réelles du bâtiment** (surfaces, isolation U des parois, vitrages,
   volume, inertie) tirées du CPE et des plans. Il **extrapole par la physique**.

2. **Les STD sont un banc d'essai, pas un entraînement.** Sur les bâtiments où on
   a une STD, on **vérifie** que Zéphyr la reproduit dans une **tolérance
   définie**. Si ça colle sur plusieurs cas variés, on est fondé à lui faire
   confiance ailleurs — *dans les mêmes ordres de grandeur*.

   > *État actuel :* validé sur **1 maison** (bois/CLT, LU) pour le comportement
   > "bâtiment à vide" → **8 pièces sur 8 à ±2,5 °C** de la STD. À étendre
   > (pénalité de chauffage, bâtiment béton lourd, bureaux).

3. **On reste honnête sur l'incertitude.** Zéphyr affiche des **fourchettes**,
   jamais un point unique, et **expose ses hypothèses**. C'est une pré-étude :
   pour une décision finale, une vraie STD reste nécessaire. Zéphyr dit *vite* si
   ça vaut le coup d'y aller.

4. **Le chiffre du ROI est robuste par construction.** La "pénalité de chauffage"
   (le surcoût de chauffe de la VNC, qui n'a pas de récupérateur, vs la VMC qui en
   a un) est calculée comme la **différence de deux simulations identiques sauf la
   récupération**. Les approximations se **compensent** dans la soustraction → le
   chiffre est fiable *directionnellement*, même si la valeur absolue de chauffage
   est plus incertaine.

**En clair :** Zéphyr est **directionnellement fiable** (le sens et l'ordre de
grandeur sont bons), pas précis au kWh près. C'est exactement ce qu'il faut pour
**pré-qualifier** un bâtiment.

---

## 3. Peut-on changer les paramètres ?

**Oui — tout est exposé et modifiable.** Aucune valeur n'est "en dur" dans le
moteur. Quatre niveaux :

- **Géométrie** : pièces, surfaces, hauteurs, vitrages, orientations, niveau,
  classe d'inertie. → avec une étape de **validation humaine** : l'ingénieur
  corrige ce qui a été extrait des plans **avant** le calcul.
- **Enveloppe** : U murs / toiture / plancher / vitrage, facteur solaire,
  étanchéité à l'air.
- **Thermique / exploitation** : consignes de chauffage, débits de ventilation,
  rendement de l'échangeur VMC, apports internes, stratégie de free-cooling
  nocturne…
- **Économique (ROI)** : tous les coûts, ratios €/m², prix de l'énergie, WACC,
  abonnement plateforme, horizon… (avec des **presets régionaux**).

Et l'outil fournit une **analyse de sensibilité (tornado)** : on voit
immédiatement **quels paramètres font bouger le résultat** (typiquement : prix de
l'élec, nombre d'ouvrants, abonnement, pénalité de chauffage). Donc un testeur
peut "jouer" avec les hypothèses et voir l'impact.

---

## 4. Et les bâtiments de bureaux ?

**Même moteur physique** — un bureau, ça reste des déperditions + de l'inertie.
Ce qui change, ce sont les **profils** (des presets différents) :

- **Occupation & apports internes** : un bureau est plein le **jour** (gens,
  ordinateurs, éclairage), vide la **nuit** et le week-end — l'inverse d'un
  logement.
- **Ventilation** : besoin d'air plus élevé par m² quand c'est occupé.
- **Confort** : ~8 h ouvrées.

**Point important pour le business :** c'est **en bureaux que la VNC est la plus
intéressante** — gros apports internes le jour + occupation diurne + fort
**rafraîchissement passif nocturne** (free-cooling) grâce à l'inertie. Le cas ROI
de référence (Pommerloch) est d'ailleurs **mixte logements + bureaux**.

> *À faire :* un **preset bureaux** (occupation/apports/ventilation) et,
> idéalement, **une STD de bureaux** pour valider (on a la résidentielle).

---

## 5. Le pipeline complet (vue d'ensemble)

```
Plans (DXF) ─▶ Géométrie ─▶ ┌─ Thermique (5R1C) : surchauffe + pénalité chauffage
 + paramètres   (pièces,     │
                murs,        ├─ Ventilation : débits naturels (tirage + vent)
                ouvrants)    │
                             ├─ Règles : verdict go / no-go / conditionnel
                             │
                             └─ ROI : VNC vs VMC, VAN, break-even, fourchettes
                                          │
                                          ▼
                                  Rapport (verdict + ROI + explications)
```

- Le **code mesure et calcule** (géométrie, physique, économie).
- Une **IA n'intervient que pour deux choses** : étiqueter les pièces à
  l'extraction des plans ("ceci est un séjour / une SDB") et **rédiger** les
  explications du rapport. **Jamais** pour calculer ou inventer un chiffre.

---

## 6. Ce qu'on peut dire aux testeurs (et ce qu'on ne doit pas)

**On peut dire :**
- "Donne-nous un bâtiment, on te dit en quelques minutes si la VNC est pertinente
  et l'ordre de grandeur du ROI."
- "Les hypothèses sont visibles et modifiables ; on montre une fourchette et ce
  qui fait bouger le résultat."
- "Le moteur thermique est validé contre nos STD IDA ICE dans une tolérance
  définie (en cours d'extension)."

**On ne doit pas dire :**
- ❌ "C'est une étude thermique." (Non — c'est une pré-étude.)
- ❌ "Le ROI est garanti / précis." (Non — fourchette, ordres de grandeur.)
- ❌ "C'est conforme / opposable." (Non.)

---

## 7. État de validation (au moment d'écrire)

| Brique | État |
|---|---|
| Moteur ROI (VNC vs VMC, VAN, tornado) | ✅ opérationnel, paramétré |
| Thermique 5R1C multi-zone — **free-float** | ✅ validé sur 1 cas réel (±2,5 °C) |
| Thermique — **pénalité de chauffage** | 🚧 à valider sur cas régulés |
| Profils d'occupation (logement/bureaux) | 🚧 à intégrer |
| Cas béton lourd / bureaux | 🚧 à valider |
| Extraction des plans (DXF) + UI | 🚧 à venir |

> Cette section est volontairement honnête : c'est un produit en construction. La
> bonne nouvelle, c'est que **l'approche est dé-risquée** — le moteur reproduit
> déjà une STD réelle là où on l'a testé.
