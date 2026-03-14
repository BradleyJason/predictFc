# Audit BDD — À faire

## Contexte
Les fusions d'équipes (session 14/03/2026) ont réassigné les matchs de TOUTE la base,
pas seulement les matchs futurs. Certaines fusions étaient incorrectes :
- Bayern Munich [626] → Bayer 04 Leverkusen [177] (FAUX — corrigé pour matchs futurs seulement)
- Bayer Leverkusen [643] → SV Werder Bremen [183] (FAUX — corrigé pour matchs futurs seulement)
- Celta Vigo [600] → CA Osasuna [117] (FAUX — corrigé pour matchs futurs seulement)
- Rennes [578] → Toulouse FC [1] (FAUX — corrigé pour matchs futurs seulement)
- West Brom [533] → Wolverhampton [66] (FAUX — corrigé pour matchs futurs seulement)

## Problème
Les matchs HISTORIQUES (FINISHED) affectés par ces mauvaises fusions n'ont pas été corrigés.

## Paires incorrectes à auditer (matchs historiques)
- [177] Bayer 04 Leverkusen — a reçu des matchs de Bayern Munich [626]
- [183] SV Werder Bremen — a reçu des matchs de Bayer Leverkusen [643]
- [117] CA Osasuna — a reçu des matchs de Celta Vigo [600]
- [1] Toulouse FC — a reçu des matchs de Rennes [578]
- [66] Wolverhampton — a reçu des matchs de West Brom [533]
