# Sram — Sorts élémentaires (Niveau 245)

Source : [Encyclopédie Wakfu](https://www.wakfu.com/fr/mmorpg/encyclopedie/classes/4-sram) (version post-rework 1.90)

> Le scaling est linéaire — les ratios entre sorts restent identiques quel que soit le niveau.

---

## Mécaniques clés

### Point Faible (PF)
Jauge 0-100 générée par la plupart des sorts (5 PF/PA en moyenne). Certains sorts consomment le PF pour des bonus de dégâts (+1% dégâts par niv. PF). La consommation du PF donne aussi des ressources :

| PF consommé | PA | PM | PW | Hémorragie appliquée |
|---|---|---|---|---|
| 100 | +4 | +4 | +1 | +40 (max) |
| 75-99 | +3 | +3 | — | ~30-39 |
| 50-74 | +2 | +2 | — | ~20 |
| 25-49 | +1 | — | — | ~10 |
| <25 | 0 | — | — | 0 |

### Hémorragie
Debuff empilable sur la cible. Pour chaque niveau d'Hémorragie, **chaque sort de dégât direct inflige une seconde ligne de dégâts finaux** égale à X% du dégât du sort (X = niv. Hémorragie). Ces dégâts finaux s'ajoutent après le calcul normal (mastery × DI × orientation × res).

Exemple : un sort tape 250 et la cible a 40 Hémorragie → +100 dégâts finaux (40% de 250).

### Sorts qui consomment PF
Mise à mort, Arnaque, Traumatisme — consomment tout le PF et gagnent +1% dégâts par niv. consommé.

### Sorts qui consomment Hémorragie
Ouvrir les veines — consomme l'Hémorragie, convertit 1:1 en Point Faible, et soigne (VdV 25/niv.).

---

## Feu (5 sorts)

### Premier Sang
| | Valeur |
|---|---|
| PA | 2 |
| Portée | 1-1 |
| Dmg Normal | Feu 60 |
| Dmg Crit | Feu 76 |
| Hémorragie | +10 Niv. si cible sans Hémo, +2 Niv. si cible a déjà Hémo |
| Point Faible | +10 Niv. |

### Ouvrir les veines
| | Valeur |
|---|---|
| PA | 2 |
| Portée | 1-1 |
| Dmg Normal | Feu 65 |
| Dmg Crit | Feu 82 |
| Soin (VdV) | 25 par niv. d'Hémorragie |
| Hémorragie | Consomme Hémorragie |
| Point Faible | +1 Niv. par niv. d'Hémorragie consommée (ex: 40 Hémo → +40 PF) |

### Châtiment
| | Valeur |
|---|---|
| PA | 4 |
| Portée | 1-1 |
| Dmg Normal | Feu 141 |
| Dmg Crit | Feu 176 |
| Si PF consommé ce tour | Feu 176 (N) / 220 (C) à la place |
| Point Faible | +20 Niv. |

### Saignée mortelle
| | Valeur |
|---|---|
| PA | 3 |
| Portée | 1-5 |
| Dmg Normal | Feu 91 |
| Dmg Crit | Feu 114 |
| Hémorragie | +6 Niv. |
| Soin | 100% des dégâts infligés par Hémorragie |
| Point Faible | +15 Niv. |
| Spécial | Saignée mortelle (Niv. 1) — relance auto au tour suivant |

### Mise à mort
| | Valeur |
|---|---|
| PA | 6 |
| Portée | 1-1 |
| Dmg Normal | Feu 211 |
| Dmg Crit | Feu 264 |
| Point Faible | +1% dégâts supplémentaires par PF, Consomme PF |

---

## Eau (5 sorts)

### Kleptosram
| | Valeur |
|---|---|
| PA | 2 |
| Portée | 1-2 |
| Dmg Normal | Eau 60 |
| Dmg Crit | Eau 76 |
| Point Faible | +10 Niv. (face) / +15 Niv. (dos) |

### Arnaque
| | Valeur |
|---|---|
| PA | 2 |
| Portée | 1-2 |
| Dmg Normal | Eau 60 |
| Dmg Crit | Eau 76 |
| Bonus | +1% dégâts supplémentaires par niv. PF consommé |
| Soin | 0.5% PV max par niv. PF |
| Point Faible | Consomme PF |

### Attaque létale
| | Valeur |
|---|---|
| PA | 4 |
| Portée | 1-2 |
| Dmg Normal | Eau 131 |
| Dmg Crit | Eau 164 |
| Si tue | Regagne 2 PA et 2 PM |
| Point Faible | +20 Niv. |

### Attaque perfide
| | Valeur |
|---|---|
| PA | 3 |
| Portée | 1-2 |
| Dmg Normal | Eau 121 (passe sous l'Armure) |
| Dmg Crit | Eau 152 (passe sous l'Armure) |
| Armure | 40% des dégâts infligés convertis en Armure sur la cible |
| Point Faible | +15 Niv. |

### Attaque mortelle
| | Valeur |
|---|---|
| PA | 5 |
| Portée | 1-2 |
| Dmg Normal | Eau 176 |
| Dmg Crit | Eau 220 |
| Si cible < 50% PV | Eau 247 (N) / 308 (C) à la place |
| Point Faible | +25 Niv. |

---

## Air (5 sorts)

### Coup pénétrant
| | Valeur |
|---|---|
| PA | 4 |
| Portée | 1-1, toujours mêlée |
| Dmg Normal | Air 131 |
| Dmg Crit | Air 164 |
| Si cible a Armure | +65 (N) / +82 (C) dégâts supplémentaires sur l'Armure |
| Point Faible | +20 Niv. |

### Effroi
| | Valeur |
|---|---|
| PA | 3 |
| Portée | 1-1 |
| Dmg Normal | Air 83 |
| Dmg Crit | Air 104 |
| Effet | Retourne la cible |
| Si PF consommé ce tour | Air 111 (N) / 139 (C) à la place |
| Point Faible | +15 Niv. |

### Fourberie
| | Valeur |
|---|---|
| PA | 3 |
| Portée | 1-4 |
| Dmg Normal | Air 98 |
| Dmg Crit | Air 123 |
| Effet | Téléporte derrière la cible |
| Point Faible | +15 Niv. |
| Condition | N'est pas porté |

### Coup Sournois
| | Valeur |
|---|---|
| PA | 3 |
| Portée | 1-1 |
| Dmg Normal | Air 98 |
| Dmg Crit | Air 123 |
| Effet | S'éloigne de 2 cases |
| Point Faible | +15 Niv. |

### Traumatisme
| | Valeur |
|---|---|
| PA | 4 |
| Portée | 1-4, toujours mêlée |
| Dmg Normal | Air 131 |
| Dmg Crit | Air 164 |
| Bonus | +1% dégâts supplémentaires par niv. PF |
| Point Faible | Consomme PF |

---

## Sorts généraux

### Invisibilité
| | Valeur |
|---|---|
| Coût | 2 PW |
| Portée | 1-4 |
| Effet | La cible devient invisible, +2 PM |
| Tour suivant | +100 dégâts infligés au prochain sort de dégât direct |

---

## Tableau récapitulatif — Ratio dégâts/PA (Niv. 245)

| Sort | Élément | PA | Dmg Normal | Dmg/PA | PF généré | Consomme PF/Hémo |
|---|---|---|---|---|---|---|
| Premier Sang | Feu | 2 | 60 | 30.0 | +10 | — |
| Ouvrir les veines | Feu | 2 | 65 | 32.5 | 1:1 Hémo→PF | Hémo |
| Châtiment | Feu | 4 | 141/176* | 35.3/44.0* | +20 | — |
| Saignée mortelle | Feu | 3 | 91 | 30.3 | +15 | — |
| Mise à mort | Feu | 6 | 211 (+1%/PF) | 35.2 (×2 à 100PF) | — | PF |
| Kleptosram | Eau | 2 | 60 | 30.0 | +10(+5 dos) | — |
| Arnaque | Eau | 2 | 60 | 30.0 | — | PF |
| Attaque létale | Eau | 4 | 131 | 32.8 | +20 | — |
| Attaque perfide | Eau | 3 | 121 | 40.3 | +15 | — |
| Attaque mortelle | Eau | 5 | 176/247* | 35.2/49.4* | +25 | — |
| Coup pénétrant | Air | 4 | 131 (+65 armure) | 32.8 | +20 | — |
| Effroi | Air | 3 | 83/111* | 27.7/37.0* | +15 | — |
| Fourberie | Air | 3 | 98 | 32.7 | +15 | — |
| Coup Sournois | Air | 3 | 98 | 32.7 | +15 | — |
| Traumatisme | Air | 4 | 131 (+1%/PF) | 32.8 | — | PF |

\* Valeur conditionnelle (cible <50% PV ou PF consommé ce tour)
