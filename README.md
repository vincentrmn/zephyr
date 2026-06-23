# Zéphyr

> Moteur de **pré-étude de faisabilité** pour l'intégration de la **VNC**
> (Ventilation Naturelle Contrôlée) dans les bâtiments.

À partir de plans (DXF) et du CPE, Zéphyr produit en quelques minutes : un
**score d'aptitude VNC** (déterministe, 4 critères pondérés) avec des
**recommandations** d'amélioration, et un **bilan financier** chiffré (VNC vs VMC
double-flux) avec fourchettes et sensibilité.

> **Décision produit** : la VNC est éligible sur ~95 % des bâtiments. On ne
> simule donc pas la thermique (ni 5R1C, ni EnergyPlus) — on **note l'aptitude**.
> Le seul terme thermique est le **surcoût de chauffage** VNC vs VMC, calculé en
> **degrés-jours** (déterministe). Full déterministe, pas de STD.

⚠️ Outil interne de **pré-qualification / aide à la décision**. Ce n'est **pas**
une étude opposable. Toute sortie expose ses hypothèses et son incertitude.

## 📖 Contexte de référence

- **[`docs/COMMENT_CA_MARCHE.md`](./docs/COMMENT_CA_MARCHE.md)** — explications
  **claires** (niveau ingénieur généraliste) : quel modèle, STD vs régression,
  fiabilité, paramètres, bureaux. À lire pour présenter/faire tester l'outil.
- **[`CLAUDE.md`](./CLAUDE.md)** — document maître : mission, décisions
  d'architecture (non négociables), glossaire, stack, spec ROI/thermique,
  roadmap, garde-fous.

## Architecture (pipeline déterministe)

`ingestion` (DXF) → `geometry` (topologie → `Building`) → `rules` (**score
d'aptitude**) & `thermal` (**pénalité chauffage degrés-jours**) → `roi`
(économie) → `web` / `report`. Le `llm` est un service transverse (narratif),
pas une étape du pipeline.

## État

| Module | État |
|---|---|
| `schemas` | ✅ contrat pydantic v2 (Building, VNCScore, HeatingPenalty, ROIResult…) |
| `rules` | ✅ **moteur de score** pondéré + recommandations (ventilation, vitrage, inertie, isolation) |
| `thermal` | ✅ **pénalité de chauffage en degrés-jours** (déterministe, sans STD) |
| `roi` | ✅ TCO/VAN paramétrique + pénalité branchée + tornado |
| `climate` | ✅ EPW réel (TMYx Findel) + degrés-jours/heures + solaire |
| `ingestion` / `geometry` | ✅ DXF → pièces (surfaces, labels, orientations, ouvrants) — validées humainement |
| `web` | ✅ plateforme FastAPI : landing → config → **validation géométrie** → résultats |
| `report` | ✅ rapport HTML (PDF optionnel WeasyPrint) |
| `study` | ✅ pipeline `compute_study` → `StudyResult` |
| `llm` | ✅ narratif Opus (optionnel) |

## Démarrage

```bash
# Cœur (schemas + roi + thermal), suffisant pour les tests :
uv sync
uv run pytest

# Runtime complet (CAO, climat, rapport, UI) :
uv sync --extra full
```

### 🚀 Lancer la plateforme web

```bash
./scripts/run_web.sh                 # → http://127.0.0.1:8000
# ou : uv run --extra full uvicorn app.web:app --reload
```

Ouvrez `http://127.0.0.1:8000`, cliquez **Lancer une étude**, et déposez le plan
d'exemple **[`examples/plan_exemple.dxf`](./examples/plan_exemple.dxf)** (6 pièces,
120 m²) — ou laissez vide pour une saisie paramétrique. Le DXF passe par l'étape
de **validation de la géométrie** avant le calcul.

```bash
# Régénérer le DXF d'exemple :
uv run --extra cao python scripts/make_sample_dxf.py
```

## Garde-fous (rappel — cf. CLAUDE.md §11)

- Le **code mesure**, le **LLM interprète**. Jamais de géométrie « lue » par vision.
- La **pénalité de chauffage VNC** est **calculée** par `thermal`, jamais postulée.
- Toujours afficher une **fourchette / sensibilité**, pas un point unique.
- **DXF vectoriel uniquement** (pas de DWG, pas de raster).
- Jamais de plans / CPE / exports STD clients committés.
