<!-- man_hours: 0.3 -->
# FIX-04 OSM avoidance — preview report (no DB writes)

- Run ID: `hi06-fix04-preview-20260510-065226`
- Generated: 2026-05-11T15:48:50.114916+00:00
- Total sites considered: **361**
- Sites with at least one proposed change (any domain): **355**
- Sites already in sync: **6**
- Fetch errors (military / HI-06): **0**
- Fetch errors (transmitter / HI-07): **0**
- Fetch errors (power / NS-02): **0**

## HI-06 (military) — proposed changes per column

| Column | Sites that would change |
|--------|------------------------:|
| `nearest_military_km` | 3 |
| `nearest_military_name` | 9 |
| `military_count` | 119 |
| `hi06_quality` | 99 |

## HI-07 (transmitter) — proposed changes per column

| Column | Sites that would change |
|--------|------------------------:|
| `nearest_transmitter_km` | 5 |
| `transmitter_type` | 4 |
| `transmitter_count` | 156 |
| `hi07_quality` | 94 |

## NS-02 (power) — proposed changes per column

| Column | Sites that would change |
|--------|------------------------:|
| `nearest_hv_line_km` | 1 |
| `nearest_substation_km` | 1 |
| `hv_line_count` | 114 |
| `substation_count` | 181 |
| `hv_line_voltage_kv` | 0 |
| `ns02_quality` | 335 |

## Sites with proposed changes (showing first 50)

### AL — Porto Romano Power Station  (`e6ecead0-54d1-41fe-8268-1253d0d7ef3e`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| power | `ns02_quality` | `medium` | `high` |

### AT — Duernrohr power station  (`6e7fc4d8-636d-411a-baef-e138a5a07acc`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| power | `hv_line_count` | `884` | `896` |
| power | `substation_count` | `2909` | `2936` |
| power | `ns02_quality` | `medium` | `high` |

### AT — Enns Power Station  (`532bfb42-0d4c-42cf-a81a-287f2b3a75bf`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| power | `substation_count` | `2089` | `2090` |
| power | `ns02_quality` | `medium` | `high` |

### AT — Mellach power station  (`90820fe3-9889-4faf-9906-7c528f8d7bc5`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| power | `substation_count` | `1658` | `1660` |
| power | `ns02_quality` | `medium` | `high` |

### AT — Riedersbach power station  (`660d9d71-6733-4294-951b-1c58614d58cf`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| transmitter | `transmitter_count` | `159` | `166` |
| power | `substation_count` | `2645` | `2656` |
| power | `ns02_quality` | `medium` | `high` |

### AT — St Andrae power station  (`021c723b-98af-4b72-8f6c-ade538885f10`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| military | `military_count` | `0` | `4` |
| military | `hi06_quality` | `not_found` | `medium` |
| power | `hv_line_count` | `0` | `490` |
| power | `substation_count` | `0` | `1479` |
| power | `ns02_quality` | `medium` | `high` |

### AT — Timelkam power station  (`2dcd2c6d-f375-4408-9492-7910662fac03`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| military | `military_count` | `0` | `71` |
| military | `hi06_quality` | `not_found` | `medium` |
| transmitter | `transmitter_count` | `0` | `225` |
| transmitter | `hi07_quality` | `not_found` | `medium` |
| power | `substation_count` | `2977` | `2987` |
| power | `ns02_quality` | `medium` | `high` |

### AT — Voitsberg power station  (`99d712ac-7993-4186-8a0e-2e88bae7e90f`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| military | `military_count` | `0` | `49` |
| military | `hi06_quality` | `not_found` | `medium` |
| transmitter | `transmitter_count` | `0` | `360` |
| transmitter | `hi07_quality` | `not_found` | `medium` |
| power | `substation_count` | `1416` | `1418` |
| power | `ns02_quality` | `medium` | `high` |

### AT — Zeltweg power station  (`33d83e11-cfcd-47cb-be5e-82ca0fc352cc`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| power | `substation_count` | `1033` | `1036` |
| power | `ns02_quality` | `medium` | `high` |

### BA — Bugojno Thermal Power Project  (`67e5a20f-e3ab-4c18-9864-cf4591d6e15f`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| military | `military_count` | `0` | `2` |
| military | `hi06_quality` | `not_found` | `high` |
| transmitter | `transmitter_count` | `0` | `25` |
| transmitter | `hi07_quality` | `not_found` | `medium` |
| power | `hv_line_count` | `0` | `47` |
| power | `substation_count` | `0` | `31` |
| power | `ns02_quality` | `medium` | `high` |

### BA — Gacko Thermal Power Plant  (`85257083-08d1-4560-b198-a9df414da4a9`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| transmitter | `transmitter_count` | `0` | `3` |
| transmitter | `hi07_quality` | `not_found` | `medium` |
| power | `hv_line_count` | `0` | `31` |
| power | `substation_count` | `0` | `10` |

### BA — Glinica power station  (`e2d645e3-c829-4aac-8f6f-d6a5507fd5fa`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| military | `military_count` | `0` | `7` |
| military | `hi06_quality` | `not_found` | `high` |
| transmitter | `transmitter_count` | `0` | `60` |
| transmitter | `hi07_quality` | `not_found` | `medium` |
| power | `hv_line_count` | `0` | `64` |
| power | `substation_count` | `0` | `45` |
| power | `ns02_quality` | `medium` | `high` |

### BA — Kakanj Thermal Power Plant  (`e671be33-8b91-40bd-b563-b833293654aa`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| power | `ns02_quality` | `medium` | `high` |

### BA — Kamengrad Thermal Power Plant  (`344e0e9a-558e-4749-bb66-cd746be50cbd`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| military | `military_count` | `0` | `1` |
| military | `hi06_quality` | `not_found` | `medium` |
| transmitter | `transmitter_count` | `0` | `13` |
| transmitter | `hi07_quality` | `not_found` | `medium` |
| power | `hv_line_count` | `0` | `50` |
| power | `substation_count` | `0` | `31` |
| power | `ns02_quality` | `medium` | `high` |

### BA — Kongora Thermal Power Plant  (`0155b913-765f-4d44-89f5-c176b6867cef`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| military | `military_count` | `0` | `2` |
| military | `hi06_quality` | `not_found` | `medium` |
| transmitter | `transmitter_count` | `0` | `32` |
| transmitter | `hi07_quality` | `not_found` | `medium` |
| power | `hv_line_count` | `0` | `77` |
| power | `substation_count` | `0` | `59` |
| power | `ns02_quality` | `medium` | `high` |

### BA — Miljevina power station  (`aa0bdb5e-45aa-4d15-8aee-cb5b0e14f5d9`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| power | `ns02_quality` | `medium` | `high` |

### BA — Tuzla Thermal Power Plant  (`0fb50bcc-5616-40d8-9109-8136a958f18d`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| power | `ns02_quality` | `medium` | `high` |

### BA — Ugljevik power station  (`a23d073a-cbbd-469a-b134-380945fd3f4c`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| power | `ns02_quality` | `medium` | `high` |

### BG — Bobov Dol power station  (`b01fe781-dbc7-40f8-a544-946288020042`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| transmitter | `transmitter_count` | `0` | `11` |
| transmitter | `hi07_quality` | `not_found` | `medium` |
| power | `substation_count` | `376` | `381` |
| power | `ns02_quality` | `medium` | `high` |

### BG — Brikel power station  (`fee1d5b3-827f-4172-8492-a3e114a3c39e`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| transmitter | `transmitter_count` | `19` | `29` |
| power | `hv_line_count` | `0` | `240` |
| power | `substation_count` | `0` | `352` |
| power | `ns02_quality` | `medium` | `high` |

### BG — Deven power station  (`398cc0f2-25d5-428a-93c9-5e4859680e86`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| military | `military_count` | `0` | `27` |
| military | `hi06_quality` | `not_found` | `medium` |
| transmitter | `nearest_transmitter_km` | `5.39` | `3.86` |
| transmitter | `transmitter_type` | `mast` | `lighting` |
| transmitter | `transmitter_count` | `55` | `65` |
| power | `hv_line_count` | `0` | `219` |
| power | `substation_count` | `0` | `321` |
| power | `ns02_quality` | `medium` | `high` |

### BG — Lom Power Station  (`30c9e377-b575-46fa-880f-922c46e6500a`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| power | `ns02_quality` | `medium` | `high` |

### BG — Maritsa 3 power station  (`3bb6666f-de2f-4c6f-a28e-c3bddb71b54a`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| transmitter | `transmitter_count` | `31` | `34` |
| power | `substation_count` | `337` | `339` |
| power | `ns02_quality` | `medium` | `high` |

### BG — Maritsa Iztok-1 power station  (`d12d7173-8595-4b53-92af-75b44b5a2fb7`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| transmitter | `transmitter_count` | `0` | `29` |
| transmitter | `hi07_quality` | `not_found` | `medium` |
| power | `hv_line_count` | `0` | `240` |
| power | `substation_count` | `0` | `352` |
| power | `ns02_quality` | `medium` | `high` |

### BG — Maritsa Iztok-2 power station  (`ec5f337a-ca52-4b86-a0f4-4933eac349e3`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| transmitter | `transmitter_count` | `0` | `27` |
| transmitter | `hi07_quality` | `not_found` | `medium` |
| power | `substation_count` | `251` | `253` |
| power | `ns02_quality` | `medium` | `high` |

### BG — Maritsa Iztok-3 power station  (`0e860f58-416b-4116-836d-04edf8ded225`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| transmitter | `transmitter_count` | `0` | `28` |
| transmitter | `hi07_quality` | `not_found` | `medium` |
| power | `hv_line_count` | `0` | `242` |
| power | `substation_count` | `0` | `354` |
| power | `ns02_quality` | `medium` | `high` |

### BG — Maritsa Iztok-4 power station  (`b1bcb7d3-cd40-40c9-9c59-a01fa71053b3`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| transmitter | `transmitter_count` | `18` | `28` |
| power | `hv_line_count` | `0` | `242` |
| power | `substation_count` | `0` | `354` |
| power | `ns02_quality` | `medium` | `high` |

### BG — Republika power station  (`33a015dd-51e0-497e-b0d3-4b1b3f070438`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| military | `military_count` | `0` | `31` |
| military | `hi06_quality` | `not_found` | `high` |
| power | `substation_count` | `806` | `809` |
| power | `ns02_quality` | `medium` | `high` |

### BG — Ruse Iztok power station  (`704ef487-f600-4f23-b06e-a0f81b627597`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| power | `ns02_quality` | `medium` | `high` |

### BG — Sliven power station  (`93685558-3355-4da2-9a4a-4cccd89f9269`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| power | `ns02_quality` | `medium` | `high` |

### BG — Svilosa power station  (`2fb27566-cc7b-4530-8ff9-e55e3a1985bd`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| power | `ns02_quality` | `medium` | `high` |

### BG — Varna power station  (`85c56b15-450b-4bb1-b75e-5ea00ee51cb2`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| military | `military_count` | `0` | `38` |
| military | `hi06_quality` | `not_found` | `high` |
| transmitter | `nearest_transmitter_km` | `5.6` | `5.37` |
| transmitter | `transmitter_type` | `mast` | `lighting` |
| transmitter | `transmitter_count` | `64` | `74` |
| power | `hv_line_count` | `0` | `212` |
| power | `substation_count` | `0` | `319` |
| power | `ns02_quality` | `medium` | `high` |

### BG — Vidin Works power station  (`a064c7ae-e699-4a94-a18c-79bdfe42bce3`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| transmitter | `transmitter_count` | `0` | `51` |
| transmitter | `hi07_quality` | `not_found` | `medium` |
| power | `hv_line_count` | `0` | `94` |
| power | `substation_count` | `0` | `41` |
| power | `ns02_quality` | `medium` | `high` |

### BY — Lelchitsy power station  (`68aabff9-e662-4b9f-b37d-4c2ebc5f7539`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| power | `ns02_quality` | `insufficient` | `high` |

### BY — Zelwa power station  (`fac3d0b5-36a5-48ae-8494-f2f08e4342f4`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| power | `ns02_quality` | `insufficient` | `high` |

### CZ — Chvaletice power station  (`d762ceeb-514f-43a6-9f91-a2d422ed6c60`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| military | `military_count` | `0` | `113` |
| military | `hi06_quality` | `not_found` | `medium` |
| transmitter | `transmitter_count` | `0` | `384` |
| transmitter | `hi07_quality` | `not_found` | `medium` |
| power | `substation_count` | `1034` | `1039` |
| power | `ns02_quality` | `medium` | `high` |

### CZ — Detmarovice power station  (`a733fc13-11a4-4722-b62d-85c85a4f8ef3`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| power | `hv_line_count` | `0` | `1172` |
| power | `substation_count` | `0` | `1771` |
| power | `ns02_quality` | `medium` | `high` |

### CZ — Hodonin power station  (`180880c2-7284-4723-b02a-a62348b9b40b`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| transmitter | `transmitter_count` | `126` | `127` |
| power | `substation_count` | `324` | `325` |
| power | `ns02_quality` | `medium` | `high` |

### CZ — Karvina power station  (`43e5b2b4-2ccf-46ab-b01e-e3d480146455`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| power | `substation_count` | `1433` | `1444` |
| power | `ns02_quality` | `medium` | `high` |

### CZ — Kladno power station  (`f1d2bca1-a7a9-4404-84c1-34fc8a59dab7`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| transmitter | `transmitter_count` | `334` | `335` |
| power | `hv_line_count` | `1702` | `1698` |
| power | `ns02_quality` | `medium` | `high` |

### CZ — Komorany power station  (`274ec928-e527-44cf-86c5-b6eddc09d0f7`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| military | `military_count` | `0` | `46` |
| military | `hi06_quality` | `not_found` | `high` |
| transmitter | `transmitter_count` | `0` | `145` |
| transmitter | `hi07_quality` | `not_found` | `medium` |
| power | `hv_line_count` | `0` | `1238` |
| power | `substation_count` | `0` | `1322` |
| power | `ns02_quality` | `medium` | `high` |

### CZ — Ledvice power station  (`2fe0a0b3-4108-427e-8e54-f77e1ea7227c`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| transmitter | `transmitter_count` | `211` | `210` |
| power | `hv_line_count` | `0` | `1476` |
| power | `substation_count` | `0` | `1538` |
| power | `ns02_quality` | `medium` | `high` |

### CZ — Malesice power station  (`1c059a42-608c-4753-8fcf-ba797d94f900`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| transmitter | `transmitter_count` | `630` | `631` |
| power | `hv_line_count` | `0` | `1789` |
| power | `substation_count` | `0` | `4647` |
| power | `ns02_quality` | `medium` | `high` |

### CZ — Marianske Hory power station  (`cbd67443-4a4e-44fd-a9ed-20ba9574c99e`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| military | `military_count` | `0` | `98` |
| military | `hi06_quality` | `not_found` | `high` |
| power | `hv_line_count` | `0` | `746` |
| power | `substation_count` | `0` | `1007` |
| power | `ns02_quality` | `medium` | `high` |

### CZ — Melnik power station  (`f3523341-daaa-4573-a856-becb2e1bb9e3`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| transmitter | `transmitter_count` | `154` | `155` |
| power | `hv_line_count` | `1946` | `1942` |
| power | `ns02_quality` | `medium` | `high` |

### CZ — Mondi Steti power station  (`e299922a-1670-4aff-acda-fd80600af9af`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| military | `military_count` | `0` | `98` |
| military | `hi06_quality` | `not_found` | `high` |
| transmitter | `transmitter_count` | `0` | `148` |
| transmitter | `hi07_quality` | `not_found` | `medium` |
| power | `nearest_hv_line_km` | `0.39` | `0.65` |
| power | `hv_line_count` | `0` | `1889` |
| power | `substation_count` | `0` | `4292` |
| power | `ns02_quality` | `medium` | `high` |

### CZ — Mostecka Power Station  (`4eb7914c-e000-403c-b5a5-c350de67bb83`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| transmitter | `transmitter_count` | `157` | `156` |
| power | `hv_line_count` | `0` | `1272` |
| power | `substation_count` | `0` | `1300` |
| power | `ns02_quality` | `medium` | `high` |

### CZ — Olomouc power station  (`44d40276-5847-41d1-ab9b-887bbdc1bcfe`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| military | `military_count` | `0` | `29` |
| military | `hi06_quality` | `not_found` | `high` |
| transmitter | `transmitter_count` | `0` | `235` |
| transmitter | `hi07_quality` | `not_found` | `medium` |
| power | `hv_line_count` | `0` | `332` |
| power | `substation_count` | `0` | `249` |
| power | `ns02_quality` | `medium` | `high` |

### CZ — Opatovice power station  (`05daa6b2-bb29-4c26-a459-855626673955`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| transmitter | `transmitter_count` | `465` | `466` |
| power | `hv_line_count` | `0` | `475` |
| power | `substation_count` | `0` | `1208` |
| power | `ns02_quality` | `medium` | `high` |

### CZ — Plana Nad Luznici power station  (`9c4291f1-173b-467e-ae26-8cb01312c605`)

| domain | column | current_db | proposed |
|--------|--------|------------|----------|
| military | `military_count` | `0` | `8` |
| military | `hi06_quality` | `not_found` | `medium` |
| transmitter | `transmitter_count` | `0` | `196` |
| transmitter | `hi07_quality` | `not_found` | `medium` |
| power | `ns02_quality` | `medium` | `high` |

_+ 305 more sites; see JSONL for the full list._

