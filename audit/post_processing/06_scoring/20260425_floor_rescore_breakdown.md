# Safety-floor rescore breakdown

- run_id: `20260425T073743_20d0478d`
- pairs in `composite_rankings`: 2904
- pairs failed exclusionary (any reason): 2696
- pairs failed by **floor only** (no hard E-code): 1288
- pairs failed by **hard E-code only** (no floor): 232
- survivors: 208

## Per-criterion verdict counts

| criterion | prompt_key | kind | n_verdicts | n_pairs |
| --- | --- | --- | ---: | ---: |
| EP-01 | `E8` | hard | 456 | 456 |
| EP-01 | `E8:floor` | floor | 1680 | 1680 |
| NH-02 | `E1` | hard | 400 | 400 |
| NH-02 | `E1:floor` | floor | 304 | 304 |
| NH-03 | `E2:floor` | floor | 8 | 8 |
| NH-04 | `E3` | hard | 24 | 24 |
| NH-04 | `E3:floor` | floor | 1288 | 1288 |
| NH-05 | `E5` | hard | 8 | 8 |
| NH-05 | `E5:floor` | floor | 824 | 824 |
| NH-05 | `E6` | hard | 800 | 800 |
| NH-05 | `E6:floor` | floor | 32 | 32 |
| NS-08 | `E7:floor` | floor | 32 | 32 |

Floor verdicts (`<E>:floor`) are emitted by
`atoms_vs_ashes.scoring._safety_floor` whenever the criterion's
0-10 ranking score is strictly below the declared `pass_mark` AND
the corresponding hard E-code expression did not already trigger.
See `report/methodology/exclusionary_floors.md` for the full rule
table.
